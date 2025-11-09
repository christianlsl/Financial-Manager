import os
from datetime import timedelta


class Settings:
    SECRET_KEY: str = os.getenv("FM_SECRET_KEY", "change-this-in-production-super-secret-key")
    JWT_ALGORITHM: str = os.getenv("FM_JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("FM_ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
    # When remaining lifetime is below this threshold, issue a new token automatically
    REFRESH_THRESHOLD_MINUTES: int = int(os.getenv("FM_REFRESH_THRESHOLD_MINUTES", "10"))

    # SQLite database placed at project root by default
    SQLITE_DB_PATH: str = os.getenv("FM_SQLITE_DB", os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "financial_manager.db")))

    @property
    def ACCESS_TOKEN_EXPIRE_DELTA(self) -> timedelta:
        return timedelta(minutes=self.ACCESS_TOKEN_EXPIRE_MINUTES)

    @property
    def REFRESH_THRESHOLD_DELTA(self) -> timedelta:
        return timedelta(minutes=self.REFRESH_THRESHOLD_MINUTES)


settings = Settings()
