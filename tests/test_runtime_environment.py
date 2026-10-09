"""環境紀錄與鎖版契約的 fixture；完全不讀正式 data。"""
from __future__ import annotations

from contextlib import contextmanager
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import shutil
import tempfile
import tokenize
import unittest
from unittest.mock import Mock, patch

from loguru import logger
from packaging.requirements import Requirement
from packaging.specifiers import SpecifierSet

from core.logger import setup_run
from core import runtime_environment as runtime

ROOT = Path(__file__).resolve().parents[1]


@contextmanager
def working_directory(root):
    before = Path.cwd()
    try:
        os.chdir(root)
        yield
    finally:
        logger.remove()
        os.chdir(before)


class RuntimeEnvironmentTests(unittest.TestCase):
    def test_missing_git_is_unknown(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(runtime, "_git", return_value=None):
            result = runtime.collect_environment(Path(directory))
        self.assertEqual(result["git"], {"head": None, "tracked_dirty": None, "status": "UNKNOWN"})
        self.assertIsNone(result["constraints_sha256"])

    def test_git_failure_has_no_private_stderr(self):
        with patch.object(runtime.subprocess, "run", return_value=Mock(returncode=1, stderr="private token")):
            self.assertIsNone(runtime._git(ROOT, "status"))

    def test_git_missing_executable_and_timeout(self):
        for error in (OSError("private path"), subprocess.TimeoutExpired("git", 3)):
            with self.subTest(error=type(error).__name__), patch.object(runtime.subprocess, "run", side_effect=error):
                self.assertIsNone(runtime._git(ROOT, "status"))

    def test_verified_dirty_and_constraints_sha(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload = b"numpy==2.2.6\n"
            (root / "runtime-constraints.txt").write_bytes(payload)
            with patch.object(runtime, "_git", side_effect=[directory, "a" * 40, " M core/logger.py"]):
                result = runtime.collect_environment(root)
        self.assertTrue(result["git"]["tracked_dirty"])
        self.assertEqual(result["git"]["head"], "a" * 40)
        self.assertEqual(result["constraints_sha256"], hashlib.sha256(payload).hexdigest())

    def test_clean_git_and_missing_status_are_distinct(self):
        for status, expected in (("", False), (None, None)):
            with self.subTest(status=status), patch.object(runtime, "_git", side_effect=[str(ROOT), "b" * 40, status]):
                result = runtime.collect_environment(ROOT)
            self.assertEqual(result["git"]["tracked_dirty"], expected)
            self.assertEqual(result["git"]["status"], "UNKNOWN" if status is None else "VERIFIED")

    def test_package_names_are_normalized_and_sorted(self):
        distributions = [Mock(metadata={"Name": "Z_Name"}, version="1"),
                         Mock(metadata={"Name": "a"}, version="2"), Mock(metadata={}, version="3")]
        with patch.object(runtime.metadata, "distributions", return_value=distributions):
            result = runtime.collect_environment(ROOT)
        self.assertEqual(list(result["packages"]), ["a", "z-name"])
        self.assertEqual(result["packages"]["z-name"], "1")

    def test_public_metadata_excludes_paths_and_environment(self):
        with patch.dict(os.environ, {"LINEAGE_TEST_SECRET": "private-token-value"}):
            result = runtime.collect_environment(ROOT)
        serialized = json.dumps(result)
        self.assertNotIn(str(ROOT), serialized)
        self.assertNotIn("private-token-value", serialized)
        self.assertNotIn("executable", result)
        self.assertNotIn("environ", result)

    def test_setup_run_writes_json(self):
        with tempfile.TemporaryDirectory() as directory, working_directory(directory):
            _, paths = setup_run("fixture_environment")
            result = json.loads((paths.output_dir / "environment.json").read_text(encoding="utf-8"))
            self.assertEqual(result["schema_version"], "runtime_environment_v1")
            self.assertIn("python", result)
            self.assertTrue(paths.log_file.is_file())

    def test_no_output_records_environment_in_log(self):
        with tempfile.TemporaryDirectory() as directory, working_directory(directory):
            _, paths = setup_run("fixture_log_only", make_output=False)
            self.assertIsNone(paths.output_dir)
            self.assertIn("runtime_environment_v1", paths.log_file.read_text(encoding="utf-8"))
            self.assertFalse(Path("output").exists())

    def test_constraints_are_exact_and_unique(self):
        requirements = [Requirement(line) for line in (ROOT / "runtime-constraints.txt").read_text(encoding="utf-8").splitlines()
                        if line.strip() and not line.startswith("#")]
        names = [item.name.lower() for item in requirements]
        self.assertEqual(len(names), len(set(names)))
        for item in requirements:
            with self.subTest(package=item.name):
                specifiers = list(item.specifier)
                self.assertEqual(len(specifiers), 1)
                self.assertEqual(specifiers[0].operator, "==")
                self.assertNotIn("*", specifiers[0].version)
        self.assertIn("cloudpickle", names)
        self.assertTrue({"pip", "setuptools", "wheel"}.issubset(names))

    def test_active_dependency_closure_is_pinned(self):
        from importlib import metadata
        requirements = [Requirement(line) for line in (ROOT / "runtime-constraints.txt").read_text(encoding="utf-8").splitlines()
                        if line.strip() and not line.startswith("#")]
        names = {item.name.lower().replace("_", "-") for item in requirements}
        for parent in requirements:
            if parent.marker is not None and not parent.marker.evaluate():
                continue
            # 舊環境可能沒有 wheel；它沒有正式執行期依賴，乾淨驗證入口另檢版本。
            if parent.name == "wheel":
                continue
            for entry in metadata.requires(parent.name) or []:
                child = Requirement(entry)
                if child.marker is not None and not child.marker.evaluate({"extra": ""}):
                    continue
                with self.subTest(parent=parent.name, child=child.name):
                    self.assertIn(child.name.lower().replace("_", "-"), names)

    def test_python_policy_is_minor_not_patch(self):
        text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        value = next(line.split('"')[1] for line in text.splitlines() if line.startswith("requires-python"))
        policy = SpecifierSet(value)
        self.assertIn("3.10.19", policy)
        self.assertIn("3.10.20", policy)
        self.assertNotIn("3.9.0", policy)
        self.assertNotIn("3.14.0", policy)

    def test_constraints_decode_under_legacy_windows_locale(self):
        # 首次真實安裝曾在 pip 23／cp950 解碼失敗；保留最小反例。
        payload = (ROOT / "runtime-constraints.txt").read_bytes()
        self.assertIn(b"coding: utf-8", payload.splitlines()[0])
        encoding, _ = tokenize.detect_encoding(io.BytesIO(payload).readline)
        self.assertEqual(payload.decode(encoding), payload.decode("utf-8"))

    def test_build_scripts_do_not_delete_existing_environments(self):
        for name in ("build_uv.sh", "build_uv_mac.sh", "build_uv.ps1"):
            text = (ROOT / name).read_text(encoding="utf-8")
            with self.subTest(script=name):
                self.assertNotIn("rm -rf", text)
                self.assertNotIn("Remove-Item", text)
        for name in ("build_uv.sh", "build_uv.ps1"):
            text = (ROOT / name).read_text(encoding="utf-8")
            self.assertIn("runtime-constraints.txt", text)
            self.assertIn("--no-build-isolation", text)

    def test_run_and_main_preserve_environment_contract(self):
        with tempfile.TemporaryDirectory() as directory, working_directory(directory):
            result = runtime.run("fixture_api")
            self.assertEqual(result["schema_version"], "runtime_environment_v1")
            with patch("sys.argv", ["runtime_environment", "--program", "runtime_environment"]):
                runtime.main()
            self.assertTrue(any(Path("output/runtime_environment").glob("*/environment.json")))

    @unittest.skipUnless(os.name == "nt" and shutil.which("pwsh"), "Windows PowerShell 7 專用安裝拒絕測試")
    def test_windows_existing_target_is_not_changed(self):
        with tempfile.TemporaryDirectory() as directory:
            marker = Path(directory) / "preserve.txt"
            marker.write_text("保留使用者環境", encoding="utf-8")
            result = subprocess.run([shutil.which("pwsh"), "-NoProfile", "-File", str(ROOT / "build_uv.ps1"),
                                     "-Python", "不存在的Python", "-VenvDir", directory], capture_output=True, timeout=15)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(marker.read_text(encoding="utf-8"), "保留使用者環境")
            self.assertEqual(list(Path(directory).iterdir()), [marker])

    @unittest.skipUnless(os.name == "nt" and shutil.which("pwsh"), "Windows PowerShell 7 專用安裝拒絕測試")
    def test_windows_invalid_python_does_not_create_target(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "new_environment"
            result = subprocess.run([shutil.which("pwsh"), "-NoProfile", "-File", str(ROOT / "build_uv.ps1"),
                                     "-Python", "不存在的Python", "-VenvDir", str(target)], capture_output=True, timeout=15)
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(target.exists())


if __name__ == "__main__":
    unittest.main()
