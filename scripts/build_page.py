#!/usr/bin/env python3
import csv
import html
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
DOCS.mkdir(exist_ok=True)


def read_csv(path):
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def esc(s):
    return html.escape(s or "", quote=True)


CSS = """
:root { --bg:#fafaf8; --fg:#1a1a1a; --muted:#666; --accent:#b85450; --border:#e5e3dd; --code-bg:#f3f1ec; --stripe:#f7f5f0; }
* { box-sizing:border-box; }
html,body { margin:0; padding:0; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif; color:var(--fg); background:var(--bg); line-height:1.65; }
header { background:rgba(255,255,255,.9); border-bottom:1px solid var(--border); padding:14px 24px; position:sticky; top:0; z-index:20; }
header .inner, main, footer { max-width:1280px; margin:0 auto; }
header h1 { font-size:17px; margin:0; font-weight:650; }
main { padding:32px 24px 80px; }
.page-title { font-size:32px; margin:0 0 8px; }
.page-sub { color:var(--muted); margin:0 0 24px; }
h2 { font-size:22px; margin:34px 0 12px; border-bottom:1px solid var(--border); padding-bottom:6px; }
table { border-collapse:collapse; width:100%; margin:16px 0; font-size:14px; background:#fff; border:1px solid var(--border); }
th,td { padding:12px 14px; text-align:left; vertical-align:top; border-bottom:1px solid var(--border); }
th { background:var(--code-bg); font-size:13px; font-weight:650; }
tr:nth-child(even) td { background:var(--stripe); }
a { color:var(--accent); text-decoration:none; }
a:hover { text-decoration:underline; }
.callout { background:#fff7ed; border:1px solid #fed7aa; padding:12px 18px; border-radius:8px; margin:16px 0; }
.source-badge { display:inline-flex; align-items:center; min-height:24px; padding:2px 7px; border-radius:6px; background:#eef2ff; color:#3730a3; text-decoration:none; font-size:12px; font-weight:650; margin:2px 4px 2px 0; white-space:nowrap; }
.source-badge:hover { outline:2px solid #818cf8; outline-offset:1px; text-decoration:none; }
.badges { margin-top:6px; display:flex; flex-wrap:wrap; gap:4px; }
.cell-label { margin:10px 0 4px; font-size:12px; font-weight:750; color:var(--muted); }
.cell-block p { margin:0 0 8px; }
.meta-row { display:flex; flex-wrap:wrap; gap:8px; margin:8px 0 10px; }
.meta-pill { display:inline-flex; min-height:24px; align-items:center; padding:2px 8px; border-radius:6px; background:var(--code-bg); border:1px solid var(--border); font-size:12px; font-weight:650; }
.evidence-tier { border-left:4px solid var(--border); padding:8px 0 2px 10px; margin:10px 0; }
.official-tier { border-left-color:#2563eb; }
.platform-tier { border-left-color:#65a30d; }
.community-tier { border-left-color:#d97706; }
.source-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(280px,1fr)); gap:12px; margin-top:16px; }
.source-card { background:#fff; border:1px solid var(--border); border-radius:8px; padding:12px; font-size:13px; }
.source-card h3 { margin:6px 0; font-size:15px; }
.source-card dl { margin:0; display:grid; gap:4px; }
.source-card dl div { display:grid; grid-template-columns:72px 1fr; gap:8px; }
.source-card dt { color:var(--muted); }
.source-card dd { margin:0; overflow-wrap:anywhere; }
footer { padding:0 24px 32px; color:var(--muted); font-size:13px; }
"""


def source_map():
    return {r["source_id"]: r for r in read_csv(ROOT / "data/sources/sources.csv")}


def expand_token(token, sources):
    if "-" not in token:
        return [token]
    left, right = token.split("-", 1)
    m = re.match(r"^(.*?)(\d+)$", left)
    if not m:
        return [token]
    prefix, start_s = m.groups()
    end_s = right[len(prefix):] if right.startswith(prefix) else right
    if not end_s.isdigit():
        return [token]
    width = max(len(start_s), len(end_s))
    expanded = [f"{prefix}{i:0{width}d}" for i in range(int(start_s), int(end_s) + 1)]
    return expanded if all(sid in sources for sid in expanded) else [token]


def badges(ids, sources, used):
    out = []
    for raw in (ids or "").replace(",", ";").split(";"):
        token = raw.strip()
        if not token:
            continue
        for sid in expand_token(token, sources):
            used.add(sid)
            title = sources.get(sid, {}).get("title", "")
            out.append(f'<a class="source-badge" href="#src-{esc(sid)}" title="{esc(title)}">{esc(sid)}</a>')
    return '<div class="badges">' + " ".join(out) + "</div>" if out else ""


def cell(row, sources, used):
    return f"""
<div class="cell-block">
  <div class="cell-label">当前维度评估</div>
  <p>{esc(row['current_dimension_assessment'])}</p>
  <div class="meta-row"><span class="meta-pill">证据充分性：{esc(row['evidence_sufficiency'])}</span><span class="meta-pill">置信度：{esc(row['confidence'])}</span></div>
  <div class="evidence-tier official-tier"><div class="cell-label">官方/统计证据</div><p>{esc(row['official_stat_evidence'])}</p>{badges(row['official_source_ids'], sources, used)}</div>
  <div class="evidence-tier platform-tier"><div class="cell-label">平台/地图证据</div><p>{esc(row['platform_map_evidence'])}</p>{badges(row['platform_source_ids'], sources, used)}</div>
  <div class="evidence-tier community-tier"><div class="cell-label">社区反馈 overlay</div><p>{esc(row['community_overlay'])}</p>{badges(row['community_source_ids'], sources, used)}</div>
  <div class="cell-label">缺口</div><p>{esc(row['gaps'])}</p>
  <div class="cell-label">下一步补数</div><p>{esc(row['next_data_to_collect'])}</p>
</div>
"""


def source_cards(used, sources):
    cards = []
    for sid in sorted(used):
        r = sources.get(sid)
        if not r:
            continue
        cards.append(f"""
<article class="source-card" id="src-{esc(sid)}">
  <a class="source-badge" href="{esc(r['url'])}" target="_blank" rel="noopener">{esc(sid)}</a>
  <h3><a href="{esc(r['url'])}" target="_blank" rel="noopener">{esc(r['title'])}</a></h3>
  <dl>
    <div><dt>类型</dt><dd>{esc(r['source_type'])}</dd></div>
    <div><dt>城市</dt><dd>{esc(r['city'])}</dd></div>
    <div><dt>维度</dt><dd>{esc(r['dimension'])}</dd></div>
    <div><dt>访问</dt><dd>{esc(r['accessed_date'])}</dd></div>
    <div><dt>URL</dt><dd><a href="{esc(r['url'])}" target="_blank" rel="noopener">{esc(r['url'])}</a></dd></div>
  </dl>
</article>""")
    return '<div class="source-grid">' + "\n".join(cards) + "</div>"


def main():
    sources = source_map()
    rows = read_csv(ROOT / "reports/indicator_evidence_stack.csv")
    by_layer = {}
    for r in rows:
        by_layer.setdefault(r["layer"], {}).setdefault(r["dimension"], {})[r["city"]] = r
    used = set()
    body = [
        '<h1 class="page-title">指标证据栈</h1>',
        '<p class="page-sub">每个小格子先写该城市在该维度的事实含义，再列官方/统计、平台/地图、社区反馈三类证据。证据 ID 是支撑，不替代文字判断。</p>',
        '<div class="callout"><strong>读法</strong>：这里不做城市总评。每行只处理一个维度；每个城市的小格子说明当前证据能支撑什么、哪里不足、下一步补什么。</div>',
    ]
    for layer, dims in by_layer.items():
        body.append(f"<h2>{esc(layer)}</h2>")
        body.append("<table><thead><tr><th>维度</th><th>里斯本</th><th>清迈</th></tr></thead><tbody>")
        for dim, cities in dims.items():
            body.append("<tr>")
            body.append(f"<td><strong>{esc(dim)}</strong></td>")
            body.append(f"<td>{cell(cities['里斯本'], sources, used) if '里斯本' in cities else ''}</td>")
            body.append(f"<td>{cell(cities['清迈'], sources, used) if '清迈' in cities else ''}</td>")
            body.append("</tr>")
        body.append("</tbody></table>")
    body.append("<h2>本页来源索引</h2>")
    body.append(source_cards(used, sources))
    html_text = f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>指标证据栈 · 家庭慢旅研究</title><style>{CSS}</style></head><body><header><div class="inner"><h1>里斯本 vs 清迈 · 指标证据栈</h1></div></header><main>{''.join(body)}</main><footer>独立页面 · source IDs 对应 data/sources/sources.csv</footer></body></html>"""
    (DOCS / "index.html").write_text(html_text, encoding="utf-8")
    (DOCS / ".nojekyll").write_text("", encoding="utf-8")


if __name__ == "__main__":
    main()
