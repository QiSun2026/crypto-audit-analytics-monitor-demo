from __future__ import annotations

from pathlib import Path

from .agent_action_example import run_agent_action_case
from .engine import run_demo
from .renderer import render_html
from .review_log import append_review_record, read_review_log
from .showcase import render_agent_action_case, render_showcase


def seed_worked_reviews(result: dict) -> list[dict]:
    output_dir = Path(result["output_dir"])
    review_path = output_dir / "review_log.jsonl"
    queue_path = output_dir / "exception_queue.json"
    existing = read_review_log(review_path)
    if existing:
        return existing

    exceptions = result["exceptions"]
    shared_wallet = next(
        item for item in exceptions if item.get("wallet_id") == "W_CASE_A1"
    )
    false_positive = next(
        item for item in exceptions if item.get("affiliate_id") == "A0104"
    )
    corrected_case = next(
        item for item in exceptions if item.get("affiliate_id") == "A0100"
    )

    records = [
        {
            "exception_id": shared_wallet["exception_id"],
            "run_id": shared_wallet["run_id"],
            "snapshot_id": shared_wallet["snapshot_id"],
            "reviewer_id": "portfolio-reviewer-1",
            "review_timestamp_utc": "2026-07-30T13:00:00Z",
            "question_presented": (
                "Is the shared self-custody beneficiary relationship "
                "documented and authorized?"
            ),
            "question_presented_zh": "该共享自托管受益人关系是否有记录并获授权？",
            "conclusion": "control_exception_confirmed",
            "disposition": "escalate_for_investigation",
            "rationale": (
                "The fabricated source rows contain no documented reason for "
                "the shared self-custody wallet. Escalation requests supporting "
                "evidence; it is not a misconduct finding."
            ),
            "rationale_zh": (
                "编造的源数据行没有记录共享自托管钱包的原因。升级仅为索取支持证据，"
                "不构成行为不当结论。"
            ),
            "evidence_viewed": shared_wallet["source_row_ids"],
            "identity_status": "self_attested_prototype",
            "ai_assistance_used": False,
            "supersedes_review_id": None,
        },
        {
            "exception_id": false_positive["exception_id"],
            "run_id": false_positive["run_id"],
            "snapshot_id": false_positive["snapshot_id"],
            "reviewer_id": "portfolio-reviewer-1",
            "review_timestamp_utc": "2026-07-30T13:15:00Z",
            "question_presented": (
                "Do the split-payment rows represent a duplicate entitlement?"
            ),
            "question_presented_zh": "这些拆分付款是否代表重复权益？",
            "conclusion": "supported_explanation",
            "disposition": "close_with_explanation",
            "rationale": (
                "The fabricated rows carry distinct source references and no "
                "duplicate transaction. This designed false positive is closed "
                "without changing the provisional threshold."
            ),
            "rationale_zh": (
                "编造的数据行具有不同来源引用，且不存在重复交易。该设计误报在不修改"
                "暂定阈值的情况下关闭。"
            ),
            "evidence_viewed": false_positive["source_row_ids"],
            "identity_status": "self_attested_prototype",
            "ai_assistance_used": False,
            "supersedes_review_id": None,
        },
        {
            "exception_id": corrected_case["exception_id"],
            "run_id": corrected_case["run_id"],
            "snapshot_id": corrected_case["snapshot_id"],
            "reviewer_id": "portfolio-reviewer-1",
            "review_timestamp_utc": "2026-07-30T13:30:00Z",
            "question_presented": (
                "Do the two commission rows settle the same entitlement?"
            ),
            "question_presented_zh": "两条佣金记录是否结算同一项权益？",
            "conclusion": "more_evidence_required",
            "disposition": "keep_open",
            "rationale": (
                "The first pass kept the case open pending a comparison of "
                "source references."
            ),
            "rationale_zh": "首次复核保持案件开放，等待比较来源引用。",
            "evidence_viewed": corrected_case["source_row_ids"],
            "identity_status": "self_attested_prototype",
            "ai_assistance_used": False,
            "supersedes_review_id": None,
        },
    ]
    appended = [
        append_review_record(review_path, record, queue_path)
        for record in records
    ]
    correction = dict(records[-1])
    correction.update(
        {
            "review_timestamp_utc": "2026-07-30T13:45:00Z",
            "conclusion": "control_exception_confirmed",
            "disposition": "escalate_for_investigation",
            "rationale": (
                "Correction: both fabricated payments reuse the same source "
                "reference. The earlier keep-open record remains in the chain."
            ),
            "rationale_zh": (
                "更正：两笔编造付款重复使用同一来源引用。先前的保持开放记录继续保留"
                "在审计链中。"
            ),
            "supersedes_review_id": appended[-1]["review_id"],
        }
    )
    appended.append(append_review_record(review_path, correction, queue_path))
    return read_review_log(review_path)


def main() -> None:
    result = run_demo()
    reviews = seed_worked_reviews(result)
    root = Path(__file__).resolve().parents[2]
    demo_dir = root / "demo"
    demo_dir.mkdir(parents=True, exist_ok=True)
    commission_demo = demo_dir / "commission_case.html"
    commission_demo.write_text(
        render_html(
            result["run_manifest"],
            result["exceptions"],
            result["comparison"],
            reviews,
            back_href="index.html",
        ),
        encoding="utf-8",
        newline="\n",
    )
    agent_result = run_agent_action_case(
        root / "outputs" / "agent_action_case_policy_v2"
    )
    agent_demo = demo_dir / "agent_action_case.html"
    agent_demo.write_text(
        render_agent_action_case(
            agent_result["run_manifest"],
            agent_result["exceptions"],
            agent_result["context_items"],
            back_href="index.html",
        ),
        encoding="utf-8",
        newline="\n",
    )
    showcase_demo = demo_dir / "index.html"
    showcase_demo.write_text(
        render_showcase(),
        encoding="utf-8",
        newline="\n",
    )
    counts = result["run_manifest"]["routing_counts"]
    print(f"Demo: {result['output_dir']}")
    print(
        "Results: "
        f"{counts['assertion_hits']} assertion hits, "
        f"{counts['review_cases']} unique review cases, "
        f"{counts['context_items']} expected-shared context items"
    )
    print(f"Worked review records: {len(reviews)} across 3 cases")
    print("Automated action: none; human review required")
    print(f"Showcase HTML: {showcase_demo}")
    print(f"Commission case: {commission_demo}")
    print(f"Agent action case: {agent_demo}")


if __name__ == "__main__":
    main()
