"""Crea le tabelle se mancano.

    python -m reformer.db.init_db
"""

from reformer.db.base import Base
from reformer.db.session import engine
import reformer.models  # noqa: F401 - registra le tabelle


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    init_db()
    print("Tabelle pronte.")
