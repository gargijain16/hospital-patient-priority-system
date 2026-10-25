"""Static audit proving the evaluated algorithm files use no built-in sorting or heap shortcuts.

Scans every module in ``algorithms/`` with the ``ast`` module for forbidden calls and imports.
"""
from __future__ import annotations

import ast
from pathlib import Path
from typing import Dict, List, Optional

FORBIDDEN_CALLS = {"sorted", "nlargest", "nsmallest", "sort_values", "heappush", "heappop", "heapify",
                   "heappushpop", "heapreplace", "insort", "bisect_left", "bisect_right", "min", "max"}
FORBIDDEN_ATTRS = FORBIDDEN_CALLS | {"sort"}
FORBIDDEN_IMPORTS = {"heapq", "bisect", "queue", "pandas", "numpy"}


def scan_file(path: Path) -> List[Dict]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    issues: List[Dict] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            f = node.func
            if isinstance(f, ast.Name) and f.id in FORBIDDEN_CALLS:
                issues.append({"file": path.name, "line": node.lineno, "issue": f"call to {f.id}()"})
            elif isinstance(f, ast.Attribute) and f.attr in FORBIDDEN_ATTRS:
                issues.append({"file": path.name, "line": node.lineno, "issue": f"call to .{f.attr}()"})
        elif isinstance(node, ast.Import):
            for a in node.names:
                if a.name.split(".")[0] in FORBIDDEN_IMPORTS:
                    issues.append({"file": path.name, "line": node.lineno, "issue": f"import {a.name}"})
        elif isinstance(node, ast.ImportFrom):
            if (node.module or "").split(".")[0] in FORBIDDEN_IMPORTS:
                issues.append({"file": path.name, "line": node.lineno, "issue": f"from {node.module} import ..."})
    return issues


def scan_algorithms(root: Optional[Path] = None) -> Dict[str, List[Dict]]:
    """Returns {file name: [issues]} for every algorithms/*.py file."""
    base = root or Path(__file__).resolve().parent.parent / "algorithms"
    result: Dict[str, List[Dict]] = {}
    for path in base.glob("*.py"):
        result[path.name] = scan_file(path)
    return result
