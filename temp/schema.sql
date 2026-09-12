CREATE EXTENSION IF NOT EXISTS vector;
CREATE SCHEMA IF NOT EXISTS clinical_rag;

CREATE TABLE IF NOT EXISTS clinical_rag.knowledge_base (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    category VARCHAR(20) NOT NULL CHECK (category IN ('SKIN', 'HAIR')),
    sub_category VARCHAR(50),
    condition_name VARCHAR(100) NOT NULL,
    document_text TEXT NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    embedding VECTOR(384),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
