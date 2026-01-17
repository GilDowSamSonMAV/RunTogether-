"""
RAG Engine - Knowledge base using PostgreSQL pgvector and FastEmbed.

Provides document ingestion and semantic search for the study bot.
"""

import os
import logging
from typing import List, Optional
import psycopg2
from psycopg2.extras import execute_values
from fastembed import TextEmbedding

logger = logging.getLogger(__name__)

# Database connection
DATABASE_URL = os.getenv("DATABASE_URL")

# Embedding model (384 dimensions, runs on CPU)
embedding_model: Optional[TextEmbedding] = None


def get_embedding_model() -> TextEmbedding:
    """Lazy load embedding model."""
    global embedding_model
    if embedding_model is None:
        logger.info("Loading FastEmbed model...")
        embedding_model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
        logger.info("FastEmbed model loaded!")
    return embedding_model


def get_db_connection():
    """Get database connection."""
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL not set in environment")
    return psycopg2.connect(DATABASE_URL)


def init_db() -> None:
    """Initialize database with pgvector extension and knowledge_chunks table."""
    logger.info("Initializing RAG database...")
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Enable pgvector extension
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        
        # Create knowledge chunks table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS knowledge_chunks (
                id SERIAL PRIMARY KEY,
                content TEXT NOT NULL,
                embedding vector(384),
                source_file TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Create index for fast similarity search
        cur.execute("""
            CREATE INDEX IF NOT EXISTS knowledge_chunks_embedding_idx 
            ON knowledge_chunks 
            USING ivfflat (embedding vector_cosine_ops)
            WITH (lists = 100);
        """)
        
        conn.commit()
        logger.info("RAG database initialized successfully!")
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Database initialization error: {e}")
        raise
    finally:
        cur.close()
        conn.close()


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """Split text into overlapping chunks."""
    chunks = []
    start = 0
    text = text.strip()
    
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        
        # Try to break at sentence boundary
        if end < len(text):
            last_period = chunk.rfind('.')
            last_newline = chunk.rfind('\n')
            break_point = max(last_period, last_newline)
            if break_point > chunk_size // 2:
                chunk = chunk[:break_point + 1]
                end = start + break_point + 1
        
        if chunk.strip():
            chunks.append(chunk.strip())
        
        start = end - overlap
    
    return chunks


def add_document(text: str, source_file: str = "unknown") -> int:
    """
    Add a document to the knowledge base.
    
    Args:
        text: The document text to index
        source_file: Name of the source file
        
    Returns:
        Number of chunks added
    """
    if not text.strip():
        return 0
    
    # Split into chunks
    chunks = chunk_text(text)
    if not chunks:
        return 0
    
    logger.info(f"Adding {len(chunks)} chunks from {source_file}")
    
    # Generate embeddings
    model = get_embedding_model()
    embeddings = list(model.embed(chunks))
    
    # Store in database
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Prepare data for batch insert
        data = [
            (chunk, embedding.tolist(), source_file)
            for chunk, embedding in zip(chunks, embeddings)
        ]
        
        execute_values(
            cur,
            """
            INSERT INTO knowledge_chunks (content, embedding, source_file)
            VALUES %s
            """,
            data,
            template="(%s, %s::vector, %s)"
        )
        
        conn.commit()
        logger.info(f"Successfully added {len(chunks)} chunks to knowledge base")
        return len(chunks)
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Error adding document: {e}")
        raise
    finally:
        cur.close()
        conn.close()


def get_relevant_context(query: str, top_k: int = 3) -> List[dict]:
    """
    Retrieve relevant context for a query using semantic search.
    
    Args:
        query: The user's question
        top_k: Number of results to return
        
    Returns:
        List of relevant chunks with content and similarity score
    """
    if not query.strip():
        return []
    
    # Generate query embedding
    model = get_embedding_model()
    query_embedding = list(model.embed([query]))[0].tolist()
    
    # Search database
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute(
            """
            SELECT content, source_file, 1 - (embedding <=> %s::vector) as similarity
            FROM knowledge_chunks
            ORDER BY embedding <=> %s::vector
            LIMIT %s;
            """,
            (query_embedding, query_embedding, top_k)
        )
        
        results = []
        for row in cur.fetchall():
            results.append({
                "content": row[0],
                "source": row[1],
                "similarity": round(row[2], 3)
            })
        
        logger.info(f"Found {len(results)} relevant chunks for query")
        return results
        
    except Exception as e:
        logger.error(f"Error searching knowledge base: {e}")
        return []
    finally:
        cur.close()
        conn.close()


def get_context_string(query: str) -> str:
    """Get formatted context string for injection into prompts."""
    results = get_relevant_context(query)
    
    if not results:
        return ""
    
    context_parts = []
    for i, result in enumerate(results, 1):
        context_parts.append(
            f"[Source {i}: {result['source']}]\n{result['content']}"
        )
    
    return "\n\n---\n\n".join(context_parts)
