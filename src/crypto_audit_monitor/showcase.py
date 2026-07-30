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
  --gray:#536174; --gray-soft:#edf0f4;
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
.brand { color:var(--ink); font:800 20px/1.2 Inter,Segoe UI,Arial,sans-serif;
  letter-spacing:-.02em; text-decoration:none; }
.brand span { color:var(--blue); margin-right:6px; }
.brand:hover { color:var(--blue); }
.brand:focus-visible { outline:3px solid #b8cce2; outline-offset:5px; border-radius:4px; }
.tools { display:flex; align-items:center; gap:12px; color:var(--muted); font-weight:700; }
select { min-width:118px; padding:10px 34px 10px 14px; border:1px solid #aebbb8;
  border-radius:999px; color:var(--ink); background:white; }
main { width:min(1320px,calc(100% - 40px)); margin:0 auto; padding:56px 0 72px; }
.back { display:inline-flex; min-height:44px; align-items:center; gap:8px; padding:0 16px;
  border-radius:999px; background:var(--blue-soft); color:#244f78; font-weight:800;
  text-decoration:none; }
.hero { display:grid; grid-template-columns:minmax(0,1.25fr) minmax(320px,.75fr);
  gap:42px; align-items:center; min-height:420px; }
.product-lockup { display:grid; gap:5px; margin-bottom:24px; }
.product-lockup strong { color:var(--blue); font-size:20px; letter-spacing:-.02em; }
.product-lockup span { color:var(--muted); font-size:15px; font-weight:700; }
.hero h1 { font-size:clamp(46px,7vw,88px); line-height:.98; letter-spacing:-.035em;
  margin:0 0 24px; max-width:13ch; }
.lede { color:var(--muted); font-size:clamp(19px,2vw,25px); line-height:1.55;
  max-width:62ch; margin:0; }
.scope-note { color:var(--gray); font-size:15px; line-height:1.5; max-width:72ch;
  margin:18px 0 0; }
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
.relationship { display:flex; flex-wrap:wrap; align-items:center; gap:10px;
  margin:26px 0; padding:18px 0; border-top:1px solid var(--line);
  border-bottom:1px solid var(--line); }
.relationship span { color:var(--muted); }
.relationship strong { color:var(--ink); }
.relationship b { color:var(--blue); font-weight:800; }
.case-grid { display:grid; grid-template-columns:1fr 1fr; gap:22px; }
.case { display:flex; flex-direction:column; min-height:330px; padding:30px;
  border:1px solid var(--line); border-radius:var(--radius); background:var(--paper);
  transition:border-color .18s ease; }
.case:hover { border-color:#91a9bd; }
.case-link:focus-visible,.workflow-link:focus-visible,.back:focus-visible,select:focus-visible {
  outline:3px solid #7aa7cd; outline-offset:3px;
}
.case h3 { font-size:clamp(29px,3vw,42px); line-height:1.05; margin:38px 0 16px;
  max-width:15ch; letter-spacing:-.035em; }
.case p { color:var(--muted); font-size:18px; line-height:1.55; margin:0; max-width:54ch; }
.case-actions { margin-top:auto; display:flex; flex-wrap:wrap; align-items:center;
  gap:18px; padding-top:28px; }
.case-link,.workflow-link { color:var(--blue); font-weight:800; text-decoration:none; }
.workflow-note { margin-top:24px; padding-top:20px; border-top:1px solid var(--line); }
.workflow-note p { margin-top:7px; color:#42576a; font-size:16px; }
.workflow-note .workflow-link { display:inline-block; margin-top:12px; }
.tag { display:inline-flex; width:max-content; min-height:36px; align-items:center;
  padding:0 12px; border-radius:999px; background:var(--gray-soft); color:var(--gray);
  font-weight:800; font-size:14px; }
.tag.blue { background:var(--blue-soft); color:#244f78; }
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
.metric.green span { color:#145d3a; }
.metric.amber span { color:#744908; }
.metric.blue span { color:#244f78; }
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
.item p strong { color:var(--ink); }
.item .question { color:var(--ink); }
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
  .brand { max-width:68%; font-size:16px; }
  .tools>span { display:none; }
  main { width:min(100% - 28px,1320px); padding-top:34px; }
  .hero h1 { font-size:46px; }
  .relationship { display:grid; gap:6px; }
  .relationship b { display:none; }
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
<title>RiskFirewall AI — Risk Control Assurance</title>
<style>{_shared_css()}</style>
</head>
<body>
<header class="top">
  <a class="brand" href="index.html">RiskFirewall AI — Risk Control Assurance</a>
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
      <div class="product-lockup">
        <strong>RiskFirewall AI — Risk Control Assurance</strong>
        <span data-lang="en">Transactions, Processes &amp; AI Actions · Third Line</span><span data-lang="zh">交易、流程与 AI 行为 · 第三道防线</span>
      </div>
      <h1><span data-lang="en">Evidence before assurance.</span><span data-lang="zh">先验证证据，再形成鉴证结论。</span></h1>
      <p class="lede"><span data-lang="en">A deterministic, fail-closed harness that binds review items to pre-committed rules, source rows and accountable human decisions. Failed gates stop evidence-pack export; they do not block transactions, employees, launches or agent actions.</span><span data-lang="zh">一个确定性、失败即关闭的证据完整性 Harness，把复核事项绑定到预先承诺的规则、源数据行与可问责的人工决定。闸门失败只会阻止证据包导出，不会阻断交易、员工、产品上线或 Agent 行为。</span></p>
      <p class="scope-note"><span data-lang="en">Third-line review of risk controls and their evidence—not full Operational Risk or AML coverage. RiskFirewall AI names the audited AI-action domain and an agent-ready target workflow; this verified release does not use a live AI or Agent to execute tests or make decisions.</span><span data-lang="zh">本产品用于第三道防线复核风险控制及其证据，不声称覆盖完整的操作风险或反洗钱职能。RiskFirewall AI 表示 AI 行为可作为被审对象，以及工作流具备 Agent-ready 的目标形态；本次已验证版本不使用真实 AI 或 Agent 执行测试或作出决定。</span></p>
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
    <h2><span data-lang="en">One product. Two cases. One shared method.</span><span data-lang="zh">一个产品，两个案例，同一套方法。</span></h2>
    <p class="section-intro"><span data-lang="en">Risk Control Assurance is the product. The two synthetic cases below show where the same evidence-integrity method can be applied. The workflow view belongs to Case 1; it is not a third product or case.</span><span data-lang="zh">Risk Control Assurance 是产品。下面两个合成案例展示同一套证据完整性方法可以应用在哪里。工作流视图属于案例 1，不是第三个产品或案例。</span></p>
    <div class="relationship" aria-label="Demo relationship">
      <span><strong><span data-lang="en">Product</span><span data-lang="zh">产品</span></strong> · Risk Control Assurance</span>
      <b aria-hidden="true">→</b>
      <span><strong><span data-lang="en">Cases</span><span data-lang="zh">案例</span></strong> · <span data-lang="en">Commission data + AI action logs</span><span data-lang="zh">佣金数据 + AI 行为日志</span></span>
      <b aria-hidden="true">→</b>
      <span><strong><span data-lang="en">Workflow view</span><span data-lang="zh">工作流视图</span></strong> · <span data-lang="en">applied to Case 1</span><span data-lang="zh">应用于案例 1</span></span>
    </div>
    <div class="case-grid">
      <article class="case">
        <span class="tag blue"><span data-lang="en">Case 1 · Commission data</span><span data-lang="zh">案例 1 · 佣金数据</span></span>
        <h3><span data-lang="en">Wallet and commission review</span><span data-lang="zh">钱包与佣金复核</span></h3>
        <p><span data-lang="en">Full-population wallet and commission tests with explicit samples, false positives, lineage and worked human reviews.</span><span data-lang="zh">对钱包与佣金执行全量测试，明确展示抽样、误报、证据血缘和人工复核记录。</span></p>
        <div class="case-actions">
          <a class="case-link" href="commission_case.html" data-case-link><span data-lang="en">Open evidence case →</span><span data-lang="zh">查看证据案例 →</span></a>
        </div>
        <div class="workflow-note">
          <span class="tag"><span data-lang="en">Second view of Case 1</span><span data-lang="zh">案例 1 的第二种视图</span></span>
          <p><span data-lang="en">See the same evidence move through a frozen mandate, allowlisted execution and human-only dispositions.</span><span data-lang="zh">查看同一组证据如何经过冻结授权、白名单执行和仅限人工的处置。</span></p>
          <a class="workflow-link" href="bounded_workflow_case.html" data-case-link><span data-lang="en">Open controlled workflow →</span><span data-lang="zh">查看受控工作流 →</span></a>
        </div>
      </article>
      <article class="case">
        <span class="tag blue"><span data-lang="en">Case 2 · AI action logs</span><span data-lang="zh">案例 2 · AI 行为日志</span></span>
        <h3><span data-lang="en">Agent action approval review</span><span data-lang="zh">Agent 行为批准复核</span></h3>
        <p><span data-lang="en">One deterministic rule tests whether irreversible agent actions bind to an exact, valid human approval artifact.</span><span data-lang="zh">一条确定性规则检验不可逆 Agent 行为是否绑定准确且有效的人工批准凭证。</span></p>
        <div class="case-actions">
          <a class="case-link" href="agent_action_case.html" data-case-link><span data-lang="en">Open evidence case →</span><span data-lang="zh">查看证据案例 →</span></a>
        </div>
      </article>
    </div>
  </section>
</main>
<script>{_language_script()}</script>
</body>
</html>
"""


def render_bounded_workflow_case(
    result: dict[str, Any],
    *,
    back_href: str = "index.html",
) -> str:
    model = _json_for_script(
        {
            "workflow": result["workflow_manifest"],
            "mandate": result["mandate"],
            "proposal": result["planning_proposal"],
            "freeze": result["human_freeze"],
            "drafts": result["investigation_drafts"],
            "metrics": result["drafting_control_metrics"],
            "reviews": result["human_reviews"],
            "conclusion": result["conclusion_draft"],
        }
    )
    return f"""<!doctype html>
<html lang="en" data-language="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Bounded Workflow | RiskFirewall AI — Risk Control Assurance</title>
<style>{_shared_css()}</style>
</head>
<body>
<header class="top">
  <a class="brand" href="{back_href}" data-case-link>RiskFirewall AI — Risk Control Assurance</a>
  <div class="tools">
    <span>Language / 语言</span>
    <select id="language" aria-label="Language">
      <option value="en">English</option>
      <option value="zh">中文</option>
    </select>
  </div>
</header>
<main>
  <a class="back" href="{back_href}" data-case-link><span aria-hidden="true">←</span><span data-lang="en">All cases</span><span data-lang="zh">全部案例</span></a>
  <div class="eyebrow"><span data-lang="en">Workflow view of Case 1 · Commission control assurance</span><span data-lang="zh">案例 1 工作流视图 · 佣金控制鉴证</span></div>
  <h1 class="case-title"><span data-lang="en">Human-directed, workflow-executed, agent-ready.</span><span data-lang="zh">人工定向、工作流执行、Agent-ready。</span></h1>
  <p class="case-copy"><span data-lang="en">A controlled workflow proof on the existing synthetic commission case. A human fixes scope and thresholds; the workflow may run only the registered test, draft cited questions, and prepare an unsigned conclusion from human records.</span><span data-lang="zh">这是在既有合成佣金案例上的受控工作流证明。人工冻结范围与阈值；工作流只能运行已登记测试、起草带引用的问题，并依据人工记录形成未签署的结论草稿。</span></p>
  <div class="chip-row">
    <span class="tag green"><span data-lang="en">Frozen mandate verified</span><span data-lang="zh">冻结授权已验证</span></span>
    <span class="tag"><span data-lang="en">Same commission case · not a third domain</span><span data-lang="zh">同一佣金案例 · 不是第三个领域</span></span>
    <span class="tag"><span data-lang="en">Fixture provider — no external model</span><span data-lang="zh">Fixture Provider — 未调用外部模型</span></span>
    <span class="tag amber"><span data-lang="en">Human disposition required</span><span data-lang="zh">必须人工处置</span></span>
    <span class="tag red"><span data-lang="en">No automated audit opinion</span><span data-lang="zh">不自动形成审计意见</span></span>
  </div>

  <section class="metrics">
    <div class="metric blue"><strong>1</strong><span data-lang="en">Allowlisted deterministic test</span><span data-lang="zh">白名单确定性测试</span></div>
    <div class="metric green"><strong>{result["drafting_control_metrics"]["citation_coverage_percent"]:.0f}%</strong><span data-lang="en">Claim citation coverage</span><span data-lang="zh">Claim 引用覆盖率</span></div>
    <div class="metric amber"><strong>{len(result["conclusion_draft"]["open_exception_ids"])}</strong><span data-lang="en">Items remain open</span><span data-lang="zh">仍保持开放的事项</span></div>
    <div class="metric green"><strong>0</strong><span data-lang="en">Unauthorized state mutations</span><span data-lang="zh">未经授权的状态变更</span></div>
  </section>

  <section class="panel">
    <h2><span data-lang="en">Bounded execution path</span><span data-lang="zh">受控执行路径</span></h2>
    <p><span data-lang="en">Every step is a separate artifact. Hash drift or an unallowlisted procedure stops this workflow run and evidence-pack export.</span><span data-lang="zh">每一步都是独立产物。哈希漂移或未列入白名单的程序都会阻断本次工作流运行和证据包导出。</span></p>
    <div class="item-list">
      <article class="item"><div class="item-head"><h3><span data-lang="en">1 · Human Audit Mandate</span><span data-lang="zh">1 · 人工审计授权</span></h3><span class="tag green"><span data-lang="en">Frozen</span><span data-lang="zh">已冻结</span></span></div><p><span data-lang="en">Scope, provisional threshold, test allowlist and prohibitions are human-owned.</span><span data-lang="zh">范围、暂定阈值、测试白名单和禁令均由人工负责。</span></p><div class="meta">{result["mandate"]["mandate_sha256"]}</div></article>
      <article class="item"><div class="item-head"><h3><span data-lang="en">2 · Planning proposal</span><span data-lang="zh">2 · 计划提案</span></h3><span class="tag"><span data-lang="en">Proposal only</span><span data-lang="zh">仅为提案</span></span></div><p><span data-lang="en">The workflow proposes one registered procedure. It has no authority until the exact proposal is frozen.</span><span data-lang="zh">工作流只提议一项已登记程序；准确计划被人工冻结前不具备执行权限。</span></p><div class="meta">{result["planning_proposal"]["proposal_sha256"]}</div></article>
      <article class="item"><div class="item-head"><h3><span data-lang="en">3 · Deterministic execution</span><span data-lang="zh">3 · 确定性执行</span></h3><span class="tag green"><span data-lang="en">Verified</span><span data-lang="zh">已验证</span></span></div><p><span data-lang="en">The existing full-population SQL engine runs unchanged and exports its evidence pack.</span><span data-lang="zh">既有全量 SQL 引擎保持不变并导出证据包。</span></p><div class="meta">{result["deterministic_result"]["run_manifest"]["run_id"]}</div></article>
      <article class="item"><div class="item-head"><h3><span data-lang="en">4 · Investigation drafting</span><span data-lang="zh">4 · 调查草稿</span></h3><span class="tag"><span data-lang="en">Draft only</span><span data-lang="zh">仅为草稿</span></span></div><p><span data-lang="en">Each factual sentence and question resolves only to source rows already bound to its exception.</span><span data-lang="zh">每个事实句和调查问题只能引用已绑定到该异常的源数据行。</span></p><div class="meta">{len(result["investigation_drafts"])} drafts · {result["drafting_control_metrics"]["citation_coverage_percent"]:.1f}% cited</div></article>
      <article class="item"><div class="item-head"><h3><span data-lang="en">5 · Human decision fixtures</span><span data-lang="zh">5 · 人工决定示例记录</span></h3><span class="tag amber"><span data-lang="en">Self-attested Demo fixtures</span><span data-lang="zh">自我声明的 Demo 示例</span></span></div><p><span data-lang="en">Only append-only human review records may close, keep open, or escalate an item. These worked records are generated Demo fixtures, not authenticated human input.</span><span data-lang="zh">只有只追加的人工复核记录可以关闭、保持开放或升级事项。这些示范记录由 Demo 生成，并非经过身份认证的人工输入。</span></p><div class="meta">{len(result["human_reviews"])} worked review fixture records</div></article>
      <article class="item"><div class="item-head"><h3><span data-lang="en">6 · Bounded conclusion draft</span><span data-lang="zh">6 · 有界结论草稿</span></h3><span class="tag red"><span data-lang="en">Unsigned</span><span data-lang="zh">未签署</span></span></div><p><span data-lang="en">{result["conclusion_draft"]["statement"]}</span><span data-lang="zh">示例人工记录关闭 {len(result["conclusion_draft"]["closed_with_explanation_ids"])} 项并附解释，升级 {len(result["conclusion_draft"]["escalated_exception_ids"])} 项，并保留 {len(result["conclusion_draft"]["open_exception_ids"])} 项为开放状态。本草稿不是审计意见，也不是控制有效性结论。</span></p><div class="meta">source_basis=human_review_chain_only · signature=null</div></article>
    </div>
  </section>

  <section class="panel boundary">
    <div>
      <h3><span data-lang="en">What is implemented</span><span data-lang="zh">已经实现</span></h3>
      <p><span data-lang="en">Mandate hashing, exact plan freeze, allowlisted orchestration, raw fixture retention, claim-level citations, human dispositions and an unsigned bounded conclusion draft.</span><span data-lang="zh">授权哈希、准确计划冻结、白名单编排、原始 Fixture 留存、Claim 级引用、人工处置和未签署的有界结论草稿。</span></p>
    </div>
    <div>
      <h3><span data-lang="en">What is not claimed</span><span data-lang="zh">不作出的声明</span></h3>
      <p><span data-lang="en">No external model was run. This does not establish model accuracy, source authenticity, production authorization, autonomous auditing or an audit opinion.</span><span data-lang="zh">未调用外部模型。本示例不能证明模型准确率、来源真实性、生产授权、自主审计能力或审计意见。</span></p>
    </div>
  </section>
</main>
<script id="model" type="application/json">{model}</script>
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
<title>AI Action Review | RiskFirewall AI — Risk Control Assurance</title>
<style>{_shared_css()}</style>
</head>
<body>
<header class="top">
  <a class="brand" href="{back_href}" data-case-link>RiskFirewall AI — Risk Control Assurance</a>
  <div class="tools">
    <span>Language / 语言</span>
    <select id="language" aria-label="Language">
      <option value="en">English</option>
      <option value="zh">中文</option>
    </select>
  </div>
</header>
<main>
  <a class="back" href="{back_href}" data-case-link><span aria-hidden="true">←</span><span data-lang="en">All cases</span><span data-lang="zh">全部案例</span></a>
  <div class="eyebrow"><span data-lang="en">Case 2 · AI action control assurance</span><span data-lang="zh">案例 2 · AI 行为控制鉴证</span></div>
  <h1 class="case-title"><span data-lang="en">AI agent action control assurance</span><span data-lang="zh">AI Agent 行为控制鉴证</span></h1>
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
const signalCopy = {{
  approval_evidence_missing:{{
    title:['Approval evidence missing','未找到批准证据'],
    explanation:[
      'This irreversible action has no linked approval record, so authorization is not proven.',
      '这项不可逆操作没有关联批准记录，因此目前无法证明它已经获得授权。'
    ],
    question:[
      'Find the applicable approval record. If none exists, keep the exception open.',
      '请查找适用的批准记录；如果不存在，该异常应继续保持开放。'
    ]
  }},
  approval_payload_mismatch:{{
    title:['Approval does not match the action','批准内容与实际操作不一致'],
    explanation:[
      'An approval record exists, but its payload does not exactly match the action that was executed.',
      '虽然存在批准记录，但其批准内容与实际执行的操作并不完全一致。'
    ],
    question:[
      'Confirm whether another approval covers the exact action or explain the mismatch.',
      '请确认是否有另一份批准准确覆盖该操作，或解释内容不一致的原因。'
    ]
  }},
  approval_outside_valid_window:{{
    title:['Action occurred outside the approval window','操作时间不在批准有效期内'],
    explanation:[
      'The linked approval existed, but it was not valid when the action was executed.',
      '关联的批准记录确实存在，但在操作执行时并不处于有效期内。'
    ],
    question:[
      'Verify the execution time and approval window, then provide any valid replacement approval.',
      '请核对执行时间和批准有效期，并提供当时有效的替代批准（如有）。'
    ]
  }},
  approval_not_approved:{{
    title:['Approval record did not authorize the action','批准记录未同意该操作'],
    explanation:[
      'The linked record does not have an approved decision status, so it cannot authorize the action.',
      '关联记录的决定状态不是“已批准”，因此不能作为该操作的授权依据。'
    ],
    question:[
      'Confirm the authoritative decision status or provide a valid approved record.',
      '请确认权威的决定状态，或提供一份有效且已批准的记录。'
    ]
  }}
}};
const contextCopy = {{
  context_only:['Reversible action retained','可逆操作：保留背景'],
  evidence_bound_context:['Exact approval matched','批准证据准确匹配']
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
  document.querySelector('#exceptions').innerHTML = model.exceptions.map(item => {{
    const copy = signalCopy[item.signal_code] || {{
      title:[item.signal_code,item.signal_code],
      explanation:[item.signal_statement,item.signal_statement],
      question:[item.human_question,item.human_question]
    }};
    return `<article class="item">
      <div class="item-head"><h3>${{item.action_id}} · ${{text(...copy.title)}}</h3><span class="tag amber">${{text('Human review','人工复核')}}</span></div>
      <p><strong>${{text('What happened:','发生了什么：')}}</strong> ${{text(...copy.explanation)}}</p>
      <p class="question"><strong>${{text('Next check:','下一步核验：')}}</strong> ${{text(...copy.question)}}</p>
      <div class="meta">${{text('Technical rule','技术规则')}}: ${{item.signal_code}} · ${{text('Source rows','来源记录')}}: ${{item.source_row_ids.join(' | ')}}</div>
    </article>`;
  }}).join('');
  document.querySelector('#context').innerHTML = model.context.map(item =>
    `<article class="item"><div class="item-head"><h3>${{item.action_id}} · ${{text(...(contextCopy[item.bucket] || [item.bucket,item.bucket]))}}</h3><span class="tag green">${{text('Retained','已保留')}}</span></div><p>${{text(item.signal_statement,item.bucket === 'context_only' ? '可逆行为背景已明确保留。' : '准确的人工批准证据已绑定。')}}</p><div class="meta">${{text('Technical bucket','技术分类')}}: ${{item.bucket}} · ${{text('Source rows','来源记录')}}: ${{item.source_row_ids.join(' | ')}}</div></article>`
  ).join('');
}}
draw();
document.querySelector('#language').addEventListener('change',draw);
</script>
</body>
</html>
"""
