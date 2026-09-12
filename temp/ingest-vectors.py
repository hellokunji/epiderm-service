#!/usr/bin/env python3
"""Embed mock clinical guidelines and insert them into clinical_rag.knowledge_base."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from urllib.parse import urlparse, unquote

import psycopg2
from dotenv import load_dotenv
from pgvector.psycopg2 import register_vector
from sentence_transformers import SentenceTransformer

from mock_clinical_data import MOCK_CLINICAL_GUIDELINES

DEFAULT_DATABASE_URL = "postgresql+psycopg2://epiderm:epiderm@localhost:5432/clinic"
REPO_ROOT = Path(__file__).resolve().parents[1]


def parse_database_url(url: str) -> dict[str, str]:
    parsed = urlparse(url.replace("postgresql+psycopg2://", "postgresql://", 1))
    if parsed.scheme not in {"postgresql", "postgres"}:
        raise ValueError(f"Unsupported DATABASE_URL scheme: {parsed.scheme}")
    if not parsed.hostname or not parsed.path.lstrip("/"):
        raise ValueError("DATABASE_URL must include host and database name")
    return {
        "dbname": parsed.path.lstrip("/"),
        "user": unquote(parsed.username or ""),
        "password": unquote(parsed.password or ""),
        "host": parsed.hostname,
        "port": str(parsed.port or 5432),
    }


def require_knowledge_base(cursor) -> None:
    cursor.execute("SELECT extname FROM pg_extension WHERE extname = 'vector'")
    if cursor.fetchone() is None:
        raise SystemExit(
            "pgvector is not installed. Use image pgvector/pgvector:pg16 and run temp/schema.sql."
        )
    cursor.execute(
        """
        SELECT 1
        FROM information_schema.tables
        WHERE table_schema = 'clinical_rag' AND table_name = 'knowledge_base'
        """
    )
    if cursor.fetchone() is None:
        raise SystemExit(
            "Missing clinical_rag.knowledge_base. Apply temp/schema.sql first."
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--replace",
        action="store_true",
        help="Delete existing knowledge_base rows before insert.",
    )
    args = parser.parse_args()

    load_dotenv(REPO_ROOT / ".env")
    db_params = parse_database_url(os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL))

    print("Loading embedding model BAAI/bge-small-en-v1.5 (~130MB)...")
    embedder = SentenceTransformer("BAAI/bge-small-en-v1.5")

    conn = psycopg2.connect(**db_params)
    cursor = conn.cursor()
    try:
        require_knowledge_base(cursor)
        register_vector(conn)

        if args.replace:
            cursor.execute("DELETE FROM clinical_rag.knowledge_base")
            print("Cleared clinical_rag.knowledge_base")

        print(f"Ingesting {len(MOCK_CLINICAL_GUIDELINES)} mock clinical guidelines...")
        for item in MOCK_CLINICAL_GUIDELINES:
            embedding = embedder.encode(item["document_text"]).tolist()
            if len(embedding) != 384:
                raise SystemExit(
                    f"Expected 384-d embedding, got {len(embedding)} for {item['condition_name']}"
                )
            cursor.execute(
                """
                INSERT INTO clinical_rag.knowledge_base
                    (category, sub_category, condition_name, document_text, metadata, embedding)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    item["category"],
                    item["sub_category"],
                    item["condition_name"],
                    item["document_text"],
                    json.dumps(item["metadata"]),
                    embedding,
                ),
            )

        conn.commit()
        print(f"Ingestion completed. Inserted {len(MOCK_CLINICAL_GUIDELINES)} rows.")
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
