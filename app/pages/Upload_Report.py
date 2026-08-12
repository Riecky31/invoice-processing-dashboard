import tempfile
from pathlib import Path

import streamlit as st

from app.ui import (
    configure_page,
    sidebar_header,
)

from app.services.invoice_importer import (
    import_weekly_report,
)


configure_page("Upload Weekly Report")

sidebar_header()

st.title("📤 Upload Weekly Report")

st.write(
    "Upload the weekly Excel report to append new "
    "invoices to the central database."
)


uploaded_file = st.file_uploader(
    "Choose Excel report",
    type=["xlsx", "xls"],
)


if uploaded_file:

    st.info(
        f"Selected file: **{uploaded_file.name}**"
    )


    if st.button(
        "Upload and Process",
        type="primary",
    ):

        try:

            with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=Path(
                    uploaded_file.name
                ).suffix,
            ) as temp_file:

                temp_file.write(
                    uploaded_file.getbuffer()
                )

                temp_path = Path(
                    temp_file.name
                )


            with st.spinner(
                "Validating and importing report..."
            ):

                result = import_weekly_report(
                    temp_path
                )


            st.success(
                "Report processed successfully!"
            )


            col1, col2, col3, col4 = st.columns(4)


            col1.metric(
                "Rows Found",
                result["rows_found"],
            )

            col2.metric(
                "Inserted",
                result["rows_inserted"],
            )

            col3.metric(
                "Duplicates",
                result["duplicates_found"],
            )

            col4.metric(
                "Status",
                result["status"],
            )


        except Exception as error:

            st.error(
                f"Upload failed: {error}"
            )