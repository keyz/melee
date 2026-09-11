"""Render coverage from a successful native build's installed source manifest.

Run from the repository root, after `nix build .#melee-gcc-native`:
    python3 tools/native_treemap.py result/share/melee/native-sources.txt > native-treemap.html
"""

import json
import subprocess
import sys
from pathlib import Path

compiled = set(Path(sys.argv[1]).read_text().splitlines())
files = sorted(
    path.as_posix()
    for root in (Path("src/melee"), Path("src/sysdolphin"))
    for path in root.rglob("*.c")
)
assert compiled <= set(files), "Build manifest does not match this source tree"
commit = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
nodes = {}
for name in files:
    path = Path(name)
    nodes[name] = (1, "Compiled" if name in compiled else "Excluded")
    for parent in path.parents:
        if parent != Path("."):
            nodes.setdefault(parent.as_posix(), (0, "Directory"))

trace = {
    "type": "treemap",
    "ids": list(nodes),
    "labels": [Path(name).name for name in nodes],
    "parents": [str(Path(name).parent) if name != "src" else "" for name in nodes],
    "values": [value for value, status in nodes.values()],
    "customdata": [status for value, status in nodes.values()],
    "marker": {"colors": [
        {"Compiled": "#20a456", "Excluded": "#89919c", "Directory": "#253041"}[status]
        for value, status in nodes.values()
    ]},
    "hovertemplate": "%{id}<br>%{customdata}<extra></extra>",
    "textinfo": "label",
}
print(f"""<!DOCTYPE html>
<html lang="en">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Melee native compilation coverage</title>
<style>
body {{ margin: 24px; background: #151b24; color: #edf1f7; font: 16px system-ui; }}
h1 {{ font-size: 24px; }}
p {{ color: #b9c3d2; }}
#map {{ height: 75vh; }}
</style>
<h1>Native compilation: {len(compiled)} / {len(files)} files ({len(compiled) / len(files):.2%})</h1>
<p>32-bit Linux GCC · commit {commit[:12]}</p>
<p>Green: compiled · Gray: excluded · One equal-area tile per C file.<br>
Scope: src/melee and src/sysdolphin. Compilation does not establish linking or runtime correctness.</p>
<div id="map"></div>
<p>Click a directory to zoom; use the path bar to go back. Chart requires internet access.</p>
<script src="https://cdn.plot.ly/plotly-3.1.0.min.js"></script>
<script>
Plotly.newPlot('map', [{json.dumps(trace)}], {{
    margin: {{t: 0, l: 0, r: 0, b: 0}}, paper_bgcolor: '#151b24',
    font: {{color: '#edf1f7'}}
}}, {{responsive: true, displayModeBar: false}});
</script>
</html>""")
