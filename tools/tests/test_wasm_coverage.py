"""Exercise coverage classification with the real Emscripten compiler."""

from pathlib import Path
import tempfile
import unittest

from tools.wasm_coverage import compile_unit, WASM_HEADER


class CompilationTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.source = self.root / "fixture.c"
        self.output = self.root / "report"

    def compile(self):
        return compile_unit(str(self.source), ["emcc", "-O0"], self.output)

    def test_real_wasm_object(self):
        self.source.write_text("int add(int a, int b) { return a + b; }\n")
        result = self.compile()
        self.assertEqual(result["status"], "passed")
        self.assertEqual(result["exit_code"], 0)
        self.assertEqual(
            (self.output / "objects/fixture.o").read_bytes()[:8], WASM_HEADER
        )

    def test_failure_cannot_reuse_stale_object(self):
        self.source.write_text("int value(void) { return 1; }\n")
        self.compile()
        self.source.write_text("#error deliberately_broken_fixture\n")
        result = self.compile()
        self.assertEqual(result["status"], "failed")
        self.assertNotEqual(result["exit_code"], 0)
        self.assertFalse((self.output / "objects/fixture.o").exists())
        self.assertIn(
            "deliberately_broken_fixture",
            (self.output / result["log"]).read_text(),
        )

    def test_missing_compiler_is_not_a_source_failure(self):
        self.source.write_text("int value;\n")
        with self.assertRaises(FileNotFoundError):
            compile_unit(str(self.source), [str(self.root / "missing-emcc")], self.output)


if __name__ == "__main__":
    unittest.main()
