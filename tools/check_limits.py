"""
Purpose:  Enforce the hard limits from CODING_STANDARDS.md (file, line, function size; headers).
Layer:    tools (dev-only; run by pre-commit, never imported by the engine or the web app)
Exports:  main(argv) -> exit code; prints one line per violation
Depends:  standard library only
"""

from __future__ import annotations

import ast
import sys
from collections.abc import Iterator
from pathlib import Path

MAX_FILE_LINES = 300
MAX_LINE_CHARS = 100
MAX_FUNCTION_LINES = 20
HEADER_KEYS = ("Purpose:", "Layer:")
HEADER_WINDOW = 12
SOURCE_SUFFIXES = {".py", ".ts", ".vue", ".css", ".js"}
SKIP_PARTS = {"node_modules", "dist", ".venv", "venv", "__pycache__", "build", ".git"}


def main(argv: list[str]) -> int:
    """Check the given files (or every source file under the current directory)."""
    paths = [Path(arg) for arg in argv] or list(_walk(Path(".")))
    problems = [problem for path in paths if _is_source(path) for problem in check_file(path)]
    for problem in problems:
        print(problem)
    return 1 if problems else 0


def check_file(path: Path) -> list[str]:
    """Every limit violated by one file."""
    source = path.read_text(encoding="utf-8")
    lines = source.splitlines()
    problems = _check_size(path, lines) + _check_header(path, lines)
    if path.suffix == ".py":
        problems += _check_functions(path, source)
    return problems


def _walk(root: Path) -> Iterator[Path]:
    yield from (path for path in root.rglob("*") if path.is_file())


def _is_source(path: Path) -> bool:
    skipped = bool(SKIP_PARTS & set(path.parts)) or path.name.endswith(".d.ts")
    return path.suffix in SOURCE_SUFFIXES and not skipped


def _check_size(path: Path, lines: list[str]) -> list[str]:
    problems = []
    if len(lines) > MAX_FILE_LINES:
        problems.append(f"{path}: {len(lines)} lines (max {MAX_FILE_LINES})")
    for number, line in enumerate(lines, 1):
        if len(line) > MAX_LINE_CHARS:
            problems.append(f"{path}:{number}: {len(line)} chars (max {MAX_LINE_CHARS})")
    return problems


def _check_header(path: Path, lines: list[str]) -> list[str]:
    head = "\n".join(lines[:HEADER_WINDOW])
    missing = [key for key in HEADER_KEYS if key not in head]
    return [f"{path}:1: header is missing {', '.join(missing)}"] if missing else []


def _check_functions(path: Path, source: str) -> list[str]:
    lines = source.splitlines()
    problems = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            size = _code_lines(node, lines)
            if size > MAX_FUNCTION_LINES:
                problems.append(
                    f"{path}:{node.lineno}: {node.name}() has {size} code lines "
                    f"(max {MAX_FUNCTION_LINES})"
                )
    return problems


def _code_lines(node: ast.FunctionDef | ast.AsyncFunctionDef, lines: list[str]) -> int:
    skip = _docstring_lines(node)
    span = range(node.lineno, (node.end_lineno or node.lineno) + 1)
    return sum(1 for number in span if number not in skip and _is_code(lines[number - 1]))


def _docstring_lines(node: ast.FunctionDef | ast.AsyncFunctionDef) -> set[int]:
    first = node.body[0] if node.body else None
    if not (isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant)):
        return set()
    if not isinstance(first.value.value, str):
        return set()
    return set(range(first.lineno, (first.end_lineno or first.lineno) + 1))


def _is_code(line: str) -> bool:
    stripped = line.strip()
    return bool(stripped) and not stripped.startswith("#")


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
