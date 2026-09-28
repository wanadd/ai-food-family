BEGIN;

-- Keep legacy keys and relationships stable while removing production identity.
UPDATE users
SET telegram_id = 900000000000000 + id,
    username = 'synthetic_user_' || id,
    first_name = 'Synthetic',
    last_name = 'User ' || id,
    phone_number = '+7999000' || lpad(id::text, 4, '0'),
    photo_url = NULL,
    blocked_reason = CASE WHEN blocked_reason IS NULL THEN NULL ELSE 'SYNTHETIC_BLOCK_REASON' END;

UPDATE families
SET name = 'Synthetic Family ' || id,
    blocked_reason = CASE WHEN blocked_reason IS NULL THEN NULL ELSE 'SYNTHETIC_BLOCK_REASON' END;

UPDATE family_members
SET display_name = 'Synthetic Member ' || id;

UPDATE family_invites
SET invited_phone_normalized = CASE WHEN invited_phone_normalized IS NULL THEN NULL ELSE '+79990009999' END,
    invite_token = NULL;

UPDATE admin_sessions
SET telegram_id = 900000100000000 + id,
    session_token = 'synthetic_session_' || id;

UPDATE admin_login_attempts
SET telegram_id = 900000150000000 + id;

UPDATE telegram_bot_sessions
SET telegram_id = 900000200000000 + row_number,
    invite_token = NULL,
    payload_json = '{}'::jsonb
FROM (SELECT ctid,
             row_number() OVER (ORDER BY telegram_id) AS row_number
      FROM telegram_bot_sessions) AS synthetic
WHERE telegram_bot_sessions.ctid = synthetic.ctid;

UPDATE user_profiles
SET favorite_foods = CASE WHEN coalesce(favorite_foods, '') = '' THEN favorite_foods ELSE 'SYNTHETIC_FAVORITE_FOOD' END,
    disliked_foods = CASE WHEN coalesce(disliked_foods, '') = '' THEN disliked_foods ELSE 'SYNTHETIC_DISLIKED_FOOD' END,
    medical_restrictions = CASE WHEN coalesce(medical_restrictions, '') = '' THEN medical_restrictions ELSE 'SYNTHETIC_AMBIGUOUS_MEDICAL_NOTE' END,
    banned_foods = CASE WHEN coalesce(banned_foods, '') = '' THEN banned_foods ELSE 'SYNTHETIC_BANNED_FOOD' END,
    allergies = CASE WHEN allergies IS NULL OR jsonb_array_length(allergies) = 0 THEN allergies ELSE '["SYNTHETIC_ALLERGEN_PRESENT"]'::jsonb END,
    restrictions = CASE WHEN restrictions IS NULL OR jsonb_array_length(restrictions) = 0 THEN restrictions ELSE '["SYNTHETIC_RESTRICTION_PRESENT"]'::jsonb END;

UPDATE event_plans
SET title = CASE WHEN title IS NULL THEN NULL ELSE 'Synthetic Event ' || id END,
    allergies_note = CASE WHEN coalesce(allergies_note, '') = '' THEN allergies_note ELSE 'SYNTHETIC_AMBIGUOUS_ALLERGY_NOTE' END;

UPDATE care_notifications
SET title = CASE WHEN title IS NULL THEN NULL ELSE 'Synthetic Notification' END,
    message = CASE WHEN coalesce(message, '') = '' THEN message ELSE 'SYNTHETIC_NOTIFICATION_MESSAGE' END,
    payload = NULL;

UPDATE admin_error_logs
SET message = CASE WHEN coalesce(message, '') = '' THEN message ELSE 'SYNTHETIC_ERROR_MESSAGE' END,
    stack = CASE WHEN coalesce(stack, '') = '' THEN stack ELSE 'SYNTHETIC_ERROR_STACK' END;

UPDATE external_food_logs
SET input_text = CASE WHEN input_text IS NULL THEN NULL ELSE 'SYNTHETIC_EXTERNAL_FOOD_INPUT' END,
    input_media_id = NULL,
    parsed_title = CASE WHEN parsed_title IS NULL THEN NULL ELSE 'Synthetic External Food' END;

UPDATE recipe_import_jobs
SET source_name = CASE WHEN source_name IS NULL THEN NULL ELSE 'synthetic_import_source' END,
    source_url = NULL;

UPDATE deferred_nutrition_advice
SET body = CASE WHEN coalesce(body, '') = '' THEN body ELSE 'SYNTHETIC_NUTRITION_ADVICE' END;

UPDATE collection_recipes SET note = CASE WHEN note IS NULL THEN NULL ELSE 'SYNTHETIC_COLLECTION_NOTE' END;
UPDATE cooking_batch_events SET note = CASE WHEN note IS NULL THEN NULL ELSE 'SYNTHETIC_COOKING_NOTE' END;
UPDATE family_pantry_items SET name = 'Synthetic Pantry Item ' || id, note = CASE WHEN note IS NULL THEN NULL ELSE 'SYNTHETIC_PANTRY_NOTE' END;
UPDATE family_recipe_preferences SET note = CASE WHEN note IS NULL THEN NULL ELSE 'SYNTHETIC_RECIPE_PREFERENCE_NOTE' END;
UPDATE meal_consumption_logs SET note = CASE WHEN note IS NULL THEN NULL ELSE 'SYNTHETIC_CONSUMPTION_NOTE' END;
UPDATE meal_leftovers SET dish_name = CASE WHEN dish_name IS NULL THEN NULL ELSE 'Synthetic Leftover ' || id END, note = CASE WHEN note IS NULL THEN NULL ELSE 'SYNTHETIC_LEFTOVER_NOTE' END;
UPDATE progress_entries SET notes = CASE WHEN notes IS NULL THEN NULL ELSE 'SYNTHETIC_PROGRESS_NOTE' END;
UPDATE recipe_history SET notes = CASE WHEN notes IS NULL THEN NULL ELSE 'SYNTHETIC_RECIPE_HISTORY_NOTE' END;
UPDATE recipe_ingredients SET notes = CASE WHEN notes IS NULL THEN NULL ELSE 'SYNTHETIC_INGREDIENT_NOTE' END;
UPDATE training_entries SET notes = CASE WHEN notes IS NULL THEN NULL ELSE 'SYNTHETIC_TRAINING_NOTE' END;

UPDATE cutover_runtime_audit SET details = CASE WHEN details IS NULL THEN NULL ELSE 'SYNTHETIC_RUNTIME_DETAIL' END;
UPDATE cutover_runtime_control SET reason = CASE WHEN reason IS NULL THEN NULL ELSE 'SYNTHETIC_RUNTIME_REASON' END;
UPDATE cutover_runtime_runs
SET backup_ref = CASE WHEN backup_ref IS NULL THEN NULL ELSE 'synthetic-backup-ref' END,
    migration_result = CASE WHEN migration_result IS NULL THEN NULL ELSE 'SYNTHETIC_MIGRATION_RESULT' END,
    reconciliation_result = CASE WHEN reconciliation_result IS NULL THEN NULL ELSE 'SYNTHETIC_RECONCILIATION_RESULT' END;
UPDATE cutover_runtime_transitions SET reason = CASE WHEN reason IS NULL THEN NULL ELSE 'SYNTHETIC_TRANSITION_REASON' END;

COMMIT;
