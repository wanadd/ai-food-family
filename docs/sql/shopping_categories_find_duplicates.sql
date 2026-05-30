-- Find duplicate system shopping categories (personal scope)
SELECT user_id, slug, COUNT(*) AS cnt, ARRAY_AGG(id ORDER BY id) AS ids
FROM shopping_categories
WHERE is_system = TRUE AND user_id IS NOT NULL
GROUP BY user_id, slug
HAVING COUNT(*) > 1
ORDER BY cnt DESC, user_id, slug;

-- Find duplicate system shopping categories (family scope)
SELECT family_id, slug, COUNT(*) AS cnt, ARRAY_AGG(id ORDER BY id) AS ids
FROM shopping_categories
WHERE is_system = TRUE AND family_id IS NOT NULL
GROUP BY family_id, slug
HAVING COUNT(*) > 1
ORDER BY cnt DESC, family_id, slug;

-- Find duplicate user-created categories (personal scope)
SELECT user_id, slug, COUNT(*) AS cnt, ARRAY_AGG(id ORDER BY id) AS ids
FROM shopping_categories
WHERE is_system = FALSE AND user_id IS NOT NULL
GROUP BY user_id, slug
HAVING COUNT(*) > 1
ORDER BY cnt DESC, user_id, slug;

-- Find duplicate user-created categories (family scope)
SELECT family_id, slug, COUNT(*) AS cnt, ARRAY_AGG(id ORDER BY id) AS ids
FROM shopping_categories
WHERE is_system = FALSE AND family_id IS NOT NULL
GROUP BY family_id, slug
HAVING COUNT(*) > 1
ORDER BY cnt DESC, family_id, slug;
