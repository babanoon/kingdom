CREATE TABLE IF NOT EXISTS n8n_testChat_histories (
  id          BIGSERIAL PRIMARY KEY,
  session_id  TEXT        NOT NULL,            -- tie all turns of one chat
  sender      TEXT        NOT NULL,            -- 'user' | 'assistant' | 'system'
  message     TEXT        NOT NULL,            -- the text content
  meta        JSONB       NOT NULL DEFAULT '{}'::jsonb,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS n8n_testChat_histories
  ON n8n_testChat_histories (session_id, created_at DESC);