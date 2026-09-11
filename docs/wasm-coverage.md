# Experimental Wasm compilation coverage

This fork compiles every tracked `.c` file under `src/melee` and
`src/sysdolphin` to wasm32. Coverage is successful compilations / total files;
there are no file exclusions. This is a compilation baseline, not a browser port.

CI pins Emscripten 4.0.15 and Aurora headers at
`e6a6f02ace4146e8a2f648d5c274dbb7dd89665c`. The runner uses GNU C99, `-O0`,
`TARGET_PC`, and `bool=int`, following the existing native check's defines.
Compiler-default warning severity applies. Existing conditional compilation and
header implementations still apply; this does not measure every original body.

Run from the repository root inside Linux with Emscripten activated and the
pinned Aurora checkout available:

```sh
AURORA_SRC=/path/to/aurora python3 tools/wasm_coverage.py
```

`build/wasm-coverage/` contains a Markdown table, JSON results with revision and
toolchain metadata, and per-file commands and diagnostics. Object files are
temporary. To replay a logged command, choose an existing output directory.

The workflow runs on pushes to `codex/wasm-compilation-coverage` and manual
dispatch. Download its artifact to follow the table's relative diagnostic links.
Source failures are findings, so a successful reporting job can have low coverage.
A setup probe must compile before scanning files. There is no regression ratchet.

SDK/Runtime/MSL implementation files, linking, asset loading, and execution are
outside this measurement. No game source is changed. Future source fixes must
independently preserve GameCube matching. Compare source inventories and compiler
configurations alongside coverage percentages.
