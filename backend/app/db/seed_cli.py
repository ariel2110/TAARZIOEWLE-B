from app.db.session import SessionLocal
from app.db.seed import seed_demo_data


def main() -> None:
    db = SessionLocal()
    try:
        seed_demo_data(db)
        print('Demo data seeded.')
    finally:
        db.close()


if __name__ == '__main__':
    main()
