from sqlalchemy import text

from server.app.db.session import engine


def main() -> None:
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    print("db ok")


if __name__ == "__main__":
    main()
