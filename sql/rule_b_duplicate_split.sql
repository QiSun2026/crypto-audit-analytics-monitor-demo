WITH completed AS (
    SELECT *
    FROM commission_payment
    WHERE payment_status = 'completed'
      AND (
          :scope = 'population'
          OR EXISTS (
              SELECT 1 FROM sample_affiliate s
              WHERE s.affiliate_id = commission_payment.affiliate_id
          )
      )
),
source_reference_pairs AS (
    SELECT
        'B1' AS rule_branch,
        'potential_exception' AS bucket,
        'high' AS severity,
        CASE
            WHEN p1.affiliate_id = p2.affiliate_id THEN p1.affiliate_id
            ELSE p1.affiliate_id || ' / ' || p2.affiliate_id
        END AS affiliate_id,
        p1.affiliate_id AS affiliate_id_a,
        p2.affiliate_id AS affiliate_id_b,
        CASE
            WHEN p1.accrual_period = p2.accrual_period THEN p1.accrual_period
            ELSE p1.accrual_period || ' / ' || p2.accrual_period
        END AS accrual_period,
        p1.payment_id AS payment_id_a,
        p2.payment_id AS payment_id_b,
        p1.source_ref AS source_ref_a,
        p2.source_ref AS source_ref_b,
        p1.amount_minor AS amount_minor_a,
        p2.amount_minor AS amount_minor_b,
        p1.payment_id || '|' || p2.payment_id AS source_row_ids
    FROM completed p1
    JOIN completed p2
      ON p1.payment_id < p2.payment_id
     AND p1.source_ref = p2.source_ref
),
repeated_amount_pairs AS (
    SELECT
        'B1' AS rule_branch,
        'potential_exception' AS bucket,
        'high' AS severity,
        p1.affiliate_id AS affiliate_id,
        p1.affiliate_id AS affiliate_id_a,
        p2.affiliate_id AS affiliate_id_b,
        p1.accrual_period AS accrual_period,
        p1.payment_id AS payment_id_a,
        p2.payment_id AS payment_id_b,
        p1.source_ref AS source_ref_a,
        p2.source_ref AS source_ref_b,
        p1.amount_minor AS amount_minor_a,
        p2.amount_minor AS amount_minor_b,
        p1.payment_id || '|' || p2.payment_id AS source_row_ids
    FROM completed p1
    JOIN completed p2
      ON p1.payment_id < p2.payment_id
     AND p1.affiliate_id = p2.affiliate_id
     AND p1.accrual_period = p2.accrual_period
     AND p1.amount_minor = p2.amount_minor
     AND p1.source_ref <> p2.source_ref
),
duplicate_pairs AS (
    SELECT * FROM source_reference_pairs
    UNION ALL
    SELECT * FROM repeated_amount_pairs
),
anchor_dates AS (
    SELECT DISTINCT affiliate_id, accrual_period, payment_date
    FROM completed
    WHERE amount_minor < :review_threshold_minor
),
split_windows AS (
    SELECT
        anchor.affiliate_id,
        anchor.accrual_period,
        anchor.payment_date AS first_payment_date,
        MAX(candidate.payment_date) AS last_payment_date,
        COUNT(*) AS payment_count,
        SUM(candidate.amount_minor) AS total_amount_minor,
        GROUP_CONCAT(candidate.payment_id, '|') AS source_row_ids
    FROM anchor_dates anchor
    JOIN completed candidate
      ON candidate.affiliate_id = anchor.affiliate_id
     AND candidate.accrual_period = anchor.accrual_period
     AND date(candidate.payment_date) >= date(anchor.payment_date)
     AND date(candidate.payment_date) <= date(anchor.payment_date, '+' || :window_days || ' day')
    WHERE candidate.amount_minor < :review_threshold_minor
    GROUP BY anchor.affiliate_id, anchor.accrual_period, anchor.payment_date
    HAVING COUNT(*) >= 2
       AND SUM(candidate.amount_minor) >= :review_threshold_minor
),
ranked_windows AS (
    SELECT
        'B2' AS rule_branch,
        'potential_exception' AS bucket,
        'medium' AS severity,
        affiliate_id,
        affiliate_id AS affiliate_id_a,
        affiliate_id AS affiliate_id_b,
        accrual_period,
        COUNT(*) OVER (
            PARTITION BY affiliate_id, accrual_period
        ) AS qualifying_window_count,
        payment_count,
        total_amount_minor,
        first_payment_date,
        last_payment_date,
        source_row_ids,
        ROW_NUMBER() OVER (
            PARTITION BY affiliate_id, accrual_period
            ORDER BY first_payment_date, source_row_ids
        ) AS canonical_window_rank
    FROM split_windows
)
SELECT
    rule_branch,
    bucket,
    severity,
    affiliate_id,
    affiliate_id_a,
    affiliate_id_b,
    accrual_period,
    payment_id_a,
    payment_id_b,
    source_ref_a,
    source_ref_b,
    amount_minor_a,
    amount_minor_b,
    NULL AS payment_count,
    NULL AS qualifying_window_count,
    NULL AS total_amount_minor,
    NULL AS first_payment_date,
    NULL AS last_payment_date,
    source_row_ids
FROM duplicate_pairs
UNION ALL
SELECT
    rule_branch,
    bucket,
    severity,
    affiliate_id,
    affiliate_id_a,
    affiliate_id_b,
    accrual_period,
    NULL AS payment_id_a,
    NULL AS payment_id_b,
    NULL AS source_ref_a,
    NULL AS source_ref_b,
    NULL AS amount_minor_a,
    NULL AS amount_minor_b,
    payment_count,
    qualifying_window_count,
    total_amount_minor,
    first_payment_date,
    last_payment_date,
    source_row_ids
FROM ranked_windows
WHERE canonical_window_rank = 1
ORDER BY rule_branch, affiliate_id, accrual_period, source_row_ids;
