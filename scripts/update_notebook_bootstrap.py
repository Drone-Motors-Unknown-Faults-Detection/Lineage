#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]


NEW_BOOTSTRAP = [
    "# --- logging bootstrap (auto-added) ---\n",
    "import importlib\n",
    "import logger as _logger_mod\n",
    "_logger_mod = importlib.reload(_logger_mod)\n",
    "save_plot = _logger_mod.save_plot\n",
    "setup_logger = _logger_mod.setup_logger\n",
    "tee_std_to_file = _logger_mod.tee_std_to_file\n",
    "\n",
    "LOG, RUN_PATHS = setup_logger('notebook', console=False)\n",
    "_tee_ctx = tee_std_to_file(RUN_PATHS.log_file)\n",
    "_tee_ctx.__enter__()\n",
    "import atexit\n",
    "atexit.register(_tee_ctx.__exit__, None, None, None)\n",
    "\n",
    "# Auto-save matplotlib figures on plt.show()\n",
    "try:\n",
    "    import matplotlib.pyplot as plt\n",
    "    if not getattr(plt, '_ancestor_save_plot_patched', False):\n",
    "        plt._ancestor_save_plot_patched = True\n",
    "        _orig_show = plt.show\n",
    "        import time\n",
    "        plt._ancestor_show_in_progress = False\n",
    "        plt._ancestor_last_save_ts = 0.0\n",
    "\n",
    "        def _show_and_save(*args, **kwargs):\n",
    "            # Guard against backend calling show() multiple times\n",
    "            if getattr(plt, '_ancestor_show_in_progress', False):\n",
    "                return _orig_show(*args, **kwargs)\n",
    "            now = time.monotonic()\n",
    "            if now - float(getattr(plt, '_ancestor_last_save_ts', 0.0)) < 0.5:\n",
    "                return _orig_show(*args, **kwargs)\n",
    "            plt._ancestor_show_in_progress = True\n",
    "            try:\n",
    "                # Save only the current figure once\n",
    "                save_plot(plt, LOG, RUN_PATHS)\n",
    "            except Exception:\n",
    "                pass\n",
    "            try:\n",
    "                return _orig_show(*args, **kwargs)\n",
    "            finally:\n",
    "                plt._ancestor_last_save_ts = time.monotonic()\n",
    "                try:\n",
    "                    plt.close(plt.gcf())\n",
    "                except Exception:\n",
    "                    pass\n",
    "                plt._ancestor_show_in_progress = False\n",
    "\n",
    "        plt.show = _show_and_save\n",
    "    else:\n",
    "        # already patched in this kernel\n",
    "        pass\n",
    "\n",
    "except Exception:\n",
    "    pass\n",
    "# --- end logging bootstrap ---\n",
]


def iter_ipynb_files() -> Iterable[Path]:
    yield from ROOT.glob("*.ipynb")


def update_bootstrap_cell(nb: dict) -> bool:
    changed = False
    for cell in nb.get("cells", []):
        if cell.get("cell_type") != "code":
            continue
        src = cell.get("source", [])
        if not isinstance(src, list):
            continue
        if any("# --- logging bootstrap (auto-added) ---" in ln for ln in src):
            if src != NEW_BOOTSTRAP:
                cell["source"] = NEW_BOOTSTRAP
                cell["execution_count"] = None
                cell["outputs"] = []
                changed = True
            break
    return changed


def main() -> None:
    changed_files: list[str] = []
    for p in iter_ipynb_files():
        nb = json.loads(p.read_text(encoding="utf-8"))
        if update_bootstrap_cell(nb):
            p.write_text(json.dumps(nb, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
            changed_files.append(p.name)

    print(f"Updated {len(changed_files)} notebook(s).")
    for n in changed_files:
        print(f"- {n}")


if __name__ == "__main__":
    main()

