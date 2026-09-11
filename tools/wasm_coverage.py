#!/usr/bin/env python3
"""Measure compile-only wasm32 coverage; source failures are report findings."""

import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import shlex
import subprocess


EMSCRIPTEN_VERSION = "4.0.15"
AURORA_REVISION = "e6a6f02ace4146e8a2f648d5c274dbb7dd89665c"
FLAGS = ["-std=gnu99", "-O0", "-DTARGET_PC", "-Dbool=int", "-fno-color-diagnostics"]
WASM_HEADER = b"\x00asm\x01\x00\x00\x00"


def git(*args):
    return subprocess.check_output(["git", *args], text=True).strip()


def compile_unit(source, command, output):
    key = Path(source).name if Path(source).is_absolute() else source
    obj = output / "objects" / Path(key).with_suffix(".o")
    log = output / "logs" / Path(key).with_suffix(".txt")
    obj.parent.mkdir(parents=True, exist_ok=True)
    log.parent.mkdir(parents=True, exist_ok=True)
    obj.unlink(missing_ok=True)
    invocation = [*command, "-c", source, "-o", str(obj)]
    result = subprocess.run(invocation, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    log.write_bytes(result.stdout)
    if result.returncode < 0:
        raise RuntimeError(f"Compiler terminated by signal for {source}")
    if result.returncode == 0:
        with obj.open("rb") as artifact:
            if artifact.read(8) != WASM_HEADER:
                raise RuntimeError(f"Compiler did not produce a Wasm object for {source}")
    return {
        "file": source,
        "status": "passed" if result.returncode == 0 else "failed",
        "exit_code": result.returncode,
        "command": invocation,
        "log": str(log.relative_to(output)),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--aurora", type=Path, required=True)
    parser.add_argument("--emcc", default="emcc")
    parser.add_argument("--output", type=Path, default=Path("build/wasm-coverage"))
    parser.add_argument("--jobs", type=int, default=min(os.cpu_count() or 1, 8))
    args = parser.parse_args()
    if args.jobs < 1:
        parser.error("--jobs must be positive")

    os.chdir(Path(__file__).resolve().parent.parent)
    output = args.output
    output.mkdir(parents=True, exist_ok=True)
    # An interrupted rerun must not leave an old summary looking current.
    for name in ("report.json", "summary.md"):
        (output / name).unlink(missing_ok=True)

    aurora = args.aurora.resolve()
    if git("-C", str(aurora), "rev-parse", "HEAD") != AURORA_REVISION:
        parser.error(f"Aurora must be at {AURORA_REVISION}")
    if git("-C", str(aurora), "status", "--porcelain", "--untracked-files=all"):
        parser.error("Aurora checkout must be clean")
    compiler = subprocess.check_output([args.emcc, "--version"], text=True)
    if EMSCRIPTEN_VERSION not in compiler.splitlines()[0].split():
        parser.error(f"Emscripten must be {EMSCRIPTEN_VERSION}")

    sources = sorted(
        path for path in git("ls-files", "src/melee", "src/sysdolphin").splitlines()
        if path.endswith(".c")
    )
    if not sources:
        parser.error("No tracked C files found in the coverage scope")
    command = [args.emcc, *FLAGS, "-I", str(aurora / "include"), "-I", "src"]
    probe = output / "probe.c"
    probe.write_text(
        "#include <stdint.h>\n#include <stdlib.h>\n#include <dolphin/types.h>\n"
        "#if !defined(__wasm32__)\n#error Expected wasm32\n#endif\n"
        "typedef char pointer_width[sizeof(void *) == 4 ? 1 : -1];\n"
        "int wasm_coverage_probe(void) { return sizeof(u32); }\n"
    )
    # Warm the SDK cache once and distinguish broken setup from source failures.
    probe_result = compile_unit(str(probe), command, output)
    if probe_result["status"] != "passed":
        raise RuntimeError(f"Toolchain/header probe failed: {probe_result['log']}")

    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        units = list(pool.map(lambda source: compile_unit(source, command, output), sources))
    passed = sum(unit["status"] == "passed" for unit in units)
    report = {
        "schema_version": 1,
        "revision": git("rev-parse", "HEAD"),
        "dirty": bool(git("status", "--porcelain", "--untracked-files=all")),
        "target": "wasm32-unknown-emscripten",
        "compiler": compiler.strip(),
        "aurora_revision": AURORA_REVISION,
        "scope": ["src/melee/**/*.c", "src/sysdolphin/**/*.c"],
        "command_prefix": command,
        "total": len(units),
        "passed": passed,
        "failed": len(units) - passed,
        "units": units,
    }
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    summary = [
        "# Wasm compilation coverage",
        "",
        f"**{passed}/{len(units)} files compile ({passed / len(units):.2%}).**",
        "",
        f"Revision: `{report['revision']}`; dirty checkout: `{report['dirty']}`.",
        f"Emscripten: `{EMSCRIPTEN_VERSION}`; Aurora: `{AURORA_REVISION}`.",
        "",
        "Scope: all tracked C files in `src/melee` and `src/sysdolphin`; no exclusions.",
        "Flags: `" + shlex.join(FLAGS) + "` (plus Aurora and project include paths).",
        "",
        "Compile-only evidence for the TARGET_PC configuration. No linking, execution,",
        "behavioral equivalence, or GameCube matching is established by this report.",
        "Existing conditional compilation and inline implementations in headers still apply.",
        "Source failures are findings, not a failed coverage job. No regression ratchet yet.",
        "",
        "Download the artifact for per-file diagnostics and exact commands.",
        "",
        "| File | Result | Diagnostics |",
        "| --- | --- | --- |",
    ]
    summary.extend(
        f"| `{unit['file']}` | {unit['status']} | [log]({unit['log']}) |"
        for unit in units
    )
    (output / "summary.md").write_text("\n".join(summary) + "\n")
    print(summary[2])


if __name__ == "__main__":
    main()
