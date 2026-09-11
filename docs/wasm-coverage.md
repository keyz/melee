# Experimental Wasm compilation coverage

This fork measures how many shared-source translation units compile to wasm32.
It is a compile-only portability experiment, not a browser port or an upstream
support commitment. It does not change game source or the GameCube build.

## Measurement

- Denominator: every tracked `.c` file under `src/melee` and `src/sysdolphin`.
  There are no per-file exclusions, including the native build's excluded files.
- Numerator: files for which Emscripten exits successfully and emits a Wasm object.
- Configuration: Emscripten 4.0.15, GNU C99, `-O0`, `TARGET_PC`, `bool=int`,
  and Aurora headers at `e6a6f02ace4146e8a2f648d5c274dbb7dd89665c`.
  The header revision and defines follow the existing native compilation check.
- Compiler-default diagnostic severity applies; warnings do not fail a file.
  Full diagnostics are retained for successful files as well as failures.
- Existing conditional compilation and header implementations apply. A passing
  file is evidence for this configuration, not proof that every original body
  was compiled. No extra stubs or game-source edits are introduced by this check.
- SDK, Runtime, and MSL implementation files are outside this initial scope.
  Their required replacements and unresolved symbols are not measured here.

The JSON report records the revision, dirty state, toolchain, inventory, result,
exit code, exact command, and diagnostic log for each file. The Markdown report
provides a summary and per-file table. Compare inventories and configurations
alongside percentages: changing either changes the measurement.

## Run in Linux

Run these commands from the repository root inside a Linux development container
with Git, Python 3, and xz-utils available. All compiler dependencies stay in Linux.

```sh
git clone --depth 1 --branch 4.0.15 https://github.com/emscripten-core/emsdk.git /tmp/melee-emsdk
/tmp/melee-emsdk/emsdk install 4.0.15
/tmp/melee-emsdk/emsdk activate 4.0.15
. /tmp/melee-emsdk/emsdk_env.sh
git clone https://github.com/r-burns/aurora.git /tmp/melee-wasm-aurora
git -C /tmp/melee-wasm-aurora checkout e6a6f02ace4146e8a2f648d5c274dbb7dd89665c
python3 -m unittest discover -s tools/tests -p 'test_wasm_coverage.py'
python3 tools/wasm_coverage.py --aurora /tmp/melee-wasm-aurora
```

Results are written to `build/wasm-coverage/`. Use `--jobs N` to control parallel
compilation and `--output PATH` to keep separate scans. Commands use repository-
relative source paths and must be replayed from the repository root.

## CI and interpretation

The fork's `Wasm compilation coverage` workflow runs on pushes to
`codex/wasm-compilation-coverage` and by manual dispatch. It publishes a job
summary and a downloadable JSON/Markdown/log artifact. Download and unpack the
artifact to follow the summary's relative diagnostic links.

Source compilation failures are baseline findings and do not fail the reporting
job. A missing compiler, wrong dependency revision, failed setup probe, or invalid
successful output fails the runner. This prototype has no regression ratchet.
100% would mean compilation coverage only: no linking, execution, asset loading,
or behavioral equivalence. Future source fixes must independently preserve the
matching GameCube build.
