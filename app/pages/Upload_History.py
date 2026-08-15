import streamlit as st
import pandas as pd

from app.ui import configure_page, sidebar_header
from app.services.uploads import (
    get_upload_history,
    delete_upload,
)


configure_page("Upload History")

sidebar_header()


st.title("📁 Upload History")

st.caption(
    "View and manage weekly invoice reports."
)


uploads = get_upload_history()


if not uploads:

    st.info("No reports have been uploaded yet.")
    st.stop()


df = pd.DataFrame(uploads)


col1, col2, col3 = st.columns(3)


col1.metric(
    "Reports",
    f"{len(df):,}",
)


col2.metric(
    "Invoices",
    f"{df['invoice_count'].sum():,}",
)


col3.metric(
    "Rows Imported",
    f"{df['rows_inserted'].sum():,}",
)


st.divider()

st.subheader("📋 Uploaded Reports")


for _, report in df.iterrows():

    upload_id = int(report["id"])

    filename = report["filename"]

    uploaded_at = report["uploaded_at"]

    invoice_count = int(
        report["invoice_count"]
    )

    rows_found = int(
        report["rows_found"]
    )

    rows_inserted = int(
        report["rows_inserted"]
    )

    duplicates = int(
        report["duplicates_found"]
    )

    status = report["status"]


    with st.container(border=True):

        col1, col2 = st.columns(
            [5, 1]
        )


        with col1:

            st.markdown(
                f"### 📄 {filename}"
            )

            st.write(
                f"**Uploaded:** "
                f"{uploaded_at}"
            )

            st.write(
                f"**Rows found:** "
                f"{rows_found:,}  |  "
                f"**Inserted:** "
                f"{rows_inserted:,}  |  "
                f"**Duplicates:** "
                f"{duplicates:,}"
            )

            st.write(
                f"**Invoices currently linked:** "
                f"{invoice_count:,}"
            )

            st.write(
                f"**Status:** {status}"
            )


        with col2:

            delete_key = (
                f"delete_{upload_id}"
            )

            confirm_key = (
                f"confirm_{upload_id}"
            )


            if st.button(
                "🗑️ Delete",
                key=delete_key,
                use_container_width=True,
            ):

                st.session_state[
                    confirm_key
                ] = True


            if st.session_state.get(
                confirm_key,
                False,
            ):

                st.warning(
                    "This will permanently delete "
                    "the report and its invoices."
                )


                confirm_col1, confirm_col2 = (
                    st.columns(2)
                )


                with confirm_col1:

                    if st.button(
                        "Yes, Delete",
                        key=f"yes_{upload_id}",
                        type="primary",
                        use_container_width=True,
                    ):

                        deleted = delete_upload(
                            upload_id
                        )


                        if deleted:

                            st.success(
                                f"Deleted: "
                                f"{deleted['filename']}"
                            )

                        else:

                            st.error(
                                "Report could not be deleted."
                            )


                        st.session_state[
                            confirm_key
                        ] = False

                        st.rerun()


                with confirm_col2:

                    if st.button(
                        "Cancel",
                        key=f"cancel_{upload_id}",
                        use_container_width=True,
                    ):

                        st.session_state[
                            confirm_key
                        ] = False

                        st.rerun()