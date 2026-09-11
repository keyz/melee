#!/usr/bin/env python3
"""Compile every tracked game/engine C file to wasm32 and report coverage."""

from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import shlex
import subprocess
import tempfile


def git(*args):
    return subprocess.check_output(["git", *args], text=True).strip()


def main():
    output = Path("build/wasm-coverage")
    output.mkdir(parents=True, exist_ok=True)
    for name in ("report.json", "summary.md"):
        (output / name).unlink(missing_ok=True)

    aurora = Path(os.environ["AURORA_SRC"])
    command = [
        "emcc", "-std=gnu99", "-O0", "-DTARGET_PC", "-Dbool=int",
        "-fno-color-diagnostics", "-I", str(aurora / "include"), "-I", "src",
    ]
    report = {
        "revision": git("rev-parse", "HEAD"),
        "dirty": bool(git("status", "--porcelain")),
        "compiler": subprocess.check_output(["emcc", "--version"], text=True).strip(),
        "aurora_revision": git("-C", str(aurora), "rev-parse", "HEAD"),
        "command_prefix": command,
    }
    sources = sorted(
        path for path in git("ls-files", "src/melee", "src/sysdolphin").splitlines()
        if path.endswith(".c")
    )
    if not sources:
        raise RuntimeError("No tracked C files found; run from the repository root")

    with tempfile.TemporaryDirectory() as temporary:
        # Check setup and initialize the SDK cache before parallel compilation.
        subprocess.run(
            [*command, "-x", "c", "-c", "-", "-o", f"{temporary}/probe.o"],
            input=(
                "#include <stdlib.h>\n#include <dolphin/types.h>\n"
                "#ifndef __wasm32__\n#error Expected wasm32\n#endif\n"
            ),
            text=True, check=True,
        )

        def compile_file(source):
            obj = Path(temporary) / Path(source).with_suffix(".o")
            log = Path("logs") / Path(source).with_suffix(".txt")
            obj.parent.mkdir(parents=True, exist_ok=True)
            (output / log).parent.mkdir(parents=True, exist_ok=True)
            invocation = [*command, "-c", source, "-o", str(obj)]
            with (output / log).open("w") as stream:
                stream.write(shlex.join(invocation) + "\n\n")
                stream.flush()
                result = subprocess.run(invocation, stdout=stream, stderr=subprocess.STDOUT)
            return {"file": source, "exit_code": result.returncode, "log": str(log)}

        with ThreadPoolExecutor(max_workers=8) as pool:
            units = list(pool.map(compile_file, sources))

    passed = sum(unit["exit_code"] == 0 for unit in units)
    report.update(total=len(units), passed=passed, units=units)
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    headline = f"{passed}/{len(units)} files compile ({passed / len(units):.2%})."
    summary = f"""# Wasm compilation coverage

{headline}

All tracked C files in `src/melee` and `src/sysdolphin`; no file exclusions.
Compile-only TARGET_PC configuration. Source failures are findings;
linking and execution are not tested.

| File | Result | Diagnostics |
| --- | --- | --- |
"""
    for unit in units:
        status = "passed" if unit["exit_code"] == 0 else "failed"
        summary += f"| `{unit['file']}` | {status} | [log]({unit['log']}) |\n"
    (output / "summary.md").write_text(summary)
    print(headline)


if __name__ == "__main__":
    main()
