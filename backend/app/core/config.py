import os
from datetime import timedelta
from typing import Any, Dict, List
import yaml  # type: ignore


def _load_yaml_config() -> Dict[str, Any]:
    """Load YAML config strictly from the fixed path (no env overrides).

    Path: backend/config.yaml (two levels up from this file). If the file is
    missing or invalid, return an empty dict so we can fall back to hardcoded
    defaults below. We intentionally avoid any os.getenv usage per requirement.
    """
    config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "config.yaml"))
    data: Dict[str, Any] = {}
    if yaml and os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                loaded = yaml.safe_load(f) or {}
                if isinstance(loaded, dict):
                    data = loaded
        except Exception:
            data = {}
    return data


class Settings:
    def __init__(self) -> None:
        cfg = _load_yaml_config()

        app_cfg = cfg.get("backend", {}) if isinstance(cfg.get("backend", {}), dict) else {}
        self.SECRET_KEY: str = str(app_cfg.get("secret_key", "change-this-in-production-super-secret-key"))
        self.JWT_ALGORITHM: str = str(app_cfg.get("jwt_algorithm", "HS256"))
        self.ACCESS_TOKEN_EXPIRE_MINUTES: int = int(app_cfg.get("access_token_expire_minutes", 60))
        self.REFRESH_THRESHOLD_MINUTES: int = int(app_cfg.get("refresh_threshold_minutes", 10))

        # Database settings
        db_cfg = cfg.get("database", {}) if isinstance(cfg.get("database", {}), dict) else {}
        raw_db_path = db_cfg.get("sqlite_db_path")
        repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
        if not raw_db_path:
            raw_db_path = os.path.join(repo_root, "backend", "financial_manager.db")
        else:
            raw_db_path = str(raw_db_path)
            if not os.path.isabs(raw_db_path):
                raw_db_path = os.path.abspath(os.path.join(repo_root, raw_db_path))
        self.SQLITE_DB_PATH: str = raw_db_path

        # Frontend/CORS settings
        fe_cfg = cfg.get("frontend", {}) if isinstance(cfg.get("frontend", {}), dict) else {}
        origins = fe_cfg.get("origins")  
        if isinstance(origins, str):
            self.FRONTEND_ORIGINS: List[str] = [origins]
        elif isinstance(origins, list):
            self.FRONTEND_ORIGINS = [str(x) for x in origins]

        # Server (uvicorn) settings 
        srv_cfg = cfg.get("server", {}) if isinstance(cfg.get("server", {}), dict) else {}
        self.SERVER_HOST: str = str(srv_cfg.get("host", "0.0.0.0"))
        self.SERVER_PORT: int = int(srv_cfg.get("port", 8000))

        uploads_cfg = cfg.get("uploads", {}) if isinstance(cfg.get("uploads", {}), dict) else {}
        self.UPLOAD_MAX_SIZE_KB: int = int(uploads_cfg.get("max_size_kb", 500))
        self.UPLOAD_MAX_SIZE_BYTES: int = max(1, self.UPLOAD_MAX_SIZE_KB) * 1024
        qiniu_cfg = uploads_cfg.get("qiniu", {}) if isinstance(uploads_cfg.get("qiniu", {}), dict) else {}
        self.QINIU_ACCESS_KEY: str = str(qiniu_cfg.get("access_key", "")).strip()
        self.QINIU_SECRET_KEY: str = str(qiniu_cfg.get("secret_key", "")).strip()
        self.QINIU_BUCKET: str = str(qiniu_cfg.get("bucket", "")).strip()
        self.QINIU_DOMAIN: str = str(qiniu_cfg.get("domain", "")).strip().rstrip("/")
        base_path = str(qiniu_cfg.get("base_path", "sales-images")).strip().strip("/")
        self.QINIU_BASE_PATH: str = base_path or "sales-images"

    @property
    def ACCESS_TOKEN_EXPIRE_DELTA(self) -> timedelta:
        return timedelta(minutes=self.ACCESS_TOKEN_EXPIRE_MINUTES)

    @property
    def REFRESH_THRESHOLD_DELTA(self) -> timedelta:
        return timedelta(minutes=self.REFRESH_THRESHOLD_MINUTES)


settings = Settings()
