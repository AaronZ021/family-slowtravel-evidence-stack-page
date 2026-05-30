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
td.level { width:110px; font-weight:700; }
td.dimension { width:150px; font-weight:700; }
td.area { width:150px; font-weight:700; }
a { color:var(--accent); text-decoration:none; }
a:hover { text-decoration:underline; }
.callout { background:#fff7ed; border:1px solid #fed7aa; padding:12px 18px; border-radius:8px; margin:16px 0; }
.toc { display:flex; flex-wrap:wrap; gap:8px; margin:16px 0 22px; }
.toc a { display:inline-flex; padding:6px 10px; border-radius:8px; border:1px solid var(--border); background:#fff; font-size:13px; font-weight:650; }
.source-badge { display:inline-flex; align-items:center; min-height:24px; padding:2px 7px; border-radius:6px; background:#eef2ff; color:#3730a3; text-decoration:none; font-size:12px; font-weight:650; margin:2px 4px 2px 0; white-space:nowrap; }
.source-badge:hover { outline:2px solid #818cf8; outline-offset:1px; text-decoration:none; }
.badges { margin-top:6px; display:flex; flex-wrap:wrap; gap:4px; }
.compact p { margin:0 0 8px; }
.wide-table { overflow-x:auto; margin:16px 0; }
.wide-table table { min-width:1120px; margin:0; }
.matrix-table table { min-width:1500px; }
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


def optional_csv(path):
    return read_csv(path) if path.exists() else []


def render_spatial_framework(sources, used):
    rows = optional_csv(ROOT / "reports/spatial_dimension_framework.csv")
    if not rows:
        return ""
    out = [
        '<h2 id="spatial-framework">空间评估口径：哪些看城市，哪些看片区</h2>',
        '<div class="callout">判断规则：法律、制度、季节和城市级医疗网络先按城市看；每天反复发生、并且 1km/5km 半径会改变体验的事项，必须按候选片区看。社区反馈不单独替代事实，只贴回对应维度解释真实摩擦。</div>',
        '<div class="wide-table"><table><thead><tr><th>维度</th><th>主评估层级</th><th>城市级要回答的问题</th><th>片区级要回答的问题</th><th>为什么这样拆</th><th>数据源口径</th><th>页面处理</th></tr></thead><tbody>',
    ]
    for r in rows:
        out.append("<tr>")
        out.append(f"<td class=\"dimension\">{esc(r['dimension'])}</td>")
        out.append(f"<td class=\"level\">{esc(r['primary_level'])}</td>")
        out.append(f"<td>{esc(r['city_level_question'])}</td>")
        out.append(f"<td>{esc(r['area_level_question'])}</td>")
        out.append(f"<td>{esc(r['why'])}</td>")
        out.append(f"<td>{esc(r['data_sources'])}{badges(r['source_ids'], sources, used)}</td>")
        out.append(f"<td>{esc(r['page_action'])}</td>")
        out.append("</tr>")
    out.append("</tbody></table></div>")
    return "".join(out)


def render_area_assessment(sources, used):
    rows = optional_csv(ROOT / "reports/area_life_radius_assessment.csv")
    if not rows:
        return ""
    out = [
        '<h2 id="area-radius">候选片区生活半径横向比较</h2>',
        '<p class="page-sub">这张表只处理片区级问题：住在这个片区附近，四口之家每天是否能低摩擦完成儿童活动、买菜药房洗衣、医疗到达和出行。城市级签证、烟季、整体安全不在这里重复判断。</p>',
        '<div class="wide-table"><table><thead><tr><th>城市</th><th>片区</th><th>片区角色</th><th>1km 事实</th><th>5km 事实</th><th>住房含义</th><th>儿童活动含义</th><th>室内 fallback</th><th>医疗/日常服务</th><th>交通含义</th><th>当前可读出的意思</th><th>缺口 / 下一步</th></tr></thead><tbody>',
    ]
    for r in rows:
        out.append("<tr>")
        out.append(f"<td>{esc(r['city'])}</td>")
        out.append(f"<td class=\"area\">{esc(r['area'])}</td>")
        out.append(f"<td>{esc(r['area_role'])}</td>")
        out.append(f"<td>{esc(r['one_km_fact'])}</td>")
        out.append(f"<td>{esc(r['five_km_fact'])}</td>")
        out.append(f"<td>{esc(r['housing_message'])}</td>")
        out.append(f"<td>{esc(r['child_activity_message'])}</td>")
        out.append(f"<td>{esc(r['indoor_fallback_message'])}</td>")
        out.append(f"<td>{esc(r['healthcare_daily_services_message'])}</td>")
        out.append(f"<td>{esc(r['mobility_message'])}</td>")
        out.append(f"<td><div class=\"compact\"><p>{esc(r['main_interpretation'])}</p><div class=\"meta-row\"><span class=\"meta-pill\">置信度：{esc(r['confidence'])}</span></div>{badges(r['evidence_ids'], sources, used)}</div></td>")
        out.append(f"<td><div class=\"cell-label\">缺口</div><p>{esc(r['gaps'])}</p><div class=\"cell-label\">下一步</div><p>{esc(r['next_verification'])}</p></td>")
        out.append("</tr>")
    out.append("</tbody></table></div>")
    return "".join(out)


def render_area_function_matrix(sources, used):
    rows = optional_csv(ROOT / "reports/area_function_matrix.csv")
    if not rows:
        return ""
    area_headers = [
        ("lisbon_campo", "里斯本 · Campo"),
        ("lisbon_estrela", "里斯本 · Estrela/Lapa"),
        ("lisbon_parque", "里斯本 · Parque"),
        ("lisbon_belem", "里斯本 · Belém/Restelo"),
        ("cm_nimman", "清迈 · Nimman/Santitham"),
        ("cm_oldcity", "清迈 · Old City edge"),
        ("cm_hangdong", "清迈 · Hang Dong"),
        ("cm_sansai", "清迈 · San Sai"),
    ]
    out = [
        '<h2 id="area-function-matrix">片区 x 生活功能矩阵</h2>',
        '<p class="page-sub">这张表按同一个生活功能横向比较 8 个片区。它不是城市总评分，而是回答：如果只看这个功能，哪些片区的证据更强，哪些片区缺口更大。</p>',
        '<div class="wide-table matrix-table"><table><thead><tr><th>生活功能</th>',
    ]
    for _, label in area_headers:
        out.append(f"<th>{esc(label)}</th>")
    out.append("<th>证据 / 缺口</th></tr></thead><tbody>")
    for r in rows:
        out.append("<tr>")
        out.append(f"<td class=\"dimension\">{esc(r['function'])}</td>")
        for key, _ in area_headers:
            out.append(f"<td>{esc(r[key])}</td>")
        out.append(f"<td><div class=\"meta-row\"><span class=\"meta-pill\">置信度：{esc(r['confidence'])}</span></div>{badges(r['evidence_ids'], sources, used)}<div class=\"cell-label\">缺口</div><p>{esc(r['gap'])}</p></td>")
        out.append("</tr>")
    out.append("</tbody></table></div>")
    return "".join(out)


def main():
    sources = source_map()
    rows = read_csv(ROOT / "reports/indicator_evidence_stack.csv")
    by_layer = {}
    for r in rows:
        by_layer.setdefault(r["layer"], {}).setdefault(r["dimension"], {})[r["city"]] = r
    used = set()
    body = [
        '<h1 class="page-title">指标证据栈</h1>',
        '<p class="page-sub">本页先拆清楚空间口径：哪些维度只能按城市整体判断，哪些必须落到 Campo、Estrela、Nimman、Hang Dong 等候选片区。后面的证据栈只作为下钻材料。</p>',
        '<nav class="toc"><a href="#spatial-framework">空间评估口径</a><a href="#area-function-matrix">片区功能矩阵</a><a href="#area-radius">片区生活半径</a><a href="#evidence-stack">维度证据栈</a><a href="#sources">来源索引</a></nav>',
        '<div class="callout"><strong>读法</strong>：这里不做城市总评。城市级维度回答“能不能去、什么季节有硬约束”；片区级维度回答“住在哪里，日常是否真的跑得起来”。</div>',
    ]
    body.append(render_spatial_framework(sources, used))
    body.append(render_area_function_matrix(sources, used))
    body.append(render_area_assessment(sources, used))
    body.append('<h2 id="evidence-stack">维度证据栈</h2>')
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
    body.append('<h2 id="sources">本页来源索引</h2>')
    body.append(source_cards(used, sources))
    html_text = f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>指标证据栈 · 家庭慢旅研究</title><style>{CSS}</style></head><body><header><div class="inner"><h1>里斯本 vs 清迈 · 指标证据栈</h1></div></header><main>{''.join(body)}</main><footer>独立页面 · source IDs 对应 data/sources/sources.csv</footer></body></html>"""
    (DOCS / "index.html").write_text(html_text, encoding="utf-8")
    (DOCS / ".nojekyll").write_text("", encoding="utf-8")


if __name__ == "__main__":
    main()
