from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import EmailStr, SecretStr


class Settings(BaseSettings):
    """Application settings."""
    
    # Base
    PROJECT_NAME: str = "Agentic AI Panel"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    
    # Security
    SECRET_KEY: str = "your-secret-key-here"  # Change in production
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Database
    SQLITE_URL: str = "sqlite+aiosqlite:///./agentic_ai.db"
    DB_ECHO: bool = False  # Set to True to log all SQL queries
    DB_POOL_SIZE: int = 5  # Maximum number of database connections
    DB_MAX_OVERFLOW: int = 10  # Maximum number of connections above pool_size
    DB_POOL_RECYCLE: int = 3600  # Recycle connections after 1 hour
    DB_TIMEOUT: int = 30  # Connection timeout in seconds
    DB_JOURNAL_MODE: str = "WAL"  # Write-Ahead Logging for better concurrency
    DB_SYNCHRONOUS: str = "NORMAL"  # NORMAL provides good balance of safety and speed
    DB_TEMP_STORE: str = "MEMORY"  # Store temporary tables and indices in memory
    DB_MMAP_SIZE: int = 268435456  # 256MB memory-mapped I/O
    
    # CORS
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:8000"]
    
    # First Superuser
    FIRST_SUPERUSER: EmailStr = "admin@example.com"
    FIRST_SUPERUSER_PASSWORD: SecretStr = SecretStr("admin")  # Change in production
    
    # Toolhouse
    TOOLHOUSE_API_KEY: Optional[str] = None
    TOOLHOUSE_BASE_URL: str = "https://api.toolhouse.ai"  # Replace with actual URL

    class Config:
        case_sensitive = True
        env_file = ".env"


settings = Settings() 