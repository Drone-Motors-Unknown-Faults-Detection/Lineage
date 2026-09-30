import hashlib
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from loguru import logger
from core.logger import RunPaths
from experiments.fault_type_archive import run


class FaultTypeArchiveTests(unittest.TestCase):
    def test_archive_verifies_content_preserves_source_and_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source, out = root / "completed", root / "index"
            source.mkdir()
            out.mkdir()
            (source / "evidence.json").write_text('{"synthetic":true}')
            paths = RunPaths("unit", "unit", root / "unit.log", out)
            result = run([source], destination=root / "archive", paths=paths, log=logger)
            archive = Path(result["archives"][0]["path"])
            self.assertEqual(hashlib.sha256(archive.read_bytes()).hexdigest(), result["archives"][0]["sha256"])
            with zipfile.ZipFile(archive) as bundle:
                index = json.loads(bundle.read("BUNDLE_INDEX.json"))
                blob = bundle.read("completed/evidence.json")
                self.assertEqual(hashlib.sha256(blob).hexdigest(), index["files"][0]["sha256"])
            self.assertTrue((source / "evidence.json").exists())
            with self.assertRaisesRegex(ValueError, "refusing overwrite"):
                run([source], destination=root / "archive", paths=paths, log=logger)


if __name__ == "__main__":
    unittest.main()
