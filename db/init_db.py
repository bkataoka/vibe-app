import aiosqlite
import logging
from pathlib import Path

from core.config import settings
from db.base import init_db

logger = logging.getLogger(__name__)


async def init_sqlite() -> None:
    """Initialize SQLite database with optimal settings."""
    # Extract database path from URL
    db_path = settings.SQLITE_URL.replace("sqlite+aiosqlite:///", "")
    
    # Create database directory if it doesn't exist
    db_dir = Path(db_path).parent
    db_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        async with aiosqlite.connect(db_path) as db:
            # Enable Write-Ahead Logging for better concurrency
            await db.execute(f"PRAGMA journal_mode = {settings.DB_JOURNAL_MODE}")
            
            # Set synchronous mode for balance of safety and speed
            await db.execute(f"PRAGMA synchronous = {settings.DB_SYNCHRONOUS}")
            
            # Store temp tables and indices in memory
            await db.execute(f"PRAGMA temp_store = {settings.DB_TEMP_STORE}")
            
            # Set memory-mapped I/O size
            await db.execute(f"PRAGMA mmap_size = {settings.DB_MMAP_SIZE}")
            
            # Other performance optimizations
            await db.execute("PRAGMA cache_size = -2000")  # 2MB page cache
            await db.execute("PRAGMA page_size = 4096")    # 4KB pages
            await db.execute("PRAGMA busy_timeout = 5000")  # 5 second timeout
            await db.execute("PRAGMA foreign_keys = ON")    # Enable foreign key constraints
            
            await db.commit()
            
            # Verify settings
            async with db.execute("PRAGMA journal_mode") as cursor:
                journal_mode = await cursor.fetchone()
                logger.info(f"SQLite journal_mode: {journal_mode[0]}")
            
            async with db.execute("PRAGMA synchronous") as cursor:
                synchronous = await cursor.fetchone()
                logger.info(f"SQLite synchronous: {synchronous[0]}")
            
    except Exception as e:
        logger.error(f"Error initializing SQLite: {e}")
        raise


async def init() -> None:
    """Initialize database."""
    try:
        # Initialize SQLite with optimal settings
        await init_sqlite()
        
        # Create all tables
        await init_db()
        
        logger.info("Database initialized successfully")
        
    except Exception as e:
        logger.error(f"Error during database initialization: {e}")
        raise 