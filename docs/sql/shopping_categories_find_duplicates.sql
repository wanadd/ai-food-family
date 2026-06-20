-- Production audit: global duplicate names (may span users OR repeat per user)
SELECT name, is_system, COUNT(*) AS cnt
FROM shopping_categories
GROUP BY name, is_system
HAVING COUNT(*) > 1
ORDER BY cnt DESC, name;

-- Per-user system duplicates (same name — root cause of MultipleResultsFound)
SELECT user_id, name, COUNT(*) AS cnt, ARRAY_AGG(id ORDER BY id) AS ids
FROM shopping_categories
WHERE is_system = TRUE AND user_id IS NOT NULL
GROUP BY user_id, name
HAVING COUNT(*) > 1
ORDER BY cnt DESC, user_id, name;

-- Per-user system duplicates (same slug)
SELECT user_id, slug, COUNT(*) AS cnt, ARRAY_AGG(id ORDER BY id) AS ids
FROM shopping_categories
WHERE is_system = TRUE AND user_id IS NOT NULL
GROUP BY user_id, slug
HAVING COUNT(*) > 1
ORDER BY cnt DESC, user_id, slug;

-- Per-family system duplicates (same name)
SELECT family_id, name, COUNT(*) AS cnt, ARRAY_AGG(id ORDER BY id) AS ids
FROM shopping_categories
WHERE is_system = TRUE AND family_id IS NOT NULL
GROUP BY family_id, name
HAVING COUNT(*) > 1
ORDER BY cnt DESC, family_id, name;

-- Cleanup preview: rows that would be deleted (keep MIN(id) per user+name)
SELECT sc.id, sc.user_id, sc.name, sc.slug
FROM shopping_categories sc
JOIN (
    SELECT user_id, name, MIN(id) AS keep_id
    FROM shopping_categories
    WHERE is_system = TRUE AND user_id IS NOT NULL
    GROUP BY user_id, name
    HAVING COUNT(*) > 1
) dup ON dup.user_id = sc.user_id AND dup.name = sc.name
WHERE sc.is_system = TRUE AND sc.id <> dup.keep_id
ORDER BY sc.user_id, sc.name, sc.id;

-- Note: family_shopping_lists.items stores category slug in JSONB, not shopping_categories.id.
-- No FK reassignment is required when deleting duplicate category rows.
