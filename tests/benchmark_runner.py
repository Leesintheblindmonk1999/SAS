"""
tests/benchmark_runner.py - VERSIÓN RÁPIDA PARA PRUEBAS
Solo escanea carpetas halueval_* (evita halogen que es enorme)
"""

import os
import sys
import json
import argparse
import time
from pathlib import Path
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).parent.parent))


def load_corpus_pairs_fast(corpus_path: str, limit: int = None):
    """
    Versión rápida - solo busca en halueval_* y truthfulqa
    Evita la carpeta halogen que tiene miles de archivos
    """
    pairs = []
    corpus_root = Path(corpus_path)
    
    if not corpus_root.exists():
        print(f"❌ No existe: {corpus_root}")
        return pairs
    
    # Solo estas carpetas (halogen está excluida porque es enorme)
    benchmark_dirs = [
        "halueval_dialogue",
        "halueval_general", 
        "halueval_qa",
        "halueval_summarization",
        "truthfulqa"
    ]
    
    for bdir in benchmark_dirs:
        bpath = corpus_root / bdir
        if not bpath.exists():
            print(f"⚠️ No encontrado: {bdir} (saltando)")
            continue
        
        print(f"📁 Escaneando {bdir}...")
        
        # Buscar archivos *_A_clean.txt
        txt_files = sorted(bpath.glob("*_A_clean.txt"))
        
        for clean_file in txt_files:
            base_name = clean_file.stem.replace("_A_clean", "")
            hall_file = bpath / f"{base_name}_B_hallucination.txt"
            
            if hall_file.exists():
                try:
                    with open(clean_file, 'r', encoding='utf-8') as f:
                        text_a = f.read().strip()
                    with open(hall_file, 'r', encoding='utf-8') as f:
                        text_b = f.read().strip()
                    
                    pairs.append({
                        "text_a": text_a,
                        "text_b": text_b,
                        "source": f"{bdir}/{base_name}",
                        "label": "hallucination"
                    })
                    
                    if limit and len(pairs) >= limit:
                        return pairs[:limit]
                        
                except Exception as e:
                    print(f"  ⚠️ Error leyendo {clean_file.name}: {e}")
        
        print(f"  → Encontrados {len([p for p in pairs if p['source'].startswith(bdir)])} pares en {bdir}")
    
    return pairs[:limit] if limit else pairs


def run_audit_on_pair(pair, api_base_url="http://localhost:8000", timeout=30):
    """Llama a la API con timeout para evitar congelamiento"""
    import requests
    
    api_key = os.environ.get("SAS_API_KEY", "test-key-123")
    headers = {"X-API-Key": api_key}
    
    try:
        if pair["text_b"]:
            # Comparación de dos textos
            response = requests.post(
                f"{api_base_url}/v1/diff",
                json={
                    "text_a": pair["text_a"],
                    "text_b": pair["text_b"],
                    "experimental": True
                },
                headers=headers,
                timeout=timeout
            )
        else:
            # Auditoría de un solo texto
            response = requests.post(
                f"{api_base_url}/v1/audit",
                json={
                    "text": pair["text_a"],
                    "input_type": "generic",
                    "experimental": True
                },
                headers=headers,
                timeout=timeout
            )
        
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"HTTP {response.status_code}", "detail": response.text}
            
    except requests.exceptions.Timeout:
        return {"error": f"Timeout después de {timeout}s"}
    except Exception as e:
        return {"error": str(e)}


def run_benchmark(pairs, api_url="http://localhost:8000", limit=None):
    """Ejecuta benchmark con barra de progreso"""
    if limit and limit < len(pairs):
        pairs = pairs[:limit]
    
    results = []
    
    for i, pair in enumerate(tqdm(pairs, desc="🔍 Auditando", unit="par")):
        start_time = time.time()
        
        try:
            result = run_audit_on_pair(pair, api_url, timeout=45)
            elapsed = time.time() - start_time
            
            if "error" in result:
                results.append({
                    "source": pair["source"],
                    "label_expected": pair["label"],
                    "error": result["error"],
                    "correct": False,
                    "elapsed_seconds": elapsed
                })
            else:
                isi = result.get("manifold_score", result.get("score", 0))
                verdict = result.get("verdict", result.get("status", "UNKNOWN"))
                evidence = result.get("evidence", {})
                modules = evidence.get("fired_modules", [])
                
                is_hallucination = isi < 0.56
                expected_hallucination = (pair["label"] == "hallucination")
                correct = is_hallucination == expected_hallucination
                
                results.append({
                    "source": pair["source"],
                    "label_expected": pair["label"],
                    "isi": isi,
                    "verdict": verdict,
                    "detected_hallucination": is_hallucination,
                    "correct": correct,
                    "fired_modules": modules[:5],  # Solo primeros 5 para no saturar
                    "elapsed_seconds": elapsed
                })
                
                # Mostrar resultado en vivo
                status = "✅" if correct else "❌"
                tqdm.write(f"{status} {pair['source'][:40]} | ISI={isi:.3f} | {'ALUCINACIÓN' if is_hallucination else 'LIMPIO'} (esperado: {pair['label']}) | {elapsed:.1f}s")
                
        except Exception as e:
            results.append({
                "source": pair.get("source", "unknown"),
                "label_expected": pair.get("label", "unknown"),
                "error": str(e),
                "correct": False
            })
    
    return results


def main():
    parser = argparse.ArgumentParser(description="Benchmark rápido para SAS API")
    parser.add_argument("--corpus", default="C:\\Users\\conno\\Downloads\\SAS-Semántico\\benchmark_corpus")
    parser.add_argument("--api-url", default="http://localhost:8000")
    parser.add_argument("--limit", type=int, default=10, help="Número de pares a evaluar")
    parser.add_argument("--output", default="benchmark_results.json")
    args = parser.parse_args()
    
    print("=" * 60)
    print("🧪 BENCHMARK DE ALUCINACIONES - SAS OMNI-SCANNER")
    print("=" * 60)
    print(f"📂 Corpus: {args.corpus}")
    print(f"🎯 Límite: {args.limit} pares")
    print(f"🌐 API: {args.api_url}")
    print()
    
    # Health check
    import requests
    try:
        resp = requests.get(f"{args.api_url}/health", timeout=5)
        if resp.status_code == 200:
            print("✅ API disponible")
            print(f"   κD = {resp.json().get('kappa_d', '?')}")
        else:
            print("⚠️ API responde pero con código {resp.status_code}")
    except Exception as e:
        print(f"❌ ERROR: No se puede conectar a la API en {args.api_url}")
        print(f"   {e}")
        print("   Asegurate de correr: uvicorn api.main:app --reload")
        return
    
    print()
    print("📂 Cargando pares (evitando halogen que es enorme)...")
    pairs = load_corpus_pairs_fast(args.corpus, limit=args.limit)
    print(f"✅ Se cargaron {len(pairs)} pares.")
    
    if not pairs:
        print("\n❌ No se encontraron pares.")
        print("   Estructura esperada:")
        print("   benchmark_corpus/")
        print("   ├── halueval_dialogue/XXX_A_clean.txt + XXX_B_hallucination.txt")
        print("   ├── halueval_general/...")
        print("   └── truthfulqa/...")
        return
    
    # Mostrar distribución
    labels = {}
    for p in pairs:
        labels[p["label"]] = labels.get(p["label"], 0) + 1
    print(f"📊 Distribución: {labels}")
    print()
    
    print("🚀 Ejecutando benchmark...")
    print("   (cada par puede tomar 2-10 segundos dependiendo del texto)")
    print()
    
    results = run_benchmark(pairs, api_url=args.api_url, limit=args.limit)
    
    # Estadísticas
    total = len(results)
    correct = sum(1 for r in results if r.get("correct", False))
    has_isi = [r["isi"] for r in results if "isi" in r]
    avg_time = sum(r.get("elapsed_seconds", 0) for r in results) / total if total > 0 else 0
    
    print()
    print("=" * 60)
    print("📊 RESULTADOS DEL BENCHMARK")
    print("=" * 60)
    print(f"   Total evaluados: {total}")
    print(f"   Correctos: {correct} ({correct/total*100:.1f}%)")
    if has_isi:
        print(f"   ISI promedio: {sum(has_isi)/len(has_isi):.4f}")
        print(f"   ISI < κD (0.56): {len([i for i in has_isi if i < 0.56])}/{len(has_isi)}")
    print(f"   Tiempo promedio por par: {avg_time:.1f}s")
    print(f"   Tiempo total: {sum(r.get('elapsed_seconds', 0) for r in results):.1f}s")
    
    # Matriz de confusión
    tp = sum(1 for r in results if r.get("label_expected") == "hallucination" and r.get("detected_hallucination", False))
    fn = sum(1 for r in results if r.get("label_expected") == "hallucination" and not r.get("detected_hallucination", False))
    fp = sum(1 for r in results if r.get("label_expected") != "hallucination" and r.get("detected_hallucination", False))
    tn = sum(1 for r in results if r.get("label_expected") != "hallucination" and not r.get("detected_hallucination", False))
    
    if tp + fn > 0:
        recall = tp / (tp + fn) * 100
        print(f"\n   🎯 Recall (hallucination detection): {recall:.1f}% ({tp}/{tp+fn})")
    if tp + fp > 0:
        precision = tp / (tp + fp) * 100
        print(f"   🎯 Precision: {precision:.1f}% ({tp}/{tp+fp})")
    
    # Guardar resultados
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\n✅ Resultados guardados en {args.output}")
    
    # Mostrar errores si los hay
    errors = [r for r in results if "error" in r]
    if errors:
        print(f"\n⚠️ {len(errors)} errores:")
        for e in errors[:3]:
            print(f"   - {e['source']}: {e.get('error', 'unknown')[:80]}")


if __name__ == "__main__":
    main()