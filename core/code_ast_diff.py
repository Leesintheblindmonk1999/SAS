"""
Code-AST Fingerprinting Module — Omni-Scanner
═══════════════════════════════════════════════════════════════════════════════
Improvements over v1:
- Identifier anonymization (ignores variable/function names)
- SHA‑256 structural hash (O(1) comparison instead of O(N²))
- Special weight for numeric/string constants
- Change localisation (control flow nodes weigh more)
- Integration with manifold (70% AST, 30% TDA for code domain)

Author: Gonzalo Emir Durante
Registry: EX-2026-18792778
"""

import ast
import hashlib
from functools import lru_cache
from typing import Tuple, Set, List
from difflib import SequenceMatcher  # only for fallback on short lists


# ── AST anonymisation (replace identifiers with 'VAR') ──────────────────────
class AnonymizingTransformer(ast.NodeTransformer):
    """Replaces variable names, function names, attributes with 'VAR'."""
    def visit_Name(self, node):
        # Do not anonymise built‑ins or language keywords
        if node.id in {'True', 'False', 'None', 'print', 'len', 'range',
                       'int', 'str', 'float', 'list', 'dict', 'set', 'tuple'}:
            return node
        return ast.Name(id='VAR', ctx=node.ctx)

    def visit_FunctionDef(self, node):
        node.name = 'VAR'
        self.generic_visit(node)
        return node

    def visit_ClassDef(self, node):
        node.name = 'VAR'
        self.generic_visit(node)
        return node

    def visit_Attribute(self, node):
        self.generic_visit(node)
        node.attr = 'VAR'
        return node

    def visit_arg(self, node):
        node.arg = 'VAR'
        return node


def anonymize_ast(tree: ast.AST) -> ast.AST:
    """Return an AST with all identifiers anonymised."""
    return AnonymizingTransformer().visit(tree)


# ── Structural hash extraction (O(1) after hashing) ────────────────────────
def _extract_structure_hash(node: ast.AST, depth: int = 0) -> str:
    """
    Generate a SHA‑256 hash of the AST structure (ignoring names).
    Maximum depth is 10 to avoid combinatorial explosion.
    """
    if depth > 10:
        return hashlib.sha256(b"MAX_DEPTH").hexdigest()

    node_type = type(node).__name__
    value_repr = ""
    if isinstance(node, ast.Constant):
        val = node.value
        if isinstance(val, bool):
            value_repr = f"BOOL:{val}"
        elif isinstance(val, (int, float)):
            value_repr = f"NUMBER:{type(val).__name__}"
        elif isinstance(val, str):
            # Store only the length to avoid huge strings
            value_repr = f"STR_LEN:{len(val)}"
        else:
            value_repr = "CONST"

    children = []
    for child in ast.iter_child_nodes(node):
        children.append(_extract_structure_hash(child, depth + 1))

    # Sort children so the hash is order‑independent
    children.sort()
    combined = f"{node_type}|{value_repr}|" + "|".join(children)
    return hashlib.sha256(combined.encode()).hexdigest()


def _extract_constants(tree: ast.AST) -> Set[str]:
    """Extract numeric and string constants for specific comparison."""
    constants = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            val = node.value
            if isinstance(val, (int, float)):
                constants.add(f"NUMBER:{val}")
            elif isinstance(val, str):
                constants.add(f"STR:{hash(val)}")  # hash to avoid storing long strings
            elif isinstance(val, bool):
                constants.add(f"BOOL:{val}")
    return constants


def _extract_control_nodes(tree: ast.AST) -> List[str]:
    """Extract control‑flow node types (if, for, while, etc.) preserving nesting order."""
    nodes = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.If, ast.For, ast.While, ast.ExceptHandler, ast.Try)):
            nodes.append(type(node).__name__)
    return nodes


# ── Main comparison function ────────────────────────────────────────────────
@lru_cache(maxsize=128)
def ast_similarity_v2(code_a: str, code_b: str) -> Tuple[float, float, float, float, float]:
    """
    Returns:
        structure_sim (hash equality), constants_sim, control_sim,
        complexity_sim, node_count_sim
    """
    try:
        tree_a = ast.parse(code_a)
        tree_b = ast.parse(code_b)
    except SyntaxError:
        # If either is not valid Python, fallback to neutral scores
        return 0.5, 0.5, 0.5, 0.5, 0.5

    anon_a = anonymize_ast(tree_a)
    anon_b = anonymize_ast(tree_b)

    # 1. Structural hash (O(1))
    hash_a = _extract_structure_hash(anon_a)
    hash_b = _extract_structure_hash(anon_b)
    structure_sim = 1.0 if hash_a == hash_b else 0.0

    # 2. Constants (high weight if they change)
    const_a = _extract_constants(tree_a)   # use original tree, not anonymised
    const_b = _extract_constants(tree_b)
    if not const_a and not const_b:
        constants_sim = 1.0
    else:
        inter = const_a.intersection(const_b)
        union = const_a.union(const_b)
        constants_sim = len(inter) / len(union) if union else 1.0

    # 3. Control flow nodes
    control_a = _extract_control_nodes(tree_a)
    control_b = _extract_control_nodes(tree_b)
    if not control_a and not control_b:
        control_sim = 1.0
    else:
        control_sim = SequenceMatcher(None, control_a, control_b).ratio()

    # 4. Cyclomatic complexity (approximate)
    def count_branching(tree):
        cnt = 1
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.For, ast.While, ast.ExceptHandler)):
                cnt += 1
            elif isinstance(node, ast.BoolOp):
                cnt += len(node.values) - 1
        return cnt
    comp_a = count_branching(tree_a)
    comp_b = count_branching(tree_b)
    max_comp = max(comp_a, comp_b)
    complexity_sim = 1.0 - abs(comp_a - comp_b) / max_comp if max_comp > 0 else 1.0

    # 5. Node count (detect size changes)
    def count_nodes(tree):
        return sum(1 for _ in ast.walk(tree))
    nodes_a = count_nodes(tree_a)
    nodes_b = count_nodes(tree_b)
    max_nodes = max(nodes_a, nodes_b)
    node_count_sim = 1.0 - abs(nodes_a - nodes_b) / max_nodes if max_nodes > 0 else 1.0

    return structure_sim, constants_sim, control_sim, complexity_sim, node_count_sim


def code_diff_isi(code_a: str, code_b: str) -> float:
    """
    ISI_CODE for the 'code' domain.

    Weights (based on Gemini's proposal + own adjustments):
        - Structural hash: 40% (identical structure → high similarity)
        - Constants:       25% (changes in numbers/strings are critical)
        - Control flow:    15% (if/for/while)
        - Complexity:      10%
        - Node count:      10%
    """
    struct_sim, const_sim, control_sim, comp_sim, node_sim = ast_similarity_v2(code_a, code_b)

    # Strict veto: different structural hash → certain hallucination
    if struct_sim == 0.0:
        return 0.1

    # Heavy penalty if constants changed a lot
    if const_sim < 0.5:
        return 0.2

    isi = (0.40 * struct_sim +
           0.25 * const_sim +
           0.15 * control_sim +
           0.10 * comp_sim +
           0.10 * node_sim)

    # Additional penalty if control flow is very different
    if control_sim < 0.6:
        isi *= 0.7

    return max(0.0, min(1.0, isi))


# ── Fallback for non‑Python languages (optional) ───────────────────────────
def code_diff_isi_fallback(code_a: str, code_b: str) -> float:
    """Simplified version for other languages (only Python is natively supported)."""
    # Currently returns neutral 0.5; can be extended with tree‑sitter later
    return 0.5


# ── CLI for quick testing ──────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("Usage: python code_ast_diff.py <file_a> <file_b>")
        sys.exit(1)

    with open(sys.argv[1], 'r') as f:
        code_a = f.read()
    with open(sys.argv[2], 'r') as f:
        code_b = f.read()

    isi = code_diff_isi(code_a, code_b)
    print(f"ISI_CODE = {isi:.6f}")
    print("→ HALLUCINATION" if isi < 0.56 else "→ COHERENT")