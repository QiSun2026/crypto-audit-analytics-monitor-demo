from __future__ import annotations

import json
from typing import Any


def _json_for_script(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True).replace(
        "</",
        "<\\/",
    )


def _shared_css() -> str:
    return """
:root {
  --ink:#17232c; --muted:#61717d; --page:#f3f6f5; --paper:#ffffff;
  --line:#d5dedc; --blue:#2e5f8c; --blue-soft:#e7eef7;
  --green:#176b43; --green-soft:#dff5e7; --amber:#8a570c;
  --amber-soft:#fff1c7; --red:#a23c34; --red-soft:#fde5e2;
  --radius:18px;
}
* { box-sizing:border-box; }
html { scroll-behavior:smooth; }
body {
  margin:0; background:var(--page); color:var(--ink);
  font-family:Inter,"Segoe UI",Arial,"Microsoft YaHei","PingFang SC",sans-serif;
}
a { color:inherit; }
button,select,a { font:inherit; }
.top {
  min-height:76px; display:flex; align-items:center; justify-content:space-between;
  gap:24px; padding:14px clamp(20px,4vw,64px); background:rgba(255,255,255,.96);
  border-bottom:1px solid var(--line); position:sticky; top:0; z-index:5;
}
.brand { font-weight:800; font-size:20px; text-decoration:none; white-space:nowrap; }
.tools { display:flex; align-items:center; gap:12px; color:var(--muted); font-weight:700; }
select { min-width:118px; padding:10px 34px 10px 14px; border:1px solid #aebbb8;
  border-radius:999px; color:var(--ink); background:white; }
main { width:min(1320px,calc(100% - 40px)); margin:0 auto; padding:56px 0 72px; }
.back { display:inline-flex; min-height:44px; align-items:center; gap:8px; padding:0 16px;
  border-radius:999px; background:var(--blue-soft); color:#244f78; font-weight:800;
  text-decoration:none; }
.hero { display:grid; grid-template-columns:minmax(0,1.25fr) minmax(320px,.75fr);
  gap:42px; align-items:center; min-height:420px; }
.hero h1 { font-size:clamp(46px,7vw,88px); line-height:.98; letter-spacing:-.035em;
  margin:0 0 24px; max-width:13ch; }
.lede { color:var(--muted); font-size:clamp(19px,2vw,25px); line-height:1.55;
  max-width:62ch; margin:0; }
.flow { background:var(--paper); border:1px solid var(--line); border-radius:var(--radius);
  padding:30px; }
.flow h2 { margin:0 0 18px; font-size:20px; }
.flow ol { list-style:none; padding:0; margin:0; display:grid; gap:0; }
.flow li { display:grid; grid-template-columns:36px 1fr; gap:14px; align-items:center;
  min-height:58px; border-bottom:1px solid var(--line); }
.flow li:last-child { border:0; }
.flow b { width:32px; height:32px; display:grid; place-items:center; border-radius:50%;
  background:var(--blue-soft); color:var(--blue); }
.section { margin-top:64px; }
.section h2 { font-size:clamp(30px,4vw,50px); margin:0 0 12px; letter-spacing:-.035em; }
.section-intro { color:var(--muted); font-size:18px; line-height:1.6; max-width:72ch; margin:0 0 28px; }
.case-grid { display:grid; grid-template-columns:1.15fr .85fr; gap:22px; }
.case { display:flex; flex-direction:column; min-height:330px; padding:30px;
  border:1px solid var(--line); border-radius:var(--radius); background:var(--paper);
  text-decoration:none; transition:transform .18s ease,border-color .18s ease; }
.case:hover { transform:translateY(-3px); border-color:#91a9bd; }
.case:active { transform:translateY(-1px); }
.case:focus-visible,.back:focus-visible,select:focus-visible { outline:3px solid #7aa7cd; outline-offset:3px; }
.case.agent { background:#eef3f8; }
.case h3 { font-size:clamp(29px,3vw,42px); line-height:1.05; margin:38px 0 16px;
  max-width:15ch; letter-spacing:-.035em; }
.case p { color:var(--muted); font-size:18px; line-height:1.55; margin:0; max-width:54ch; }
.case footer { margin-top:auto; display:flex; align-items:center; justify-content:space-between;
  gap:16px; padding-top:28px; font-weight:800; color:var(--blue); }
.tag { display:inline-flex; width:max-content; min-height:36px; align-items:center;
  padding:0 12px; border-radius:999px; background:var(--blue-soft); color:#244f78;
  font-weight:800; font-size:14px; }
.tag.green { background:var(--green-soft); color:var(--green); }
.tag.amber { background:var(--amber-soft); color:var(--amber); }
.tag.red { background:var(--red-soft); color:var(--red); }
.case-title { margin:26px 0 8px; font-size:clamp(34px,5vw,62px); letter-spacing:-.04em; }
.case-copy { color:var(--muted); font-size:20px; line-height:1.55; max-width:72ch; margin:0; }
.chip-row { display:flex; flex-wrap:wrap; gap:10px; margin:24px 0 0; }
.metrics { display:grid; grid-template-columns:repeat(4,1fr); gap:14px; margin:34px 0; }
.metric { padding:24px; border:1px solid var(--line); border-radius:var(--radius); background:white; }
.metric strong { display:block; font-size:40px; margin-bottom:8px; }
.metric span { color:var(--muted); line-height:1.35; }
.metric.green { background:var(--green-soft); border-color:#a8d9ba; color:var(--green); }
.metric.amber { background:var(--amber-soft); border-color:#e7c66c; color:var(--amber); }
.metric.blue { background:var(--blue-soft); border-color:#b5cbe0; color:var(--blue); }
.panel { background:white; border:1px solid var(--line); border-radius:var(--radius);
  padding:28px; margin-top:18px; }
.panel h2 { margin:0 0 8px; font-size:28px; }
.panel>p { margin:0 0 22px; color:var(--muted); line-height:1.55; }
.gate-grid { display:grid; grid-template-columns:repeat(4,1fr); gap:10px; }
.gate { padding:14px; border-radius:12px; background:var(--green-soft); color:var(--green);
  font-weight:800; font-size:14px; }
.gate.release { background:var(--blue-soft); color:var(--blue); }
.item-list { display:grid; gap:12px; }
.item { border:1px solid var(--line); border-radius:14px; padding:20px; }
.item-head { display:flex; align-items:flex-start; justify-content:space-between; gap:16px; }
.item h3 { margin:0; font-size:20px; overflow-wrap:anywhere; }
.item p { margin:10px 0 0; color:var(--muted); line-height:1.5; }
.meta { margin-top:12px; color:var(--muted); font-family:Consolas,monospace; font-size:13px;
  overflow-wrap:anywhere; }
.boundary { display:grid; grid-template-columns:1fr 1fr; gap:18px; }
.boundary div { padding:22px; border-radius:14px; background:#f7f9f8; }
.boundary h3 { margin:0 0 10px; }
.boundary p { margin:0; color:var(--muted); line-height:1.55; }
[data-lang="zh"] { display:none; }
html[data-language="zh"] [data-lang="en"] { display:none; }
html[data-language="zh"] [data-lang="zh"] { display:initial; }
@media(max-width:900px) {
  .hero,.case-grid,.boundary { grid-template-columns:1fr; }
  .hero { min-height:0; }
  .metrics,.gate-grid { grid-template-columns:1fr 1fr; }
}
@media(max-width:560px) {
  .top { align-items:flex-start; }
  .tools>span { display:none; }
  main { width:min(100% - 28px,1320px); padding-top:34px; }
  .hero h1 { font-size:46px; }
  .metrics,.gate-grid { grid-template-columns:1fr; }
  .case { min-height:300px; padding:24px; }
  .item-head { display:grid; grid-template-columns:1fr; }
}
@media(prefers-reduced-motion:reduce) {
  html { scroll-behavior:auto; }
  .case { transition:none; }
}
"""


def _language_script() -> str:
    return """
const params = new URLSearchParams(location.search);
const initial = params.get('lang') === 'zh-CN' ? 'zh' : 'en';
const select = document.querySelector('#language');
function setLanguage(language) {
  document.documentElement.dataset.language = language;
  document.documentElement.lang = language === 'zh' ? 'zh-CN' : 'en';
  if (select) select.value = language;
}
setLanguage(initial);
if (select) {
  select.addEventListener('change', event => {
    setLanguage(event.target.value);
    const url = new URL(location.href);
    if (event.target.value === 'zh') url.searchParams.set('lang','zh-CN');
    else url.searchParams.delete('lang');
    history.replaceState(null,'',url);
  });
}
document.querySelectorAll('a[data-case-link]').forEach(link => {
  link.addEventListener('click', event => {
    event.preventDefault();
    const url = new URL(link.getAttribute('href'), location.href);
    if (document.documentElement.dataset.language === 'zh') {
      url.searchParams.set('lang','zh-CN');
    }
    location.href = url.href;
  });
});
"""


def render_showcase() -> str:
    return f"""<!doctype html>
<html lang="en" data-language="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>RiskFirewall Evidence Integrity Harness</title>
<style>{_shared_css()}</style>
</head>
<body>
<header class="top">
  <a class="brand" href="index.html">RiskFirewall</a>
  <div class="tools">
    <span>Language / 语言</span>
    <select id="language" aria-label="Language">
      <option value="en">English</option>
      <option value="zh">中文</option>
    </select>
  </div>
</header>
<main>
  <section class="hero">
    <div>
      <h1><span data-lang="en">Evidence before assurance.</span><span data-lang="zh">先验证证据，再形成鉴证结论。</span></h1>
      <p class="lede"><span data-lang="en">A deterministic, fail-closed harness that binds review items to pre-committed rules, source rows and accountable human decisions. Failed gates stop evidence-pack export; they do not block transactions, employees, launches or agent actions.</span><span data-lang="zh">一个确定性、失败即关闭的证据完整性 Harness，把复核事项绑定到预先承诺的规则、源数据行与可问责的人工决定。闸门失败只会阻止证据包导出，不会阻断交易、员工、产品上线或 Agent 行为。</span></p>
    </div>
    <aside class="flow">
      <h2><span data-lang="en">Evidence contract</span><span data-lang="zh">证据契约</span></h2>
      <ol>
        <li><b>1</b><span data-lang="en">Pre-commit the rule</span><span data-lang="zh">预先承诺规则</span></li>
        <li><b>2</b><span data-lang="en">Run deterministically</span><span data-lang="zh">确定性执行</span></li>
        <li><b>3</b><span data-lang="en">Fail closed on drift</span><span data-lang="zh">发现漂移即关闭</span></li>
        <li><b>4</b><span data-lang="en">Bind the evidence pack</span><span data-lang="zh">绑定证据包</span></li>
        <li><b>5</b><span data-lang="en">Preserve human authority</span><span data-lang="zh">保留人工决定权</span></li>
      </ol>
    </aside>
  </section>
  <section class="section">
    <h2><span data-lang="en">Choose an assurance case.</span><span data-lang="zh">选择一个鉴证案例。</span></h2>
    <p class="section-intro"><span data-lang="en">Two synthetic applications use the same evidence-integrity mechanisms. Their results remain separate and are not combined into a compensating score.</span><span data-lang="zh">两个合成案例使用同一套证据完整性机制。结果彼此独立，不汇总为可补偿的单一分数。</span></p>
    <div class="case-grid">
      <a class="case" href="commission_case.html" data-case-link>
        <span class="tag green"><span data-lang="en">Audit Assurance</span><span data-lang="zh">审计鉴证</span></span>
        <h3><span data-lang="en">Commission assurance</span><span data-lang="zh">佣金审计证据</span></h3>
        <p><span data-lang="en">Full-population wallet and commission tests with explicit samples, false positives, lineage and worked human reviews.</span><span data-lang="zh">对钱包与佣金执行全量测试，明确展示抽样、误报、证据血缘和人工复核记录。</span></p>
        <footer><span data-lang="en">Open case</span><span data-lang="zh">进入案例</span><span aria-hidden="true">→</span></footer>
      </a>
      <a class="case agent" href="agent_action_case.html" data-case-link>
        <span class="tag"><span data-lang="en">AI as audited subject</span><span data-lang="zh">AI 是被审对象</span></span>
        <h3><span data-lang="en">AI agent action assurance</span><span data-lang="zh">AI Agent 行为审计</span></h3>
        <p><span data-lang="en">One deterministic rule tests whether irreversible agent actions bind to an exact, valid human approval artifact.</span><span data-lang="zh">一条确定性规则检验不可逆 Agent 行为是否绑定准确且有效的人工批准凭证。</span></p>
        <footer><span data-lang="en">Open case</span><span data-lang="zh">进入案例</span><span aria-hidden="true">→</span></footer>
      </a>
    </div>
  </section>
</main>
<script>{_language_script()}</script>
</body>
</html>
"""


def render_agent_action_case(
    run_manifest: dict[str, Any],
    exceptions: list[dict[str, Any]],
    context_items: list[dict[str, Any]],
    *,
    back_href: str = "../../demo/index.html",
) -> str:
    model = _json_for_script(
        {
            "run": run_manifest,
            "exceptions": exceptions,
            "context": context_items,
        }
    )
    return f"""<!doctype html>
<html lang="en" data-language="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>AI Agent Action Assurance</title>
<style>{_shared_css()}</style>
</head>
<body>
<header class="top">
  <a class="brand" href="{back_href}" data-case-link>RiskFirewall</a>
  <div class="tools">
    <span>Language / 语言</span>
    <select id="language" aria-label="Language">
      <option value="en">English</option>
      <option value="zh">中文</option>
    </select>
  </div>
</header>
<main>
  <a class="back" href="{back_href}" data-case-link><span aria-hidden="true">←</span><span data-lang="en">All assurance cases</span><span data-lang="zh">全部鉴证案例</span></a>
  <h1 class="case-title"><span data-lang="en">AI agent action assurance</span><span data-lang="zh">AI Agent 行为审计</span></h1>
  <p class="case-copy"><span data-lang="en">A controlled synthetic trial. Deterministic SQL checks whether irreversible actions bind to the exact approved payload at execution time. It does not use AI to detect, classify or decide.</span><span data-lang="zh">这是受控的合成试验。确定性 SQL 检查不可逆行为在执行时是否绑定获批的准确 payload。系统不使用 AI 进行检测、分类或决策。</span></p>
  <div class="chip-row">
    <span class="tag"><span data-lang="en">Synthetic only</span><span data-lang="zh">仅合成数据</span></span>
    <span class="tag amber"><span data-lang="en">Human decision required</span><span data-lang="zh">必须人工判断</span></span>
    <span class="tag red"><span data-lang="en">No runtime blocking</span><span data-lang="zh">不作运行时阻断</span></span>
  </div>
  <section class="metrics" id="metrics"></section>
  <section class="panel">
    <h2><span data-lang="en">Human review status</span><span data-lang="zh">人工复核状态</span></h2>
    <p><span data-lang="en">Pending · 0 human review records · no disposition recorded. The review chain is initialized and append-ready.</span><span data-lang="zh">待处理 · 0 条人工复核记录 · 尚未录入处置结论。复核链已初始化，可按只追加方式记录后续判断。</span></p>
    <p><span data-lang="en">This example tests approval existence, decision, exact payload hash and validity window. It does not test approval uniqueness, revocation, consumption or one-time use.</span><span data-lang="zh">本示例仅检查批准记录是否存在、决定状态、准确 payload 哈希及有效期；不检查批准唯一性、撤销、消耗或单次使用。</span></p>
  </section>
  <section class="panel">
    <h2><span data-lang="en">Integrity gates</span><span data-lang="zh">完整性闸门</span></h2>
    <p><span data-lang="en">Runtime gates pass in the generated case. Review-chain and determinism gates remain release-test controls.</span><span data-lang="zh">生成案例中的运行闸门已通过。复核链和确定性闸门仍由发布测试验证。</span></p>
    <div class="gate-grid" id="gates"></div>
  </section>
  <section class="panel">
    <h2><span data-lang="en">Exceptions requiring explanation</span><span data-lang="zh">需要解释的异常</span></h2>
    <p><span data-lang="en">A signal means approval evidence was not proven by the frozen inputs. It is not a finding of misconduct.</span><span data-lang="zh">信号只表示冻结输入未能证明批准证据充分，不代表认定存在不当行为。</span></p>
    <div class="item-list" id="exceptions"></div>
  </section>
  <section class="panel">
    <h2><span data-lang="en">Visible non-exception context</span><span data-lang="zh">可见的非异常背景</span></h2>
    <p><span data-lang="en">Reversible actions and exactly bound approvals remain visible instead of disappearing through silent exclusion.</span><span data-lang="zh">可逆行为和准确绑定的批准记录仍然可见，不会因静默排除而消失。</span></p>
    <div class="item-list" id="context"></div>
  </section>
  <section class="panel boundary">
    <div>
      <h3><span data-lang="en">L1 release candidate</span><span data-lang="zh">L1 发布候选</span></h3>
      <p><span data-lang="en">Deterministic recomputation on fabricated, hash-bound inputs; G6-G7 remain release-harness checks.</span><span data-lang="zh">对哈希绑定的合成输入进行确定性重算；G6-G7 仍需发布 Harness 验证。</span></p>
    </div>
    <div>
      <h3><span data-lang="en">Not achieved</span><span data-lang="zh">尚未达到</span></h3>
      <p><span data-lang="en">Source authentication, external validation, production enforcement and authenticated reviewer identity.</span><span data-lang="zh">尚未实现来源认证、外部验证、生产阻断和审阅人身份认证。</span></p>
    </div>
  </section>
</main>
<script id="model" type="application/json">{model}</script>
<script>
{_language_script()}
const model = JSON.parse(document.querySelector('#model').textContent);
const text = (en,zh) => document.documentElement.dataset.language === 'zh' ? zh : en;
const gateLabels = {{
  G1_snapshot_integrity:['Snapshot integrity','快照完整性'],
  G2_population_completeness:['Population completeness','总体完整性'],
  G3_precommitment:['Registered pre-commitment','已注册预先承诺'],
  G4_rule_validation:['Rule validation','规则验证'],
  G5_traceability:['Source-row traceability','源数据行可追溯'],
  G6_append_only_review_contract:['Append-only review','只追加复核'],
  G7_determinism:['Deterministic recomputation','确定性重算'],
  G8_bounded_conclusions:['Bounded conclusions','有界结论']
}};
const statusLabels = {{
  passed:['passed','通过'],
  implemented_requires_release_test:['release test','发布测试'],
  requires_release_test:['release test','发布测试']
}};
const metricData = [
  [model.run.population.actions,'Actions tested','已测试行为',''],
  [model.run.routing_counts.potential_exceptions,'Exceptions','异常','amber'],
  [model.run.routing_counts.context_items,'Visible context','可见背景','blue'],
  [0,'Automated decisions','自动决定','green']
];
function draw() {{
  document.querySelector('#metrics').innerHTML = metricData.map(item =>
    `<div class="metric ${{item[3]}}"><strong>${{item[0]}}</strong><span>${{text(item[1],item[2])}}</span></div>`
  ).join('');
  document.querySelector('#gates').innerHTML = Object.entries(model.run.gates).map(([name,status]) =>
    `<div class="gate ${{status === 'passed' ? '' : 'release'}}">${{text(...(gateLabels[name] || [name,name]))}}<br>${{text(...(statusLabels[status] || [status,status]))}}</div>`
  ).join('');
  document.querySelector('#exceptions').innerHTML = model.exceptions.map(item =>
    `<article class="item"><div class="item-head"><h3>${{item.action_id}} · ${{item.signal_code}}</h3><span class="tag amber">${{text('Human review','人工复核')}}</span></div><p>${{text(item.human_question,'是否存在与准确行为 payload 匹配的有效批准凭证，还是该事项应继续保持开放？')}}</p><div class="meta">${{item.source_row_ids.join(' | ')}}</div></article>`
  ).join('');
  document.querySelector('#context').innerHTML = model.context.map(item =>
    `<article class="item"><div class="item-head"><h3>${{item.action_id}} · ${{item.bucket}}</h3><span class="tag green">${{text('Retained','已保留')}}</span></div><p>${{text(item.signal_statement,item.bucket === 'context_only' ? '可逆行为背景已明确保留。' : '准确的人工批准证据已绑定。')}}</p><div class="meta">${{item.source_row_ids.join(' | ')}}</div></article>`
  ).join('');
}}
draw();
document.querySelector('#language').addEventListener('change',draw);
</script>
</body>
</html>
"""
