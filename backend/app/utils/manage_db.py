import os
import stat

from ..core.config import settings
from ..db import Base, engine

# Import models so they are registered with Base metadata
from ..models import company  # noqa: F401
from ..models import user  # noqa: F401
from ..models import purchase  # noqa: F401
from ..models import sale  # noqa: F401
from ..models import type  # noqa: F401


def reset_sqlite_db() -> None:
    db_path = settings.SQLITE_DB_PATH

    if os.path.exists(db_path):
        os.remove(db_path)
    Base.metadata.create_all(bind=engine)
    os.chmod(db_path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IWGRP)

if __name__ == "__main__":
    reset_sqlite_db()
    print("Database reset and initialized.")
