-- 앱에서 사용할 수 있는 활성 정책 목록
SELECT policy_id, name, category, rule_mode, verified_at
FROM policies
WHERE is_active = 1
ORDER BY category, name;

-- 정책 카테고리별 개수
SELECT category, COUNT(*) AS policy_count
FROM policies
WHERE is_active = 1
GROUP BY category
ORDER BY policy_count DESC, category;

-- 최근 분석 로그(데모 DB에 로그가 있을 때 사용)
SELECT id, session_id, region_code, risk_class, affordability_ratio, created_at
FROM analysis_runs
ORDER BY created_at DESC
LIMIT 10;
