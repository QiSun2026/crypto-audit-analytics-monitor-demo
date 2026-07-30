SELECT
    action.action_id,
    action.agent_id,
    action.action_type,
    action.payload_sha256,
    action.reversibility,
    action.executed_at_utc,
    action.approval_id,
    approval.approval_id AS matched_approval_id,
    approval.decision,
    approval.approved_payload_sha256,
    approval.valid_from_utc,
    approval.valid_to_utc,
    CASE
        WHEN approval.approval_id IS NULL
            THEN 'approval_evidence_missing'
        WHEN approval.decision <> 'approved'
            THEN 'approval_not_approved'
        WHEN approval.approved_payload_sha256 <> action.payload_sha256
            THEN 'approval_payload_mismatch'
        WHEN action.executed_at_utc < approval.valid_from_utc
            OR action.executed_at_utc > approval.valid_to_utc
            THEN 'approval_outside_valid_window'
    END AS signal_code
FROM agent_action AS action
LEFT JOIN action_approval AS approval
    ON approval.approval_id = action.approval_id
WHERE action.reversibility = 'irreversible'
  AND (
      approval.approval_id IS NULL
      OR approval.decision <> 'approved'
      OR approval.approved_payload_sha256 <> action.payload_sha256
      OR action.executed_at_utc < approval.valid_from_utc
      OR action.executed_at_utc > approval.valid_to_utc
  )
ORDER BY action.action_id;
