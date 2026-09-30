"""Preserve completed derived experiment artifacts outside temporary worktrees.

No sources are changed or removed. ZIP64 stored archives contain only explicit
output directories, never formal/raw feature data or credentials.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from pathlib import Path

from core.logger import setup_run


def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run(pools, *, destination: Path, paths, log) -> dict:
    """Archive exact completed output roots; refuse overwrites and active runs."""
    destination = Path(destination).resolve()
    destination.mkdir(parents=True, exist_ok=True)
    roots = [Path(p).resolve() for p in pools]
    if len({r.name for r in roots}) != len(roots):
        raise ValueError("archive input directory names must be unique")
    manifests = []
    for root in roots:
        if not root.is_dir():
            raise ValueError(f"artifact root is missing: {root}")
        status_path = root / "run_status.json"
        if status_path.exists():
            state = json.loads(status_path.read_text(encoding="utf-8"))
            if len(state["runs"]) != state["declared_run_count"] or any(r["status"] not in {"completed", "failed", "skipped"} for r in state["runs"].values()):
                raise ValueError("archive refuses active or incomplete run inventories")
        archive = destination / f"fault_type_{root.name}.zip"
        partial = archive.with_suffix(".zip.partial")
        if archive.exists() or partial.exists():
            raise ValueError(f"archive already exists; refusing overwrite: {archive}")
        entries = []
        with zipfile.ZipFile(partial, "x", compression=zipfile.ZIP_STORED, allowZip64=True) as bundle:
            for source in sorted(root.rglob("*")):
                if not source.is_file():
                    continue
                resolved = source.resolve()
                if source.is_symlink() or root not in resolved.parents:
                    raise ValueError("archive input contains an external link")
                relative = root.name + "/" + source.relative_to(root).as_posix()
                info = zipfile.ZipInfo(relative, date_time=(1980, 1, 1, 0, 0, 0))
                digest = hashlib.sha256()
                size = 0
                with source.open("rb") as reader, bundle.open(info, "w", force_zip64=True) as writer:
                    for chunk in iter(lambda: reader.read(1024 * 1024), b""):
                        writer.write(chunk)
                        digest.update(chunk)
                        size += len(chunk)
                entries.append({"path": relative, "bytes": size, "sha256": digest.hexdigest()})
            index = {"source_root": str(root), "files": entries,
                "path_note": "internal summaries retain original worktree paths; files are preserved under the root timestamp for portable extraction"}
            bundle.writestr("BUNDLE_INDEX.json", json.dumps(index, sort_keys=True, ensure_ascii=False))
        partial.rename(archive)
        with zipfile.ZipFile(archive) as bundle:
            bad = bundle.testzip()
            if bad:
                raise ValueError(f"archive CRC verification failed: {bad}")
        result = {"path": str(archive), "sha256": _sha(archive), "bytes": archive.stat().st_size,
            "source_root": str(root), "source_files": len(entries), "crc_status": "PASS"}
        manifests.append(result)
        log.info("verified archive {} bytes={} files={}", archive, result["bytes"], len(entries))
    index = {"archives": manifests, "source_files_removed": False, "contains_raw_data": False}
    (paths.output_dir / "archive_index.json").write_text(json.dumps(index, indent=2), encoding="utf-8")
    return index


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", action="append", type=Path, required=True)
    parser.add_argument("--destination", type=Path, required=True)
    args = parser.parse_args()
    log, paths = setup_run("fault_type_archive")
    # CLI deliberately accepts only this project's generated outputs.
    output = (Path.cwd() / "output").resolve()
    if any(output not in root.resolve().parents for root in args.output_root):
        raise ValueError("only explicit project output subdirectories can be archived")
    run(args.output_root, destination=args.destination, paths=paths, log=log)


if __name__ == "__main__":
    main()
