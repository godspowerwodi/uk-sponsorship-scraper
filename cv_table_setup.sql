CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS temp_cvs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cv_text TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

SELECT cron.schedule(
    'delete_old_cvs',
    '0 * * * *',
    $$ DELETE FROM temp_cvs WHERE created_at < NOW() - INTERVAL '24 hours' $$
);
