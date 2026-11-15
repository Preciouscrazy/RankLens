"""Subprocess-based CLI, file-safety and evidence regression tests."""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class RankLensCliTests(unittest.TestCase):
    def run_cli(self, *args, cwd=None):
        return subprocess.run(
            [sys.executable, "-m", "ranklens.cli", *(str(arg) for arg in args)],
            cwd=cwd or ROOT, capture_output=True, text=True, check=False, timeout=20,
        )

    def test_stdout_matches_golden_json(self):
        response = self.run_cli(ROOT / "data" / "sample_matches.json")
        self.assertEqual(response.returncode, 0, response.stderr)
        expected = json.loads((ROOT / "evidence" / "sample-report.json").read_text(encoding="utf-8"))
        self.assertEqual(json.loads(response.stdout), expected)

    def test_explicit_output_matches_golden_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "report.json"
            response = self.run_cli(ROOT / "data" / "sample_matches.json", "--output", output)
            self.assertEqual(response.returncode, 0, response.stderr)
            expected = json.loads((ROOT / "evidence" / "sample-report.json").read_text(encoding="utf-8"))
            self.assertEqual(json.loads(output.read_text(encoding="utf-8")), expected)

    def test_existing_output_replaced_without_temporary_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "report.json"
            output.write_text("old", encoding="utf-8")
            response = self.run_cli(ROOT / "data" / "sample_matches.json", "--output", output)
            self.assertEqual(response.returncode, 0, response.stderr)
            self.assertEqual(json.loads(output.read_text())["records_analyzed"], 3)
            self.assertFalse(list(Path(tmp).glob("*.tmp")))

    def test_reject_input_output_same_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "input.json"
            source.write_bytes((ROOT / "data" / "sample_matches.json").read_bytes())
            before = source.read_bytes()
            response = self.run_cli(source, "--output", source)
            self.assertEqual(response.returncode, 1)
            self.assertIn("same file", response.stderr)
            self.assertEqual(source.read_bytes(), before)

    def test_reject_hardlink_to_input(self):
        with tempfile.TemporaryDirectory() as tmp:
            source, alias = Path(tmp) / "input.json", Path(tmp) / "alias.json"
            source.write_bytes((ROOT / "data" / "sample_matches.json").read_bytes())
            try:
                os.link(source, alias)
            except OSError as exc:
                self.skipTest(f"Hard links unsupported: {exc}")
            before = source.read_bytes()
            response = self.run_cli(source, "--output", alias)
            self.assertEqual(response.returncode, 1)
            self.assertEqual(source.read_bytes(), before)

    def test_bad_json_keeps_previous_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            source, output = Path(tmp) / "bad.json", Path(tmp) / "report.json"
            source.write_text("{invalid", encoding="utf-8")
            output.write_text("keep this", encoding="utf-8")
            response = self.run_cli(source, "--output", output)
            self.assertEqual(response.returncode, 1)
            self.assertIn("Error:", response.stderr)
            self.assertEqual(output.read_text(), "keep this")

    def test_bad_record_keeps_previous_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            source, output = Path(tmp) / "bad.json", Path(tmp) / "report.json"
            source.write_text('[{"player_id":"x"}]', encoding="utf-8")
            output.write_text("keep this", encoding="utf-8")
            response = self.run_cli(source, "--output", output)
            self.assertEqual(response.returncode, 1)
            self.assertIn("record 1:", response.stderr)
            self.assertEqual(output.read_text(), "keep this")

    def test_missing_input_returns_one(self):
        with tempfile.TemporaryDirectory() as tmp:
            response = self.run_cli(Path(tmp) / "missing.json")
            self.assertEqual(response.returncode, 1)
            self.assertIn("Error:", response.stderr)

    def test_empty_json_list_outputs_empty_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "empty.json"
            source.write_text("[]", encoding="utf-8")
            response = self.run_cli(source)
            self.assertEqual(response.returncode, 0, response.stderr)
            self.assertEqual(json.loads(response.stdout)["records_analyzed"], 0)

    def test_top_level_object_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "object.json"
            source.write_text("{}", encoding="utf-8")
            response = self.run_cli(source)
            self.assertEqual(response.returncode, 1)
            self.assertIn("JSON array", response.stderr)

    def test_help_exits_zero(self):
        response = self.run_cli("--help")
        self.assertEqual(response.returncode, 0)
        self.assertIn("--output", response.stdout)

    def test_missing_argument_is_usage_error(self):
        response = self.run_cli()
        self.assertEqual(response.returncode, 2)
        self.assertIn("required", response.stderr)

    def test_extra_argument_is_usage_error(self):
        response = self.run_cli(ROOT / "data" / "sample_matches.json", "unexpected")
        self.assertEqual(response.returncode, 2)

    def test_bom_json_accepted(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "bom.json"
            source.write_text('[]', encoding="utf-8-sig")
            response = self.run_cli(source)
            self.assertEqual(response.returncode, 0, response.stderr)


if __name__ == "__main__":
    unittest.main()
