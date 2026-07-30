PRAGMA foreign_key_check;

SELECT COUNT(*) = 17 AS ok
FROM regions;

SELECT COUNT(*) >= 5 AS ok
FROM policies
WHERE is_active = 1;

SELECT COUNT(*) = 0 AS ok
FROM regions
WHERE demo_cost_index <= 0;

SELECT COUNT(*) = 0 AS ok
FROM policies
WHERE official_url NOT LIKE 'https://%';

SELECT COUNT(*) = 0 AS ok
FROM policies
WHERE rule_mode NOT IN ('screening', 'discovery');
