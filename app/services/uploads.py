from sqlalchemy import text

from app.db.database import engine


def get_upload_history():
    query = text(
        """
        SELECT
            u.id,
            u.filename,
            u.uploaded_at,
            u.rows_found,
            u.rows_inserted,
            u.duplicates_found,
            u.status,
            COUNT(i.id) AS invoice_count
        FROM uploads u
        LEFT JOIN invoices i
            ON i.upload_id = u.id
        GROUP BY
            u.id,
            u.filename,
            u.uploaded_at,
            u.rows_found,
            u.rows_inserted,
            u.duplicates_found,
            u.status
        ORDER BY u.uploaded_at DESC
        """
    )

    with engine.connect() as connection:
        result = connection.execute(query)

        return result.mappings().all()


def delete_upload(upload_id: int):
    query = text(
        """
        DELETE FROM uploads
        WHERE id = :upload_id
        RETURNING id, filename
        """
    )

    with engine.begin() as connection:
        result = connection.execute(
            query,
            {
                "upload_id": upload_id
            },
        )

        deleted = result.mappings().first()

        return deleted