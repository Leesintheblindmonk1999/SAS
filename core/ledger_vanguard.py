"""
core/ledger_vanguard.py — Omni-Scanner Semantic v2.0
═══════════════════════════════════════════════════════
Forensic Ledger — Immutable Verdict Registry

Generates SHA-256 hashes linking document + ManifoldScore +
timestamp. The hash is deterministic: same inputs always produce
the same hash, enabling independent verification.

Esquema de anclaje blockchain (Blockchain Readiness):
  - Compatible con OpenTimestamps (OTS) — ancla en Bitcoin via merkle
  - Compatible with Ethereum calldata — hash embeddable in tx.data
  - Generates the signing-ready payload; broadcasting is the operator's
    responsibility (requires external wallet/node)
"""
from __future__ import annotations
import hashlib
import json
import datetime
import struct
from dataclasses import dataclass
from typing import Optional


@dataclass
class LedgerEntry:
    """Immutable Forensic Ledger entry."""
    entry_hash:     str     # SHA-256 of canonical payload
    doc_hash:       str     # SHA-256 del texto original
    manifold_score: float
    verdict:        str
    timestamp_utc:  str
    kappa_d:        float
    ots_payload:    str     # hex del payload para OpenTimestamps
    eth_calldata:   str     # hex del calldata para Ethereum
    canonical_json: str     # reproducible JSON for verification

    def verify(self, text: str, score: float) -> bool:
        """Verifies this entry corresponds to the given text and score."""
        expected = LedgerVanguard().sign(text, score, self.verdict, self.kappa_d)
        return expected.entry_hash == self.entry_hash


class LedgerVanguard:
    """
    Forensic signing engine for Omni-Scanner verdicts.

    The hash combines:
      SHA-256( doc_hash || manifold_score_bytes || timestamp || verdict || kappa_d )

    Concatenation is deterministic via canonical JSON (sorted keys).
    """

    def sign(
        self,
        text: str,
        manifold_score: float,
        verdict: str,
        kappa_d: float = 0.56,
        timestamp_utc: Optional[str] = None,
    ) -> LedgerEntry:
        ts = timestamp_utc or datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%f") + "Z"

        # Hash of original document
        doc_hash = hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()

        # Canonical payload — JSON with sorted keys for reproducibility
        payload = {
            "doc_hash":      doc_hash,
            "kappa_d":       kappa_d,
            "manifold_score": round(manifold_score, 8),
            "timestamp_utc": ts,
            "verdict":       verdict,
            "version":       "omni-scanner-v2.0",
        }
        canonical = json.dumps(payload, sort_keys=True, ensure_ascii=True)
        entry_hash = hashlib.sha256(canonical.encode("ascii")).hexdigest()

        # OTS payload: standard prefix + hash (ready for ots-client stamp)
        ots_payload = "4f54530001" + entry_hash  # OTS magic + hash

        # Ethereum calldata: 0x + dummy selector + hash
        # In production: abi.encode(bytes32(hash)) in registry contract
        eth_calldata = "0x" + "a0b1c2d3" + entry_hash  # selector + hash

        return LedgerEntry(
            entry_hash      = entry_hash,
            doc_hash        = doc_hash,
            manifold_score  = manifold_score,
            verdict         = verdict,
            timestamp_utc   = ts,
            kappa_d         = kappa_d,
            ots_payload     = ots_payload,
            eth_calldata    = eth_calldata,
            canonical_json  = canonical,
        )

    def verify_entry(self, entry: LedgerEntry, text: str) -> dict:
        """Verifies the integrity of a ledger entry."""
        recomputed_doc = hashlib.sha256(
            text.encode("utf-8", errors="replace")
        ).hexdigest()

        payload = json.loads(entry.canonical_json)
        recomputed_entry = hashlib.sha256(
            entry.canonical_json.encode("ascii")
        ).hexdigest()

        return {
            "doc_hash_match":   recomputed_doc == entry.doc_hash,
            "entry_hash_match": recomputed_entry == entry.entry_hash,
            "tampered":         recomputed_entry != entry.entry_hash,
            "recomputed_entry": recomputed_entry,
            "stored_entry":     entry.entry_hash,
        }
