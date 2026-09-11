"""Render coverage from a successful native build's installed source manifest.

Run from the repository root, after `nix build .#melee-gcc-native`:
    python3 tools/native_treemap.py result/share/melee/native-sources.txt > native-treemap.html
"""

import subprocess
import sys
from pathlib import Path

import plotly.graph_objects as go

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
figure = go.Figure(trace)
figure.update_layout(
    template="plotly_dark",
    title=dict(
        text=f"Native compilation: {len(compiled)} / {len(files)} files ({len(compiled) / len(files):.2%})",
        subtitle=dict(text=(
            f"32-bit Linux GCC · commit {commit[:12]}<br>"
            "Green: compiled · Gray: excluded · Equal-area C file tiles · Click directories to zoom.<br>"
            "Scope: src/melee and src/sysdolphin. Compilation does not establish linking or runtime correctness."
        )),
    ),
    margin=dict(t=140, l=10, r=10, b=10),
)
figure.write_html(sys.stdout, config={"displayModeBar": False})
