#!/usr/bin/env python3
"""
tests/benchmark_runner.py

Universal benchmark runner for SAS.

Goals:
- Let the user choose which benchmark suite to run.
- Avoid accidentally scanning huge corpora such as Halogen unless explicitly requested.
- Support local regression cases with no corpus required.
- Support hosted API or local API.
- Produce a complete JSON report with metadata, summary, confusion matrix and per-case outputs.

Examples:

    # Fast local regression suite against hosted API
    python tests/benchmark_runner.py --suite regression --api-url https://sas-api.onrender.com

    # Quick HaluEval/TruthfulQA sample
    python tests/benchmark_runner.py --suite quick --corpus ./benchmark_corpus --limit 50 --api-url http://localhost:8000

    # Only HaluEval QA
    python tests/benchmark_runner.py --suite halueval_qa --corpus ./benchmark_corpus --limit 100

    # All supported normal suites, excluding halogen by default
    python tests/benchmark_runner.py --suite all --corpus ./benchmark_corpus --limit 500

    # Explicitly include halogen
    python tests/benchmark_runner.py --suite halogen --corpus ./benchmark_corpus --limit 100

    # Custom folder with *_A_clean.txt and *_B_hallucination.txt pairs
    python tests/benchmark_runner.py --suite custom --custom-dir ./my_pairs

Environment:

    SAS_API_KEY or SAS_KEY is used for authenticated /v1/diff.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import requests
except ImportError as exc:
    raise SystemExit("Missing dependency: requests. Install with: pip install requests") from exc

try:
    from tqdm import tqdm
except ImportError:
    tqdm = None


KAPPA_D = 0.56

BENCHMARK_GROUPS: dict[str, list[str]] = {
    "quick": [
        "halueval_dialogue",
        "halueval_general",
        "halueval_qa",
        "halueval_summarization",
        "truthfulqa",
    ],
    "all": [
        "halueval_dialogue",
        "halueval_general",
        "halueval_qa",
        "halueval_summarization",
        "truthfulqa",
    ],
    "halueval": [
        "halueval_dialogue",
        "halueval_general",
        "halueval_qa",
        "halueval_summarization",
    ],
    "halueval_dialogue": ["halueval_dialogue"],
    "halueval_general": ["halueval_general"],
    "halueval_qa": ["halueval_qa"],
    "halueval_summarization": ["halueval_summarization"],
    "truthfulqa": ["truthfulqa"],
    "halogen": ["halogen"],
}

SUITE_CHOICES = [
    "regression",
    "quick",
    "all",
    "halueval",
    "halueval_dialogue",
    "halueval_general",
    "halueval_qa",
    "halueval_summarization",
    "truthfulqa",
    "halogen",
    "custom",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def stable_case_id(text_a: str, text_b: str, source: str) -> str:
    raw = f"{source}\n{text_a}\n{text_b}".encode("utf-8", errors="ignore")
    return hashlib.sha256(raw).hexdigest()[:16]


def iter_progress(items: list[dict[str, Any]], desc: str):
    if tqdm is None:
        for item in items:
            yield item
    else:
        yield from tqdm(items, desc=desc, unit="case")


def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace").strip()


def make_pair(
    text_a: str,
    text_b: str,
    label: str,
    source: str,
    suite: str,
    expected_reason: str | None = None,
) -> dict[str, Any]:
    return {
        "id": stable_case_id(text_a, text_b, source),
        "text_a": text_a,
        "text_b": text_b,
        "label": label,
        "source": source,
        "suite": suite,
        "expected_reason": expected_reason,
    }


def load_regression_suite() -> list[dict[str, Any]]:
    """
    Built-in deterministic suite. No external corpus required.

    Labels:
    - hallucination: expected ISI < kappa / rupture signal
    - clean: expected ISI >= kappa
    """
    cases: list[dict[str, Any]] = []

    cases.append(make_pair(
        text_a="The Eiffel Tower is located in Paris, France. It was built in 1889. It is one of the most recognized landmarks in France.",
        text_b="The Eiffel Tower is located in Paris, France. It was built in 1889. It is one of the most recognized landmarks in France.",
        label="clean",
        source="regression/identical_eiffel",
        suite="regression",
        expected_reason="identical text should preserve invariance",
    ))

    cases.append(make_pair(
        text_a="The Eiffel Tower is located in Paris, France, and was built in 1889.",
        text_b="Paris, France is home to the Eiffel Tower, which was built in 1889.",
        label="clean",
        source="regression/faithful_paraphrase_eiffel",
        suite="regression",
        expected_reason="faithful paraphrase preserves source facts",
    ))

    cases.append(make_pair(
        text_a="The Eiffel Tower is located in Paris, France. It was built in 1889. It is one of the most recognized landmarks in France.",
        text_b="The Eiffel Tower is located in Berlin, Germany. It was built in 1950. It is one of the most recognized landmarks in Germany.",
        label="hallucination",
        source="regression/source_target_guard_eiffel",
        suite="regression",
        expected_reason="year and anchored entity/location mutation should trigger SourceTargetGuard",
    ))

    cases.append(make_pair(
        text_a="Python is a programming language commonly used for automation, data analysis, and web development.",
        text_b="A python is a large snake that lives in tropical regions and kills prey by constriction.",
        label="hallucination",
        source="regression/python_language_vs_snake",
        suite="regression",
        expected_reason="same surface token but different meaning/domain",
    ))

    cases.append(make_pair(
        text_a="The recommended dose is 5 mg once per day, and patients should not exceed the prescribed amount.",
        text_b="The recommended dose is 50 mg once per day, and patients should not exceed the prescribed amount.",
        label="hallucination",
        source="regression/dose_5mg_to_50mg",
        suite="regression",
        expected_reason="critical numeric mutation",
    ))

    cases.append(make_pair(
        text_a="Marie Curie was born in 1867 and won Nobel Prizes in Physics and Chemistry for her scientific work.",
        text_b="Marie Curie was born in 1867 and received Nobel Prizes in Physics and Chemistry for her scientific work.",
        label="clean",
        source="regression/marie_curie_faithful",
        suite="regression",
        expected_reason="faithful paraphrase preserves temporal and entity anchors",
    ))

    cases.append(make_pair(
        text_a="The company reported revenue of 10 million dollars in 2024 and described growth as moderate.",
        text_b="The company reported revenue of 100 million dollars in 2024 and described growth as moderate.",
        label="hallucination",
        source="regression/revenue_10m_to_100m",
        suite="regression",
        expected_reason="numeric magnitude mutation",
    ))

    cases.append(make_pair(
        text_a="Water freezes at 0 degrees Celsius under standard atmospheric pressure.",
        text_b="Water freezes at 0 degrees Celsius under standard atmospheric pressure.",
        label="clean",
        source="regression/water_freezing_identical",
        suite="regression",
        expected_reason="simple clean invariant",
    ))

    return cases


def load_pairs_from_folder(folder: Path, suite_name: str, limit: int | None = None) -> list[dict[str, Any]]:
    """
    Loads paired text files with naming:

        *_A_clean.txt
        *_B_hallucination.txt

    For every clean/hallucination pair, it creates:
    - a hallucination case: clean -> hallucination
    - a clean case: clean -> clean

    This produces both positive and negative examples when possible.
    """
    pairs: list[dict[str, Any]] = []
    if not folder.exists():
        print(f"[WARN] folder not found: {folder}")
        return pairs

    clean_files = sorted(folder.rglob("*_A_clean.txt"))

    for clean_file in clean_files:
        base_name = clean_file.name.replace("_A_clean.txt", "")
        hall_file = clean_file.with_name(f"{base_name}_B_hallucination.txt")

        try:
            clean_text = load_text(clean_file)
        except Exception as exc:
            print(f"[WARN] failed reading {clean_file}: {exc}")
            continue

        if clean_text:
            pairs.append(make_pair(
                text_a=clean_text,
                text_b=clean_text,
                label="clean",
                source=f"{suite_name}/{clean_file.relative_to(folder)}::clean",
                suite=suite_name,
                expected_reason="clean self-comparison",
            ))

        if hall_file.exists():
            try:
                hall_text = load_text(hall_file)
            except Exception as exc:
                print(f"[WARN] failed reading {hall_file}: {exc}")
                hall_text = ""

            if clean_text and hall_text:
                pairs.append(make_pair(
                    text_a=clean_text,
                    text_b=hall_text,
                    label="hallucination",
                    source=f"{suite_name}/{clean_file.relative_to(folder)}::hallucination",
                    suite=suite_name,
                    expected_reason="paired hallucination mutation",
                ))

        if limit and len(pairs) >= limit:
            return pairs[:limit]

    return pairs[:limit] if limit else pairs


def load_jsonl_custom(path: Path, suite_name: str, limit: int | None = None) -> list[dict[str, Any]]:
    """
    Optional JSONL format:

        {"text_a":"...", "text_b":"...", "label":"hallucination", "source":"case-1"}

    label must be "hallucination" or "clean".
    """
    pairs: list[dict[str, Any]] = []
    if not path.exists():
        print(f"[WARN] JSONL not found: {path}")
        return pairs

    with path.open("r", encoding="utf-8") as f:
        for idx, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except Exception as exc:
                print(f"[WARN] invalid JSONL line {idx}: {exc}")
                continue

            text_a = str(obj.get("text_a") or obj.get("source") or "").strip()
            text_b = str(obj.get("text_b") or obj.get("response") or "").strip()
            label = str(obj.get("label") or "").strip().lower()
            source = str(obj.get("source_id") or obj.get("source_name") or obj.get("id") or f"jsonl/{idx}")

            if label not in {"hallucination", "clean"}:
                print(f"[WARN] invalid label at line {idx}: {label!r}")
                continue
            if not text_a or not text_b:
                print(f"[WARN] missing text at line {idx}")
                continue

            pairs.append(make_pair(text_a, text_b, label, source, suite_name))
            if limit and len(pairs) >= limit:
                break

    return pairs


def load_benchmark_suite(args: argparse.Namespace) -> list[dict[str, Any]]:
    if args.suite == "regression":
        pairs = load_regression_suite()
        return pairs[:args.limit] if args.limit else pairs

    if args.suite == "custom":
        if not args.custom_dir and not args.jsonl:
            raise SystemExit("--suite custom requires --custom-dir or --jsonl")

        pairs: list[dict[str, Any]] = []
        if args.custom_dir:
            pairs.extend(load_pairs_from_folder(Path(args.custom_dir), "custom", args.limit))
        if args.jsonl:
            remaining = None if args.limit is None else max(0, args.limit - len(pairs))
            if remaining != 0:
                pairs.extend(load_jsonl_custom(Path(args.jsonl), "custom_jsonl", remaining))
        return pairs[:args.limit] if args.limit else pairs

    corpus_root = Path(args.corpus)
    if not corpus_root.exists():
        raise SystemExit(f"Corpus path does not exist: {corpus_root}")

    dirs = BENCHMARK_GROUPS.get(args.suite)
    if not dirs:
        raise SystemExit(f"Unknown suite: {args.suite}")

    pairs: list[dict[str, Any]] = []

    for dirname in dirs:
        suite_dir = corpus_root / dirname
        if not suite_dir.exists():
            print(f"[WARN] missing suite directory: {suite_dir}")
            continue

        remaining = None if args.limit is None else max(0, args.limit - len(pairs))
        if remaining == 0:
            break

        print(f"[INFO] loading suite: {dirname}")
        suite_pairs = load_pairs_from_folder(suite_dir, dirname, remaining)
        print(f"[INFO] loaded {len(suite_pairs)} cases from {dirname}")
        pairs.extend(suite_pairs)

        if args.limit and len(pairs) >= args.limit:
            break

    return pairs[:args.limit] if args.limit else pairs


def health_check(api_url: str, timeout: int) -> dict[str, Any]:
    url = api_url.rstrip("/") + "/health"
    try:
        resp = requests.get(url, timeout=timeout)
        return {
            "ok": resp.status_code == 200,
            "status_code": resp.status_code,
            "body": safe_json(resp),
        }
    except Exception as exc:
        return {
            "ok": False,
            "error": str(exc),
        }


def safe_json(resp: requests.Response) -> Any:
    try:
        return resp.json()
    except Exception:
        return resp.text[:500]


def run_case(pair: dict[str, Any], api_url: str, api_key: str, timeout: int, experimental: bool) -> dict[str, Any]:
    url = api_url.rstrip("/") + "/v1/diff"
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": api_key,
    }
    payload = {
        "text_a": pair["text_a"],
        "text_b": pair["text_b"],
        "experimental": experimental,
    }

    start = time.perf_counter()

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=timeout)
        elapsed_ms = round((time.perf_counter() - start) * 1000, 2)

        if resp.status_code != 200:
            return {
                "id": pair["id"],
                "source": pair["source"],
                "suite": pair["suite"],
                "label_expected": pair["label"],
                "http_status": resp.status_code,
                "error": safe_json(resp),
                "correct": False,
                "elapsed_ms": elapsed_ms,
            }

        data = resp.json()
        isi = data.get("isi", data.get("manifold_score", 0.0))
        try:
            isi_float = float(isi)
        except Exception:
            isi_float = 0.0

        verdict = data.get("verdict", "UNKNOWN")
        detected_hallucination = isi_float < KAPPA_D or verdict == "MANIFOLD_RUPTURE"
        expected_hallucination = pair["label"] == "hallucination"
        correct = detected_hallucination == expected_hallucination

        evidence = data.get("evidence") or {}
        manipulation_alert = data.get("manipulation_alert") or {}

        return {
            "id": pair["id"],
            "source": pair["source"],
            "suite": pair["suite"],
            "label_expected": pair["label"],
            "expected_reason": pair.get("expected_reason"),
            "http_status": resp.status_code,
            "isi": isi_float,
            "verdict": verdict,
            "confidence": data.get("confidence"),
            "detected_hallucination": detected_hallucination,
            "correct": correct,
            "manipulation_alert": {
                "triggered": manipulation_alert.get("triggered"),
                "sources": manipulation_alert.get("sources", []),
            },
            "fired_modules": evidence.get("fired_modules", [])[:10],
            "module_notes": evidence.get("module_notes", [])[:5],
            "elapsed_ms": elapsed_ms,
        }

    except requests.exceptions.Timeout:
        elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
        return {
            "id": pair["id"],
            "source": pair["source"],
            "suite": pair["suite"],
            "label_expected": pair["label"],
            "error": f"timeout after {timeout}s",
            "correct": False,
            "elapsed_ms": elapsed_ms,
        }
    except Exception as exc:
        elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
        return {
            "id": pair["id"],
            "source": pair["source"],
            "suite": pair["suite"],
            "label_expected": pair["label"],
            "error": str(exc),
            "correct": False,
            "elapsed_ms": elapsed_ms,
        }


def summarize(results: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(results)
    correct = sum(1 for r in results if r.get("correct") is True)
    errors = [r for r in results if "error" in r]
    scored = [r for r in results if "isi" in r]

    tp = sum(
        1 for r in results
        if r.get("label_expected") == "hallucination" and r.get("detected_hallucination") is True
    )
    fn = sum(
        1 for r in results
        if r.get("label_expected") == "hallucination" and r.get("detected_hallucination") is False
    )
    fp = sum(
        1 for r in results
        if r.get("label_expected") == "clean" and r.get("detected_hallucination") is True
    )
    tn = sum(
        1 for r in results
        if r.get("label_expected") == "clean" and r.get("detected_hallucination") is False
    )

    precision = tp / (tp + fp) if (tp + fp) else None
    recall = tp / (tp + fn) if (tp + fn) else None
    accuracy = correct / total if total else None
    f1 = (
        2 * precision * recall / (precision + recall)
        if precision is not None and recall is not None and (precision + recall) > 0
        else None
    )

    isi_values = [float(r["isi"]) for r in scored]
    elapsed_values = [float(r.get("elapsed_ms", 0.0)) for r in results if r.get("elapsed_ms") is not None]

    by_suite: dict[str, dict[str, Any]] = {}
    for r in results:
        suite = r.get("suite", "unknown")
        item = by_suite.setdefault(suite, {"total": 0, "correct": 0})
        item["total"] += 1
        if r.get("correct") is True:
            item["correct"] += 1

    for item in by_suite.values():
        item["accuracy"] = item["correct"] / item["total"] if item["total"] else None

    return {
        "total": total,
        "correct": correct,
        "errors": len(errors),
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "confusion_matrix": {
            "tp": tp,
            "fp": fp,
            "fn": fn,
            "tn": tn,
        },
        "isi": {
            "count": len(isi_values),
            "mean": statistics.mean(isi_values) if isi_values else None,
            "median": statistics.median(isi_values) if isi_values else None,
            "min": min(isi_values) if isi_values else None,
            "max": max(isi_values) if isi_values else None,
            "below_kappa": sum(1 for v in isi_values if v < KAPPA_D),
        },
        "latency_ms": {
            "mean": statistics.mean(elapsed_values) if elapsed_values else None,
            "median": statistics.median(elapsed_values) if elapsed_values else None,
            "max": max(elapsed_values) if elapsed_values else None,
        },
        "by_suite": by_suite,
    }


def print_summary(summary: dict[str, Any]) -> None:
    def pct(value: float | None) -> str:
        if value is None:
            return "n/a"
        return f"{value * 100:.2f}%"

    print("\n" + "=" * 72)
    print("BENCHMARK SUMMARY")
    print("=" * 72)
    print(f"Total:       {summary['total']}")
    print(f"Correct:     {summary['correct']}")
    print(f"Errors:      {summary['errors']}")
    print(f"Accuracy:    {pct(summary['accuracy'])}")
    print(f"Precision:   {pct(summary['precision'])}")
    print(f"Recall:      {pct(summary['recall'])}")
    print(f"F1:          {pct(summary['f1'])}")

    cm = summary["confusion_matrix"]
    print("\nConfusion matrix:")
    print(f"  TP: {cm['tp']}  FP: {cm['fp']}")
    print(f"  FN: {cm['fn']}  TN: {cm['tn']}")

    isi = summary["isi"]
    print("\nISI:")
    print(f"  count:       {isi['count']}")
    print(f"  mean:        {isi['mean']}")
    print(f"  median:      {isi['median']}")
    print(f"  min/max:     {isi['min']} / {isi['max']}")
    print(f"  below κD:    {isi['below_kappa']}")

    lat = summary["latency_ms"]
    print("\nLatency ms:")
    print(f"  mean:        {lat['mean']}")
    print(f"  median:      {lat['median']}")
    print(f"  max:         {lat['max']}")

    print("\nBy suite:")
    for suite, item in summary["by_suite"].items():
        print(f"  {suite}: {item['correct']}/{item['total']} ({pct(item['accuracy'])})")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Universal SAS benchmark runner",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--suite",
        choices=SUITE_CHOICES,
        default="regression",
        help="Benchmark suite to run",
    )
    parser.add_argument(
        "--corpus",
        default=os.environ.get("SAS_BENCHMARK_CORPUS", "./benchmark_corpus"),
        help="Benchmark corpus root",
    )
    parser.add_argument(
        "--custom-dir",
        default=None,
        help="Custom directory containing *_A_clean.txt / *_B_hallucination.txt pairs",
    )
    parser.add_argument(
        "--jsonl",
        default=None,
        help="Custom JSONL dataset with text_a/text_b/label",
    )
    parser.add_argument(
        "--api-url",
        default=os.environ.get("SAS_API_URL", "http://localhost:8000"),
        help="SAS API base URL",
    )
    parser.add_argument(
        "--api-key",
        default=os.environ.get("SAS_API_KEY") or os.environ.get("SAS_KEY") or "test-key-123",
        help="SAS API key. Defaults to SAS_API_KEY, SAS_KEY, or test-key-123",
    )
    parser.add_argument("--limit", type=int, default=None, help="Maximum number of cases")
    parser.add_argument("--timeout", type=int, default=45, help="Per-request timeout in seconds")
    parser.add_argument("--output", default=None, help="Output JSON path")
    parser.add_argument("--experimental", action="store_true", default=True, help="Send experimental=true")
    parser.add_argument("--no-experimental", dest="experimental", action="store_false", help="Send experimental=false")
    parser.add_argument("--fail-under-accuracy", type=float, default=None, help="Exit non-zero if accuracy is below this value, e.g. 0.95")
    parser.add_argument("--fail-under-recall", type=float, default=None, help="Exit non-zero if recall is below this value, e.g. 0.95")
    parser.add_argument("--quiet", action="store_true", help="Reduce per-case output")
    args = parser.parse_args()

    print("=" * 72)
    print("SAS UNIVERSAL BENCHMARK RUNNER")
    print("=" * 72)
    print(f"Suite:       {args.suite}")
    print(f"Corpus:      {args.corpus}")
    print(f"API URL:     {args.api_url}")
    print(f"Limit:       {args.limit}")
    print(f"κD:          {KAPPA_D}")
    print(f"Started:     {utc_now()}")

    health = health_check(args.api_url, timeout=10)
    if not health.get("ok"):
        print("\n[ERROR] API health check failed:")
        print(json.dumps(health, indent=2, ensure_ascii=False))
        return 2

    print("\n[OK] API health check passed")
    print(json.dumps(health.get("body"), indent=2, ensure_ascii=False))

    pairs = load_benchmark_suite(args)
    if not pairs:
        print("\n[ERROR] no benchmark cases loaded")
        return 2

    print(f"\nLoaded cases: {len(pairs)}")

    label_counts: dict[str, int] = {}
    for p in pairs:
        label_counts[p["label"]] = label_counts.get(p["label"], 0) + 1
    print(f"Label distribution: {label_counts}")

    results: list[dict[str, Any]] = []
    started = time.perf_counter()

    for pair in iter_progress(pairs, desc="Benchmarking"):
        result = run_case(
            pair=pair,
            api_url=args.api_url,
            api_key=args.api_key,
            timeout=args.timeout,
            experimental=args.experimental,
        )
        results.append(result)

        if not args.quiet:
            ok = "OK" if result.get("correct") else "FAIL"
            isi = result.get("isi", "n/a")
            verdict = result.get("verdict", result.get("error", "UNKNOWN"))
            print(f"[{ok}] {pair['source'][:70]} | label={pair['label']} | isi={isi} | verdict={verdict}")

    elapsed_total = round(time.perf_counter() - started, 3)
    summary = summarize(results)
    print_summary(summary)

    output = {
        "metadata": {
            "runner": "tests/benchmark_runner.py",
            "created_at": utc_now(),
            "suite": args.suite,
            "corpus": str(args.corpus),
            "api_url": args.api_url,
            "kappa_d": KAPPA_D,
            "limit": args.limit,
            "experimental": args.experimental,
            "elapsed_seconds": elapsed_total,
        },
        "summary": summary,
        "results": results,
    }

    output_path = args.output
    if not output_path:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        output_path = f"benchmark_results_{args.suite}_{stamp}.json"

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"\nSaved: {output_file}")
    print(f"SHA-256: {sha256_file(output_file)}")

    exit_code = 0
    if args.fail_under_accuracy is not None:
        acc = summary.get("accuracy")
        if acc is None or acc < args.fail_under_accuracy:
            print(f"[FAIL] accuracy {acc} < {args.fail_under_accuracy}")
            exit_code = 1

    if args.fail_under_recall is not None:
        recall = summary.get("recall")
        if recall is None or recall < args.fail_under_recall:
            print(f"[FAIL] recall {recall} < {args.fail_under_recall}")
            exit_code = 1

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
