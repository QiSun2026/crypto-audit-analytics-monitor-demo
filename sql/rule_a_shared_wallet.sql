WITH candidate_pairs AS (
    SELECT
        w.wallet_id,
        w.wallet_type,
        l1.link_id AS source_row_a,
        l1.entity_type AS entity_a_type,
        l1.entity_id AS entity_a_id,
        l2.link_id AS source_row_b,
        l2.entity_type AS entity_b_type,
        l2.entity_id AS entity_b_id
    FROM entity_wallet_link l1
    JOIN entity_wallet_link l2
      ON l1.wallet_id = l2.wallet_id
     AND l1.link_id < l2.link_id
     AND NOT (
         l1.entity_type = l2.entity_type
         AND l1.entity_id = l2.entity_id
     )
     AND date(l1.valid_from) <= date(COALESCE(l2.valid_to, '9999-12-31'))
     AND date(l2.valid_from) <= date(COALESCE(l1.valid_to, '9999-12-31'))
    JOIN payout_wallet w ON w.wallet_id = l1.wallet_id
    WHERE (
        :scope = 'population'
        OR (
            (
                l1.entity_type = 'affiliate'
                AND EXISTS (
                    SELECT 1 FROM sample_affiliate s
                    WHERE s.affiliate_id = l1.entity_id
                )
            )
            OR
            (
                l2.entity_type = 'affiliate'
                AND EXISTS (
                    SELECT 1 FROM sample_affiliate s
                    WHERE s.affiliate_id = l2.entity_id
                )
            )
        )
    )
)
SELECT
    'A' AS rule_branch,
    CASE
        WHEN wallet_type = 'self_custody' THEN 'potential_exception'
        WHEN wallet_type IN ('exchange_deposit', 'internal_treasury')
        THEN 'expected_shared'
        ELSE 'data_quality_block'
    END AS bucket,
    CASE
        WHEN MAX(
            CASE
                WHEN entity_a_type = 'employee' OR entity_b_type = 'employee'
                THEN 1 ELSE 0
            END
        ) = 1 THEN 'high'
        ELSE 'medium'
    END AS severity,
    wallet_id,
    wallet_type,
    COUNT(*) AS overlapping_pair_count,
    GROUP_CONCAT(source_row_a || '|' || source_row_b, '|') AS source_row_ids
FROM candidate_pairs
GROUP BY wallet_id, wallet_type
ORDER BY wallet_id;
