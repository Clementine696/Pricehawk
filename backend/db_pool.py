"""
Database Connection Pool for Async Operations

Provides asyncpg connection pool for alert service and other async database operations.
"""

import os
import asyncpg
import logging
from typing import Optional

logger = logging.getLogger(__name__)

_pool: Optional[asyncpg.Pool] = None


async def get_pool() -> asyncpg.Pool:
    """
    Get or create asyncpg connection pool
    
    Returns:
        asyncpg.Pool: Database connection pool
        
    Raises:
        ValueError: If DATABASE_URL is not set
        Exception: If connection fails
    """
    global _pool
    
    if _pool is not None:
        return _pool
    
    # Get database URL from environment
    database_url = os.getenv('DATABASE_URL')
    
    # If DATABASE_URL not set, construct from separate variables
    if not database_url:
        db_host = os.getenv('DB_HOST')
        db_port = os.getenv('DB_PORT', '5432')
        db_name = os.getenv('DB_NAME')
        db_user = os.getenv('DB_USER')
        db_password = os.getenv('DB_PASSWORD')
        
        if not all([db_host, db_name, db_user, db_password]):
            raise ValueError("DATABASE_URL or DB_HOST/DB_NAME/DB_USER/DB_PASSWORD environment variables must be set")
        
        database_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}?sslmode=require"
        logger.info("Constructed DATABASE_URL from separate DB variables")
    
    try:
        # Create connection pool
        logger.info(f"Creating database connection pool...")
        _pool = await asyncpg.create_pool(
            database_url,
            min_size=1,
            max_size=10,
            command_timeout=60
        )
        logger.info("Database connection pool created successfully")
        return _pool
        
    except Exception as e:
        logger.error(f"Failed to create database pool: {e}")
        raise


async def close_pool() -> None:
    """Close the database connection pool"""
    global _pool
    
    if _pool is not None:
        await _pool.close()
        _pool = None
        logger.info("Database connection pool closed")
