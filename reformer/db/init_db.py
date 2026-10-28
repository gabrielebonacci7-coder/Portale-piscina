"""Crea le tabelle se mancano.

    python -m reformer.db.init_db
"""

from sqlalchemy import text

from reformer.db.base import Base
from reformer.db.session import engine
import reformer.models  # noqa: F401 - registra le tabelle


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    # Le lezioni si chiamavano "Reformer": ora il nome base è "Pilates".
    with engine.begin() as conn:
        conn.execute(text("UPDATE lezioni SET titolo = 'Pilates' WHERE titolo = 'Reformer'"))
        conn.execute(text("UPDATE titoli_fissi SET titolo = 'Pilates' WHERE titolo = 'Reformer'"))


if __name__ == "__main__":
    init_db()
    print("Tabelle pronte.")
