"""
Dynamic tool loader for RAGNAROK CONTROL CENTER.

Scans the tools/ folder and auto-registers every valid tool module, so new
tools appear in the menu without ever touching menu.py.

Plugin standard for a tool module (see tools/weather.py, tools/password.py
for real examples after migration):

    TOOL_NAME = "Display name shown in the menu"   # optional, defaults to filename
    CATEGORY  = "Custom category"                   # optional, overrides sub-folder name

    def run() -> None:
        ...   # entry point called when the user selects this tool
              # ("main" is also accepted as an alias for "run")

Rules:
- Any *.py file directly inside tools/ belongs to the "Chung / General" category.
- Any *.py file inside a sub-folder of tools/ belongs to a category named after
  that sub-folder (e.g. tools/Media/x.py -> category "Media"), unless CATEGORY
  is set explicitly in the file.
- Files starting with "_" (including __init__.py) are ignored.
- A file with a syntax error, an import error, or missing run()/main() is
  skipped with a warning instead of crashing the whole program.
"""

import importlib.util
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List, Tuple

TOOLS_DIR = Path(__file__).resolve().parent / "tools"
DEFAULT_CATEGORY = "Chung / General"


@dataclass
class ToolEntry:
    name: str
    run: Callable[[], None]
    path: Path


def _prettify(stem: str) -> str:
    """Fallback display name: 'voice_recorder' -> 'Voice recorder'."""
    return stem.replace("_", " ").strip().capitalize()


def _load_module(py_file: Path):
    """Import a single .py file as an isolated module. Raises on any failure."""
    # Unique module name so files with the same name in different sub-folders
    # (e.g. tools/Media/tts.py vs tools/AI/tts.py) never collide.
    rel = py_file.relative_to(TOOLS_DIR.parent).with_suffix("")
    module_name = "ragnarok_dynamic." + ".".join(rel.parts)

    spec = importlib.util.spec_from_file_location(module_name, py_file)
    if spec is None or spec.loader is None:
        raise ImportError(f"Không tạo được import spec cho {py_file.name}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
    except Exception:
        sys.modules.pop(module_name, None)
        raise
    return module


def _entry_point(module) -> Callable[[], None]:
    """Return the tool's entry function: run() takes priority over main()."""
    func = getattr(module, "run", None) or getattr(module, "main", None)
    if not callable(func):
        raise AttributeError("Thiếu hàm run() hoặc main()")
    return func


def discover_tools() -> Tuple[Dict[str, List[ToolEntry]], List[Tuple[str, str]]]:
    """
    Scan tools/ and return:
      - categories: {category_name: [ToolEntry, ...]}
      - warnings:   [(relative_file_path, error_message), ...] for tools that
                     failed to load (logged instead of crashing the app)
    """
    categories: Dict[str, List[ToolEntry]] = {}
    warnings: List[Tuple[str, str]] = []

    if not TOOLS_DIR.is_dir():
        return categories, warnings

    for py_file in sorted(TOOLS_DIR.rglob("*.py")):
        if py_file.name.startswith("_"):
            continue  # skip __init__.py, private helpers, etc.

        try:
            module = _load_module(py_file)
            run_func = _entry_point(module)
        except Exception as exc:  # noqa: BLE001 - a broken tool must never crash the menu
            warnings.append((str(py_file.relative_to(TOOLS_DIR)), str(exc)))
            continue

        display_name = getattr(module, "TOOL_NAME", None) or _prettify(py_file.stem)

        sub_folder = py_file.relative_to(TOOLS_DIR).parent
        default_category = (
            DEFAULT_CATEGORY if sub_folder == Path(".") else sub_folder.parts[0]
        )
        category = getattr(module, "CATEGORY", None) or default_category

        categories.setdefault(category, []).append(
            ToolEntry(name=display_name, run=run_func, path=py_file)
        )

    for entries in categories.values():
        entries.sort(key=lambda e: e.name.lower())

    return categories, warnings
