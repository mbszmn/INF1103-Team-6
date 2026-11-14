import ast
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PYTHON_FILES = sorted(
    path for path in PROJECT_ROOT.rglob("*.py")
    if not any(part.startswith(".") or part == "__pycache__" for part in path.relative_to(PROJECT_ROOT).parts)
)
APP_FILES = [path for path in PYTHON_FILES if "test_scripts" not in path.parts]


def file_id(path: Path) -> str:
    return path.relative_to(PROJECT_ROOT).as_posix()


def top_level(path: Path, kinds: tuple[type, ...]) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return [node.name for node in tree.body if isinstance(node, kinds)]


@pytest.mark.parametrize("path", PYTHON_FILES, ids=file_id)
def test_one_class_per_file(path):
    # the week 10 lecture rule
    classes = top_level(path, (ast.ClassDef,))
    assert len(classes) <= 1, f"{file_id(path)} has {len(classes)} classes: {', '.join(classes)}"


@pytest.mark.parametrize("path", APP_FILES, ids=file_id)
def test_no_procedural_functions_left_in_the_app(path):
    # phase 2 brief: no procedural style code left, everything lives in a class
    functions = top_level(path, (ast.FunctionDef, ast.AsyncFunctionDef))
    assert functions == [], f"{file_id(path)} still has plain functions: {', '.join(functions)}"
