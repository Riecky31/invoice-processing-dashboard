from app.db.database import create_tables
from app.email.outlook import scan_outlook_inbox


if __name__ == "__main__":
    create_tables()
    result = scan_outlook_inbox()
    print(result.to_dict())
