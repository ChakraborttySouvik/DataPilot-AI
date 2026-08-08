from __future__ import annotations

import streamlit as st
import pandas as pd


def render_data_cleaning(
    dataframe: pd.DataFrame,
) -> None:
    
    # ======================================================
    # Working Dataset
    # ======================================================

    if "cleaned_df" not in st.session_state:
        st.session_state.cleaned_df = dataframe.copy()
    # ======================================================
    # Cleaning History Initialization
    # ======================================================

    if "cleaning_history" not in st.session_state:
        st.session_state.cleaning_history = []

    cleaned = st.session_state.cleaned_df.copy()
    st.title("🧹 Data Cleaning")
    st.caption("Clean and prepare your dataset before analysis.")

    st.divider()

    st.info(
        "Choose one or more cleaning operations from the options below."
    )
    if st.button(
        "🔄 Reset Dataset",
        key="reset_dataset_btn",
    ):
        st.session_state.cleaned_df = dataframe.copy()
        cleaned = st.session_state.cleaned_df
        st.success("Dataset restored.")
    # ======================================================
    # Remove Duplicate Rows
    # ======================================================

    st.subheader("🗑 Remove Duplicate Rows")

    duplicates = cleaned.duplicated().sum()

    st.metric(
        "Duplicate Rows",
        duplicates,
    )

    if duplicates == 0:
        st.success("✅ No duplicate rows found.")
    else:
        st.warning(f"⚠️ {duplicates} duplicate rows detected.")

    if st.button(
        "Remove Duplicates",
        key="remove_duplicates_btn",
        disabled=(duplicates == 0),
    ):

        cleaned = cleaned.drop_duplicates()
        st.session_state.cleaned_df = cleaned

        col1, col2 = st.columns(2)

        with col1:
            st.metric(
                "Original Rows",
                len(dataframe),
            )

        with col2:
            st.metric(
                "Cleaned Rows",
                len(cleaned),
            )

        st.success(
            f"Removed {duplicates} duplicate rows."
        )

        st.dataframe(
            cleaned.head(10),
            use_container_width=True,
            hide_index=True,
        )
        st.session_state.cleaning_history.append(
            f"🗑 Removed {duplicates} duplicate rows"
        )

  

    st.divider()
    # ======================================================
    # Handle Missing Values
    # ======================================================

    st.subheader("🩹 Handle Missing Values")

    missing_columns = [
        col
        for col in cleaned.columns
        if cleaned[col].isna().sum() > 0
    ]

    if not missing_columns:

        st.success("✅ No missing values found.")

    else:

        columns = st.multiselect(
            "Select Columns",
            missing_columns,
            placeholder="Choose one or more columns...",
            key="missing_columns",
        )

        methods = [
            "Auto (Recommended)",
            "Mean",
            "Median",
            "Mode",
            "Drop Missing Rows",
        ]

        method = st.selectbox(
            "Method",
            methods,
            key="missing_method",
        )

        if columns and st.button(
            "Apply Missing Value Cleaning",
            key="missing_values_btn",
        ):

            before = {
                col: cleaned[col].isna().sum()
                for col in columns
            }

            for column in columns:

                is_numeric = pd.api.types.is_numeric_dtype(cleaned[column])

                if method == "Auto (Recommended)":
                    if is_numeric:
                        cleaned[column] = cleaned[column].fillna(
                            cleaned[column].mean()
                        )
                    else:
                        cleaned[column] = cleaned[column].fillna(
                            cleaned[column].mode()[0]
                        )

                elif method == "Mean" and is_numeric:
                    cleaned[column] = cleaned[column].fillna(
                        cleaned[column].mean()
                    )

                elif method == "Median" and is_numeric:
                    cleaned[column] = cleaned[column].fillna(
                        cleaned[column].median()
                    )

                elif method == "Mode":
                    cleaned[column] = cleaned[column].fillna(
                        cleaned[column].mode()[0]
                    )

                elif method == "Drop Missing Rows":
                    cleaned = cleaned.dropna(subset=[column])

            st.session_state.cleaned_df = cleaned

            st.success("✅ Missing values handled successfully.")

            c1, c2 = st.columns(2)

            with c1:
                st.metric(
                    "Missing Before",
                    sum(before.values()),
                )

            with c2:
                st.metric(
                    "Missing After",
                    sum(cleaned[col].isna().sum() for col in columns),
                )

            st.dataframe(
                cleaned.head(10),
                use_container_width=True,
                hide_index=True,
            )
            st.session_state.cleaning_history.append(
                f"🩹 Filled missing values in {len(columns)} column(s) using {method}"
            )

    st.divider()
    # ======================================================
    # Remove Columns
    # ======================================================

    st.subheader("🗑 Remove Columns")

    columns_to_remove = st.multiselect(
        "Select Columns",
        cleaned.columns.tolist(),
        placeholder="Choose one or more columns...",
        key="remove_columns",
    )

    if columns_to_remove:

        st.warning(
            f"Selected {len(columns_to_remove)} column(s) for removal."
        )

    if st.button(
        "Remove Selected Columns",
        key="remove_columns_btn",
        disabled=(len(columns_to_remove) == 0),
    ):

        original_columns = cleaned.shape[1]

        cleaned = cleaned.drop(
            columns=columns_to_remove
        )

        st.session_state.cleaned_df = cleaned

        col1, col2 = st.columns(2)

        with col1:
            st.metric(
                "Original Columns",
                original_columns,
            )

        with col2:
            st.metric(
                "Remaining Columns",
                cleaned.shape[1],
            )

        st.success(
            f"✅ Removed {len(columns_to_remove)} column(s)."
        )

        st.dataframe(
            cleaned.head(10),
            use_container_width=True,
            hide_index=True,
        )

        # Add to Cleaning History
        st.session_state.cleaning_history.append(
            f"❌ Removed {len(columns_to_remove)} column(s): {', '.join(columns_to_remove)}"
        )

    st.divider()
    
    
    # ======================================================
    # Rename Columns
    # ======================================================

    

    st.subheader("🏷️ Rename Columns")

    rename_column = st.selectbox(
        "Select Column",
        cleaned.columns.tolist(),
        key="rename_column",
    )

    new_name = st.text_input(
        "New Column Name",
        key="new_column_name",
    )

    if st.button(
        "Rename Column",
        key="rename_column_btn",
    ):

        if not new_name.strip():

            st.warning("Please enter a new column name.")

        elif new_name in cleaned.columns:

            st.error("A column with this name already exists.")

        else:

            old_name = rename_column

            cleaned = cleaned.rename(
                columns={
                    old_name: new_name.strip()
                }
            )

            st.session_state.cleaned_df = cleaned

            st.success(
                f"✅ '{old_name}' renamed to '{new_name}'."
            )

            col1, col2 = st.columns(2)

            with col1:
                st.metric(
                    "Columns",
                    cleaned.shape[1],
                )

            with col2:
                st.metric(
                    "Renamed",
                    1,
                )

            st.dataframe(
                cleaned.head(10),
                use_container_width=True,
                hide_index=True,
            )
            st.session_state.cleaning_history.append(
                f"🏷 Renamed '{old_name}' → '{new_name.strip()}'"
            )
    # ======================================================
    # Change Data Types
    # ======================================================

    st.divider()

    st.subheader("📊 Change Data Types")

    selected_columns = st.multiselect(
        "Select Columns",
        cleaned.columns.tolist(),
        key="datatype_columns",
    )

    datatype = st.selectbox(
        "Convert To",
        [
            "int",
            "float",
            "string",
            "category",
            "datetime",
        ],
        key="datatype_choice",
    )

    if selected_columns and st.button(
        "Change Data Type",
        key="datatype_btn",
    ):

        success = 0
        failed = 0

        for column in selected_columns:

            try:

                if datatype == "int":
                    cleaned[column] = cleaned[column].astype(int)

                elif datatype == "float":
                    cleaned[column] = cleaned[column].astype(float)

                elif datatype == "string":
                    cleaned[column] = cleaned[column].astype(str)

                elif datatype == "category":
                    cleaned[column] = cleaned[column].astype("category")

                elif datatype == "datetime":
                    cleaned[column] = pd.to_datetime(
                        cleaned[column],
                        errors="coerce",
                    )

                success += 1

            except Exception:

                failed += 1

        st.session_state.cleaned_df = cleaned

        c1, c2 = st.columns(2)

        with c1:
            st.metric(
                "Successful",
                success,
            )

        with c2:
            st.metric(
                "Failed",
                failed,
            )

        if failed == 0:
            st.success("✅ Data types updated successfully.")
        else:
            st.warning(
                f"{failed} column(s) could not be converted."
            )

        st.dataframe(
            cleaned.head(10),
            use_container_width=True,
            hide_index=True,
        )
        st.session_state.cleaning_history.append(
            f"📊 Converted {success} column(s) to {datatype}"
        )
    # ======================================================
    # Remove Outliers (IQR)
    # ======================================================

    st.divider()

    st.subheader("📈 Remove Outliers (IQR Method)")

    numeric_columns = cleaned.select_dtypes(
        include=["number"]
    ).columns.tolist()

    if not numeric_columns:

        st.info("No numeric columns available.")

    else:

        selected_columns = st.multiselect(
            "Select Numeric Columns",
            numeric_columns,
            key="outlier_columns",
        )

        if selected_columns and st.button(
            "Remove Outliers",
            key="remove_outliers_btn",
        ):

            original_rows = len(cleaned)

            for column in selected_columns:

                Q1 = cleaned[column].quantile(0.25)
                Q3 = cleaned[column].quantile(0.75)

                IQR = Q3 - Q1

                lower = Q1 - 1.5 * IQR
                upper = Q3 + 1.5 * IQR

                cleaned = cleaned[
                    (cleaned[column] >= lower)
                    & (cleaned[column] <= upper)
                ]

            removed_rows = original_rows - len(cleaned)

            st.session_state.cleaned_df = cleaned

            c1, c2 = st.columns(2)

            with c1:
                st.metric(
                    "Rows Removed",
                    removed_rows,
                )

            with c2:
                st.metric(
                    "Remaining Rows",
                    len(cleaned),
                )

            st.success(
                f"✅ Removed {removed_rows} outlier rows."
            )

            st.dataframe(
                cleaned.head(10),
                use_container_width=True,
                hide_index=True,
            )
            st.session_state.cleaning_history.append(
                f"📈 Removed {removed_rows} outlier row(s)"
            )
    # ======================================================
    # Trim Text Columns
    # ======================================================

    st.divider()

    st.subheader("🧹 Trim Text Columns")

    text_columns = cleaned.select_dtypes(
        include=["object", "string"]
    ).columns.tolist()

    if not text_columns:

        st.info("No text columns found.")

    else:

        selected_columns = st.multiselect(
            "Select Text Columns",
            text_columns,
            key="trim_columns",
        )

        if selected_columns and st.button(
            "Trim Text",
            key="trim_text_btn",
        ):

            for column in selected_columns:

                cleaned[column] = (
                    cleaned[column]
                    .astype(str)
                    .str.strip()
                )

            st.session_state.cleaned_df = cleaned

            st.success(
                f"✅ Trimmed {len(selected_columns)} column(s)."
            )

            st.dataframe(
                cleaned.head(10),
                use_container_width=True,
                hide_index=True,
            )
            st.session_state.cleaning_history.append(
                f"🧹 Trimmed text in {len(selected_columns)} column(s)"
            )
    # ======================================================
    # Remove Constant Columns
    # ======================================================

    st.divider()

    st.subheader("❌ Remove Constant Columns")

    constant_columns = [
        col
        for col in cleaned.columns
        if cleaned[col].nunique(dropna=False) == 1
    ]

    if not constant_columns:

        st.success("✅ No constant columns found.")

    else:

        st.write("Columns with only one unique value:")

        st.write(constant_columns)

        if st.button(
            "Remove Constant Columns",
            key="constant_columns_btn",
        ):

            cleaned = cleaned.drop(
                columns=constant_columns
            )

            st.session_state.cleaned_df = cleaned

            st.success(
                f"✅ Removed {len(constant_columns)} constant column(s)."
            )

            st.dataframe(
                cleaned.head(10),
                use_container_width=True,
                hide_index=True,
            )
            st.session_state.cleaning_history.append(
                f"🚫 Removed {len(constant_columns)} constant column(s)"
            )
    # ======================================================
    # Cleaning History
    # ======================================================

    st.divider()

    st.subheader("📋 Cleaning History")

    history = st.session_state.cleaning_history

    if not history:

        st.info("No cleaning operations performed yet.")

    else:

        for i, operation in enumerate(history, start=1):
            st.write(f"{i}. {operation}")

        col1, col2 = st.columns([1, 3])

        with col1:
            if st.button(
                "🗑 Clear History",
                key="clear_history_btn",
            ):
                st.session_state.cleaning_history = []
                st.rerun()

        with col2:

            history_text = "\n".join(
                f"{i}. {op}"
                for i, op in enumerate(history, start=1)
            )

            st.download_button(
                "⬇ Download History",
                history_text,
                file_name="cleaning_history.txt",
                mime="text/plain",
                key="download_history_btn",
            )

    st.divider()

    st.subheader("📋 Current Cleaned Dataset")

    st.dataframe(
        st.session_state.cleaned_df.head(10),
        use_container_width=True,
        hide_index=True,
    )

    csv = (
        st.session_state.cleaned_df
        .to_csv(index=False)
        .encode("utf-8")
    )

    st.download_button(
        "⬇ Download Final Cleaned Dataset",
        csv,
        "datapilot_cleaned_dataset.csv",
        "text/csv",
        key="final_download_btn",
    )
                    
        
    
 