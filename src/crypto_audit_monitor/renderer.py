from __future__ import annotations

import html
import json
from typing import Any


def _json_for_script(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True).replace(
        "</", "<\\/"
    )


def render_html(
    run_manifest: dict[str, Any],
    exceptions: list[dict[str, Any]],
    comparison: dict[str, Any],
    reviews: list[dict[str, Any]] | None = None,
    back_href: str | None = None,
) -> str:
    model = {
        "run": run_manifest,
        "exceptions": exceptions,
        "comparison": comparison,
        "reviews": reviews or [],
    }
    data = _json_for_script(model)
    run_id = html.escape(run_manifest["run_id"])
    back_link = (
        f'<a class="brand" href="{html.escape(back_href)}" data-case-link>'
        '<span aria-hidden="true">←</span> RiskFirewall</a>'
        if back_href
        else '<div class="brand">Crypto Audit Analytics Monitor</div>'
    )
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Commission Assurance | RiskFirewall</title>
<style>
:root {{
  --ink:#172033; --muted:#647084; --line:#d8dee8; --paper:#f6f8fb;
  --white:#fff; --blue:#2d5f91; --blue-bg:#eaf1f8; --green:#16713b;
  --green-bg:#e5f6eb; --amber:#8a5400; --amber-bg:#fff2c7;
  --red:#a12626; --red-bg:#fee7e7; --gray:#536174; --gray-bg:#edf0f4;
}}
* {{ box-sizing:border-box; }}
body {{ margin:0; background:var(--paper); color:var(--ink);
  font-family:Inter,Segoe UI,Arial,"Microsoft YaHei",sans-serif; }}
header {{ position:sticky; top:0; z-index:5; background:rgba(255,255,255,.96);
  border-bottom:1px solid var(--line); }}
.top {{ max-width:1240px; margin:auto; padding:18px 28px 12px;
  display:flex; align-items:center; gap:18px; flex-wrap:wrap; }}
.brand {{ font-size:20px; font-weight:800; white-space:nowrap; flex-shrink:0; }}
.case {{ padding-left:18px; border-left:1px solid var(--line); font-weight:700; white-space:nowrap; }}
.spacer {{ flex:1; }}
select {{ border:1px solid var(--line); border-radius:999px; padding:9px 34px 9px 14px;
  background:white; color:var(--ink); font-weight:650; }}
nav {{ max-width:1240px; margin:auto; padding:0 28px 14px; display:flex; gap:8px; flex-wrap:wrap; }}
nav a {{ color:var(--muted); text-decoration:none; padding:8px 10px; border-radius:8px; }}
nav a:hover {{ background:var(--blue-bg); color:var(--blue); }}
main {{ max-width:1240px; margin:auto; padding:34px 28px 72px; }}
.eyebrow {{ color:var(--blue); font-weight:800; letter-spacing:.08em; text-transform:uppercase; }}
h1 {{ max-width:980px; font-size:clamp(40px,7vw,82px); line-height:.98; letter-spacing:-.035em;
  margin:18px 0 24px; }}
h2 {{ font-size:32px; margin:58px 0 10px; letter-spacing:-.025em; }}
.lede {{ max-width:820px; font-size:21px; line-height:1.55; color:var(--muted); }}
.chips,.filters {{ display:flex; gap:10px; flex-wrap:wrap; margin:24px 0; }}
.chip,.filter {{ border:1px solid var(--line); border-radius:999px; padding:9px 14px;
  background:white; font-weight:750; color:var(--gray); }}
.chip.green {{ background:var(--green-bg); color:var(--green); border-color:#a9dfba; }}
.chip.amber {{ background:var(--amber-bg); color:var(--amber); border-color:#f0cc63; }}
.chip.red {{ background:var(--red-bg); color:var(--red); border-color:#f1b4b4; }}
.filter {{ cursor:pointer; }}
.filter.active {{ background:var(--blue); color:white; border-color:var(--blue); }}
.grid {{ display:grid; grid-template-columns:repeat(4,1fr); gap:14px; }}
.card {{ background:white; border:1px solid var(--line); border-radius:18px; padding:22px; }}
.metric strong {{ display:block; font-size:42px; margin-bottom:8px; }}
.metric span {{ color:var(--muted); }}
.gate-grid {{ display:grid; grid-template-columns:repeat(4,1fr); gap:10px; }}
.gate {{ background:var(--green-bg); color:var(--green); border:1px solid #a9dfba;
  border-radius:12px; padding:13px; font-weight:750; }}
.gate.harness {{ background:var(--blue-bg); color:var(--blue); border-color:#b8cce2; }}
.table-wrap {{ overflow:auto; background:white; border:1px solid var(--line); border-radius:18px; }}
table {{ width:100%; border-collapse:collapse; min-width:900px; }}
th,td {{ text-align:left; padding:14px 16px; border-bottom:1px solid var(--line); vertical-align:top; }}
th {{ color:var(--muted); font-size:13px; letter-spacing:.04em; text-transform:uppercase; }}
.badge {{ display:inline-block; border-radius:999px; padding:5px 9px; font-size:12px; font-weight:800; }}
.potential_exception {{ background:var(--amber-bg); color:var(--amber); }}
.expected_shared {{ background:var(--blue-bg); color:var(--blue); }}
.review-list {{ display:grid; gap:14px; }}
.review-card {{ background:white; border:1px solid var(--line); border-radius:18px; padding:20px; }}
.review-head {{ display:flex; justify-content:space-between; gap:14px; flex-wrap:wrap; margin-bottom:10px; }}
.review-meta {{ color:var(--muted); font-size:14px; }}
.review-rationale {{ line-height:1.55; margin:10px 0 0; }}
.review-correction {{ border-left:4px solid var(--blue); }}
.high {{ color:var(--red); }} .medium {{ color:var(--amber); }}
.note {{ border-left:4px solid var(--blue); background:var(--blue-bg);
  border-radius:0 14px 14px 0; padding:18px 20px; color:#244b72; line-height:1.55; }}
.boundary {{ background:var(--gray-bg); border:1px solid var(--line); border-radius:18px; padding:24px;
  display:grid; grid-template-columns:1fr 1fr; gap:20px; }}
.boundary ul {{ margin:8px 0 0; padding-left:20px; line-height:1.65; }}
code {{ font-family:"Cascadia Code",Consolas,monospace; font-size:.9em; }}
details {{ margin-top:6px; }} summary {{ cursor:pointer; color:var(--blue); }}
section[id] {{ scroll-margin-top:150px; }}
[data-lang="zh"] {{ display:none; }}
html.lang-zh [data-lang="en"] {{ display:none; }}
html.lang-zh [data-lang="zh"] {{ display:initial; }}
@media(max-width:850px) {{
  header {{ position:static; }}
  .grid,.gate-grid {{ grid-template-columns:1fr 1fr; }}
  .boundary {{ grid-template-columns:1fr; }}
  .case {{ width:100%; border-left:0; padding-left:0; white-space:normal; }}
  nav {{ flex-wrap:nowrap; overflow-x:auto; }}
  nav a {{ flex:0 0 auto; }}
  section[id] {{ scroll-margin-top:18px; }}
}}
@media(max-width:540px) {{ .grid,.gate-grid {{ grid-template-columns:1fr; }} main,.top,nav {{ padding-left:18px; padding-right:18px; }} }}
</style>
</head>
<body>
<header>
  <div class="top">
    {back_link}
    <div class="case"><span data-lang="en">Commission assurance</span><span data-lang="zh">佣金审计证据</span></div>
    <div class="spacer"></div>
    <label><span data-lang="en">Language</span><span data-lang="zh">语言</span>
      <select id="language"><option value="en">English</option><option value="zh">中文</option></select>
    </label>
  </div>
  <nav>
    <a href="#overview"><span data-lang="en">Overview</span><span data-lang="zh">概览</span></a>
    <a href="#exceptions"><span data-lang="en">Exceptions</span><span data-lang="zh">异常队列</span></a>
    <a href="#reviews"><span data-lang="en">Worked reviews</span><span data-lang="zh">人工复核示例</span></a>
    <a href="#sampling"><span data-lang="en">Population vs sample</span><span data-lang="zh">全量与抽样</span></a>
    <a href="#evidence"><span data-lang="en">Evidence boundary</span><span data-lang="zh">证据边界</span></a>
  </nav>
</header>
<main>
  <section id="overview">
    <div class="eyebrow"><span data-lang="en">Commission assurance · controlled synthetic case</span><span data-lang="zh">佣金审计证据 · 受控合成案例</span></div>
    <h1><span data-lang="en">Commission assurance: test the population, preserve the explanation.</span><span data-lang="zh">佣金审计证据：测试全量总体，保留解释责任。</span></h1>
    <p class="lede"><span data-lang="en">Deterministic SQL identifies signals in fabricated wallet and commission data. Every item stays tied to its rule, source rows and hash-bound snapshot; only a human may interpret it.</span><span data-lang="zh">确定性 SQL 在编造的钱包与佣金数据中识别信号。每一项都绑定规则、源数据行与哈希绑定的快照；含义只能由人工判断。</span></p>
    <div class="chips">
      <span class="chip green"><span data-lang="en">6 run gates passed</span><span data-lang="zh">6 项运行闸门通过</span></span>
      <span class="chip"><span data-lang="en">2 release tests separate</span><span data-lang="zh">另有 2 项发布测试</span></span>
      <span class="chip amber"><span data-lang="en">Human review required</span><span data-lang="zh">必须人工复核</span></span>
      <span class="chip red"><span data-lang="en">No fraud conclusion</span><span data-lang="zh">不作欺诈结论</span></span>
      <span class="chip green"><span data-lang="en">L1 candidate: deterministic recomputation</span><span data-lang="zh">L1 候选：确定性重算</span></span>
      <span class="chip"><span data-lang="en">G6-G7 release tests required; L2-L3 not achieved</span><span data-lang="zh">仍需 G6-G7 发布测试；尚未达到 L2-L3</span></span>
    </div>
    <div class="grid" id="metrics"></div>
    <h2><span data-lang="en">Integrity gates</span><span data-lang="zh">完整性闸门</span></h2>
    <div class="gate-grid" id="gates"></div>
  </section>

  <section id="exceptions">
    <h2><span data-lang="en">Exception queue</span><span data-lang="zh">异常队列</span></h2>
    <p class="lede"><span data-lang="en">A signal is an exception requiring explanation, not proof of misconduct.</span><span data-lang="zh">信号只代表需要解释的异常，不是行为不当的证明。</span></p>
    <div class="filters">
      <button class="filter active" data-filter="all" aria-pressed="true"><span data-lang="en">All review items</span><span data-lang="zh">全部复核项</span></button>
      <button class="filter" data-filter="potential_exception" aria-pressed="false"><span data-lang="en">Potential exceptions</span><span data-lang="zh">潜在异常</span></button>
      <button class="filter" data-filter="expected_shared" aria-pressed="false"><span data-lang="en">Expected shared</span><span data-lang="zh">预期共享</span></button>
    </div>
    <p id="filterCount" aria-live="polite" style="color:var(--muted)"></p>
    <div class="table-wrap"><table>
      <caption style="position:absolute;left:-10000px"><span data-lang="en">Evidence items requiring review</span><span data-lang="zh">需要复核的证据项</span></caption>
      <thead><tr>
        <th scope="col">ID</th>
        <th scope="col"><span data-lang="en">Rule</span><span data-lang="zh">规则</span></th>
        <th scope="col"><span data-lang="en">Route</span><span data-lang="zh">路由</span></th>
        <th scope="col"><span data-lang="en">Severity</span><span data-lang="zh">严重性</span></th>
        <th scope="col"><span data-lang="en">Context</span><span data-lang="zh">情境</span></th>
        <th scope="col"><span data-lang="en">Source rows</span><span data-lang="zh">源数据行</span></th>
      </tr></thead>
      <tbody id="exceptionRows"></tbody>
    </table></div>
  </section>

  <section id="reviews">
    <h2><span data-lang="en">Worked human reviews</span><span data-lang="zh">人工复核示例</span></h2>
    <p class="lede"><span data-lang="en">Three fabricated cases demonstrate a substantiated exception, a closed designed false positive, and an append-only correction. Reviewer identity is self-attested for this prototype.</span><span data-lang="zh">三个编造案例分别演示已确认控制异常、关闭的设计误报，以及只追加的更正记录。原型中的复核人身份仅为自我声明。</span></p>
    <div class="review-list" id="reviewRows"></div>
  </section>

  <section id="sampling">
    <h2><span data-lang="en">Full population vs bounded sample</span><span data-lang="zh">全量总体与有限抽样</span></h2>
    <div class="note"><span data-lang="en">Observed synthetic results only. Samples use the affiliate as the unit, fixed size and pre-committed seeds. No confidence, detection probability or real-world inference is claimed.</span><span data-lang="zh">仅报告合成数据中的观测结果。抽样以 affiliate 为单位，样本量与 seeds 均预先固定；不声称置信度、检出概率或真实世界外推。</span></div>
    <div class="table-wrap" style="margin-top:18px"><table>
      <caption style="position:absolute;left:-10000px"><span data-lang="en">Full population versus bounded sample results</span><span data-lang="zh">全量总体与有限抽样结果</span></caption>
      <thead><tr>
        <th scope="col">Seed</th>
        <th scope="col"><span data-lang="en">Sample unit</span><span data-lang="zh">抽样单位</span></th>
        <th scope="col"><span data-lang="en">Sample size</span><span data-lang="zh">样本量</span></th>
        <th scope="col"><span data-lang="en">Observed caught</span><span data-lang="zh">实际捕获</span></th>
        <th scope="col"><span data-lang="en">Observed missed</span><span data-lang="zh">实际漏过</span></th>
        <th scope="col"><span data-lang="en">Affiliate sampling-frame coverage</span><span data-lang="zh">Affiliate 抽样框覆盖</span></th>
      </tr></thead>
      <tbody id="sampleRows"></tbody>
    </table></div>
  </section>

  <section id="evidence">
    <h2><span data-lang="en">Evidence and authority boundary</span><span data-lang="zh">证据与权限边界</span></h2>
    <div class="boundary">
      <div><strong><span data-lang="en">What this run establishes</span><span data-lang="zh">本次运行能够证明</span></strong>
        <ul>
          <li><span data-lang="en">The fabricated population reconciled.</span><span data-lang="zh">编造的测试总体已完成对账。</span></li>
          <li><span data-lang="en">Rules and thresholds were hash-bound before the logical run; the time order is self-attested, not externally timestamped.</span><span data-lang="zh">规则与阈值在逻辑运行前完成哈希绑定；时间顺序属于自我声明，并无外部时间戳证明。</span></li>
          <li><span data-lang="en">Seeded positive and negative controls behaved as declared.</span><span data-lang="zh">预设正负控制按声明运行。</span></li>
          <li><span data-lang="en">Each signal resolves to exact source rows.</span><span data-lang="zh">每个信号均可追溯到准确源数据行。</span></li>
        </ul>
      </div>
      <div><strong><span data-lang="en">What remains human or unknown</span><span data-lang="zh">仍需人工或保持未知</span></strong>
        <ul>
          <li><span data-lang="en">Whether any relationship is legitimate, erroneous or misconduct.</span><span data-lang="zh">关系属于合理、错误还是行为不当。</span></li>
          <li><span data-lang="en">Whether a real data population is complete or identity-resolved.</span><span data-lang="zh">真实数据总体是否完整、身份是否准确解析。</span></li>
          <li><span data-lang="en">Legal basis, proportionality, retention and employee notice.</span><span data-lang="zh">合法依据、比例原则、留存与员工告知。</span></li>
          <li><span data-lang="en">Any HR, legal, payment or control action.</span><span data-lang="zh">任何人事、法律、付款或控制行动。</span></li>
        </ul>
      </div>
    </div>
    <p style="color:var(--muted); margin-top:18px"><code>{run_id}</code> · self_attested_prototype · automated_action=none</p>
  </section>
</main>
<script>
const model = {data};
const q = s => document.querySelector(s);
const qa = s => [...document.querySelectorAll(s)];
const routeLabel = v => v === 'potential_exception' ? ['Potential exception','潜在异常'] : ['Expected shared','预期共享'];
const severityLabel = {{
  high:['high','高'], medium:['medium','中'], informational:['informational','信息项']
}};
const gateLabel = {{
  G1_snapshot_integrity:['snapshot integrity','快照完整性'],
  G2_population_completeness:['population completeness','总体完整性'],
  G3_precommitment:['pre-commitment','预先承诺'],
  G4_rule_validation:['rule validation','规则验证'],
  G5_traceability:['traceability','可追溯性'],
  G6_append_only_review_contract:['append-only review','只追加复核记录'],
  G7_determinism:['determinism','确定性'],
  G8_bounded_conclusions:['bounded conclusions','有界结论']
}};
function t(pair) {{ return document.documentElement.classList.contains('lang-zh') ? pair[1] : pair[0]; }}
function renderMetrics() {{
  const c = model.run.routing_counts;
  const items = [
    [c.assertion_hits,['Assertion hits','规则命中']],
    [c.potential_assertion_hits,['Potential-exception hits','潜在异常命中']],
    [c.review_cases,['Unique review cases','独立复核案件']],
    [c.context_items,['Expected-shared context','预期共享情境']]
  ];
  q('#metrics').innerHTML = items.map(x => `<div class="card metric"><strong>${{x[0]}}</strong><span>${{t(x[1])}}</span></div>`).join('');
}}
function renderGates() {{
  q('#gates').innerHTML = Object.entries(model.run.gates).map(([k,v]) => {{
    const passed = v === 'passed';
    const status = passed ? t(['PASS','通过']) : t(['RELEASE TEST','发布测试']);
    return `<div class="gate ${{passed ? '' : 'harness'}}">${{passed ? '✓' : '◇'}} ${{t(gateLabel[k] || [k,k])}} · ${{status}}</div>`;
  }}).join('');
}}
let activeFilter = 'all';
function context(e) {{
  if(e.assertion_hits.includes('A')) return `${{e.wallet_id}} · ${{e.overlapping_pair_count}} ${{t(['overlapping pair(s)','组重叠关系'])}}`;
  return `${{e.affiliate_id}} · ${{e.accrual_period}} · ${{e.signal_hit_count}} ${{t(['assertion hit(s)','项规则命中'])}}`;
}}
function formatSources(ids) {{
  const shown = ids.slice(0,4);
  const more = ids.length - shown.length;
  if(more <= 0) return shown.join('<br>');
  return shown.join('<br>') + `<details><summary>+${{more}} ${{t(['more, expand','条，展开'])}}</summary>${{ids.slice(4).join('<br>')}}</details>`;
}}
function renderExceptions() {{
  const rows = model.exceptions.filter(e => activeFilter === 'all' || e.bucket === activeFilter);
  q('#exceptionRows').innerHTML = rows.map(e => `<tr>
    <td><code>${{e.exception_id}}</code></td><td><strong>${{e.rule_branch}}</strong><br><code>${{e.rule_version_id}}</code></td>
    <td><span class="badge ${{e.bucket}}">${{t(routeLabel(e.bucket))}}</span></td>
    <td class="${{e.severity}}">${{t(severityLabel[e.severity] || [e.severity,e.severity])}}</td><td>${{context(e)}}</td>
    <td><code>${{formatSources(e.source_row_ids)}}</code></td></tr>`).join('');
  q('#filterCount').textContent = t([`${{rows.length}} review item(s) shown`, `当前显示 ${{rows.length}} 个复核项`]);
}}
function renderSamples() {{
  q('#sampleRows').innerHTML = model.comparison.sample_runs.map(s => `<tr><td>${{s.seed}}</td><td>${{s.sample_unit}}</td><td>${{s.sample_size}}</td><td>${{s.observed_potential_exceptions}}</td><td>${{s.observed_missed_population_cases}}</td><td>${{s.observed_population_coverage_percent}}%</td></tr>`).join('');
}}
const conclusionLabel = {{
  supported_explanation:['Supported explanation','解释有支持'],
  more_evidence_required:['More evidence required','需要更多证据'],
  control_exception_confirmed:['Control exception confirmed','已确认控制异常'],
  data_quality_issue:['Data-quality issue','数据质量问题']
}};
const dispositionLabel = {{
  keep_open:['Keep open','保持开放'],
  close_with_explanation:['Close with explanation','有解释关闭'],
  escalate_for_investigation:['Escalate for investigation','升级调查']
}};
function renderReviews() {{
  q('#reviewRows').innerHTML = model.reviews.map(r => `<article class="review-card ${{r.supersedes_review_id ? 'review-correction' : ''}}">
    <div class="review-head">
      <strong>${{t(conclusionLabel[r.conclusion] || [r.conclusion,r.conclusion])}}</strong>
      <span class="badge ${{r.disposition === 'escalate_for_investigation' ? 'potential_exception' : 'expected_shared'}}">${{t(dispositionLabel[r.disposition] || [r.disposition,r.disposition])}}</span>
    </div>
    <div class="review-meta"><code>${{r.exception_id}}</code> · ${{r.review_timestamp_utc}} · ${{r.reviewer_id}}</div>
    <p class="review-rationale"><strong>${{t(['Review question','复核问题'])}}:</strong> ${{t([r.question_presented,r.question_presented_zh || r.question_presented])}}</p>
    <p class="review-rationale">${{t([r.rationale,r.rationale_zh || r.rationale])}}</p>
    ${{r.supersedes_review_id ? `<div class="review-meta">${{t(['Supersedes','更正并取代'])}} <code>${{r.supersedes_review_id}}</code></div>` : ''}}
  </article>`).join('');
}}
function setLanguage(language) {{
  document.documentElement.classList.toggle('lang-zh', language === 'zh');
  document.documentElement.lang = language === 'zh' ? 'zh-CN' : 'en';
  q('#language').value = language;
  renderMetrics(); renderGates(); renderExceptions(); renderReviews();
}}
q('#language').addEventListener('change', e => {{
  setLanguage(e.target.value);
  const url = new URL(location.href);
  if (e.target.value === 'zh') url.searchParams.set('lang','zh-CN');
  else url.searchParams.delete('lang');
  history.replaceState(null,'',url);
}});
qa('a[data-case-link]').forEach(link => link.addEventListener('click', event => {{
  event.preventDefault();
  const url = new URL(link.getAttribute('href'), location.href);
  if (document.documentElement.lang === 'zh-CN') url.searchParams.set('lang','zh-CN');
  location.href = url.href;
}}));
qa('.filter').forEach(btn => btn.addEventListener('click', () => {{
  activeFilter = btn.dataset.filter; qa('.filter').forEach(x => x.classList.remove('active'));
  qa('.filter').forEach(x => x.setAttribute('aria-pressed','false'));
  btn.classList.add('active'); btn.setAttribute('aria-pressed','true'); renderExceptions();
}}));
setLanguage(new URLSearchParams(location.search).get('lang') === 'zh-CN' ? 'zh' : 'en');
renderSamples();
</script>
</body>
</html>
"""
