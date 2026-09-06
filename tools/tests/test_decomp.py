"""Run with python3 -m unittest discover -s tools/tests."""

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from tools import decomp


class DecompWriteTest(unittest.TestCase):
    def test_write_preserves_c_escapes(self):
        for literal in (r"line\n", r"\x41", r"\1", r"path\\file"):
            with self.subTest(literal=literal), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                source = root / "unit.c"
                (root / "unit.s").touch()
                before = "/* before */\n/// #target\n/* after */\n/// #target\n"
                output = 'void target(void) { puts("' + literal + '"); }\n'
                source.write_text(before)

                with (
                    patch.object(
                        sys,
                        "argv",
                        [
                            "decomp.py",
                            "--no-context",
                            "--no-copy",
                            "--no-print",
                            "--write",
                            "target",
                        ],
                    ),
                    patch.multiple(
                        decomp,
                        ASM_ROOT=root,
                        SRC_ROOT=root,
                        find_obj=Mock(return_value=Path("unit.o")),
                        run_cmd=Mock(return_value=output),
                    ),
                ):
                    decomp.main()

                self.assertEqual(
                    source.read_text(),
                    "/* before */\n" + output + "/* after */\n/// #target\n",
                )
