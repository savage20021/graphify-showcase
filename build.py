"""Build the public showcase map: megamap filtered to public GitHub repos, re-rendered."""
import json, subprocess, sys
from collections import defaultdict
from pathlib import Path
import networkx as nx
from graphify.exporters.html import to_html

HERE = Path(__file__).parent
SRC = HERE.parent / "graphify-maps" / "megamap" / "graph.json"
PUBLIC = {"agentdeck", "asciicam", "beamlab", "cardealfinder", "fileconverter", "goldtracker", "hikari",
          "metastrip", "minesweeper-solver", "profile-cards", "savage20021", "trusslab", "wordle-solver"}
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

g = json.loads(SRC.read_text(encoding="utf-8"))
keep = {n["id"] for n in g["nodes"] if n.get("repo") in PUBLIC}
g["nodes"] = [n for n in g["nodes"] if n["id"] in keep]
g["links"] = [e for e in g["links"] if e["source"] in keep and e["target"] in keep]
g["hyperedges"] = [h for h in g.get("hyperedges", []) if all(n in keep for n in h.get("nodes", []))]
g["graph"]["hyperedges"] = [h for h in g["graph"].get("hyperedges", []) if all(n in keep for n in h.get("nodes", []))]
(HERE / "graph.json").write_text(json.dumps(g, ensure_ascii=False), encoding="utf-8")

G = nx.node_link_graph(g, edges="links")
communities, labels = defaultdict(list), {}
for nid, d in G.nodes(data=True):
    c = d.get("community", 0)
    communities[c].append(nid)
    labels.setdefault(c, d.get("community_name") or f"Community {c}")
ok = to_html(G, dict(communities), str(HERE / "graph.html"), community_labels=labels, node_limit=10_000)
assert ok and G.number_of_nodes() > 2000, (ok, G.number_of_nodes())
print(f"{G.number_of_nodes()} nodes, {G.number_of_edges()} edges, {len(communities)} communities, repos={len(PUBLIC)}")

if "--png" in sys.argv:
    url = "file:///" + str(HERE / "graph.html").replace("\\", "/").replace(" ", "%20")
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--window-size=2200,1300",
                    "--virtual-time-budget=20000", f"--screenshot={HERE / 'map.png'}", url], capture_output=True, timeout=120)
    print("map.png", (HERE / "map.png").stat().st_size)
