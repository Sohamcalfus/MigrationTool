import pandas as pd
import tempfile
import shutil
import zipfile
import io

def generate_fbdi_from_files(template_file_path, raw_file_path):
    # Create temporary copies of the files (optional, but mimics upload behavior)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsm") as tmp_template, \
         tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp_raw:
        with open(template_file_path, "rb") as src_template:
            shutil.copyfileobj(src_template, tmp_template)
        with open(raw_file_path, "rb") as src_raw:
            shutil.copyfileobj(src_raw, tmp_raw)

    # Read the template file (specific sheet)
    template_df = pd.read_excel(tmp_template.name, sheet_name="RA_INTERFACE_LINES_ALL", header=None)

    # Read raw file (first sheet)
    raw_sheets = pd.read_excel(tmp_raw.name, sheet_name=None)
    raw_df = pd.read_excel(tmp_raw.name, sheet_name=list(raw_sheets.keys())[0], header=None)

    # Extract headers
    template_columns = template_df.iloc[3].tolist()  # Row 4 (index 3)
    raw_columns = raw_df.iloc[1].tolist()            # Row 2 (index 1)

    # Get raw data starting from row 3 (index 2)
    raw_data = raw_df.iloc[2:].reset_index(drop=True)

    # Determine starting point for data insertion in template
    start_row = 4
    num_rows = raw_data.shape[0]

    # Ensure the template has enough rows
    rows_needed = start_row + num_rows
    if template_df.shape[0] < rows_needed:
        empty_rows = pd.DataFrame([[""] * template_df.shape[1]] * (rows_needed - template_df.shape[0]))
        template_df = pd.concat([template_df, empty_rows], ignore_index=True)

    # Copy data from raw file into the template
    for col_idx, template_col in enumerate(template_columns):
        if template_col in raw_columns:
            raw_col_idx = raw_columns.index(template_col)
            template_df.iloc[start_row:start_row + num_rows, col_idx] = raw_data.iloc[:, raw_col_idx].values
        else:
            template_df.iloc[start_row:start_row + num_rows, col_idx] = ""

    # Save result to CSV in memory and return zipped buffer
    with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp_csv:
        template_df.to_csv(tmp_csv.name, index=False, header=False)

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.write(tmp_csv.name, arcname="fbdi_output.csv")
        zip_buffer.seek(0)

    return zip_buffer

if __name__ == "__main__":
    template_path = "C:/Users/SohamKasurde/Conversion/AR_Normal_POC.xlsm"
    raw_path = "C:/Users/SohamKasurde/Conversion/Customer Invoice Conversion Data - RAW File.xlsx"

    zip_buffer = generate_fbdi_from_files(template_path, raw_path)

    with open("fbdi_output.zip", "wb") as f:
        f.write(zip_buffer.read())
