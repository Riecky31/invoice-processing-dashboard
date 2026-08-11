from app.db.database import test_connection


if __name__ == "__main__":
    result = test_connection()

    if result == 1:
        print("Database connection successful!")
    else:
        print(f"Unexpected database response: {result}")