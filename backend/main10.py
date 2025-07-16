import pandas as pd
import google.generativeai as genai
import json
from datetime import datetime
import os

# ==== CONFIGURE GEMINI ====
genai.configure(api_key="AIzaSyAMrzeuCtgCF5l_8o5Q4HCf6cSy_VudVXc")  # Replace with your actual API key
model = genai.GenerativeModel("gemini-1.5-flash")

# === Hardcoded paths ===
TEMPLATE_PATH = r"C:/Project/MigrationTool/AR_Normal_POC.xlsm"
RAW_PATH = r"C:/Project/MigrationTool/Customer Invoice Conversion Data - RAW File.xlsx"

def format_date_column(series):
    def try_parse(val):
        if pd.isna(val):
            return val
        try:
            return pd.to_datetime(val).strftime('%Y/%m/%d')
        except:
            return val
    return series.apply(try_parse)

def is_date_like(col_name):
    return any(word in col_name.lower() for word in ["date", "time"])

def suggest_column_mappings(raw_columns, template_columns):
    prompt = f"""
    Match each template column to the most semantically similar raw column.

    Template Columns: {template_columns}
    Raw Columns: {raw_columns}

    Return a JSON object like:
    {{
        "TemplateColumn1": "RawColumn1",
        "TemplateColumn2": "Not Mapped"
    }}
    """

    response = model.generate_content(prompt)
    try:
        text = response.text.strip()
        if text.startswith("```json"):
            text = text[7:-3].strip()
        elif text.startswith("```"):
            text = text[3:-3].strip()
        return json.loads(text)
    except Exception as e:
        print("❌ Failed to parse Gemini response:", e)
        return {}

def main():
    # Step 1: Validate paths
    if not os.path.exists(TEMPLATE_PATH):
        raise FileNotFoundError(f"Template file not found: {TEMPLATE_PATH}")
    if not os.path.exists(RAW_PATH):
        raise FileNotFoundError(f"Raw file not found: {RAW_PATH}")

    # Step 2: Read Excel files
    template_df = pd.read_excel(TEMPLATE_PATH, sheet_name="RA_INTERFACE_LINES_ALL", header=None)
    raw_df = pd.read_excel(RAW_PATH, header=None)

    # Step 3: Extract columns
    template_columns = template_df.iloc[3].tolist()
    raw_columns = raw_df.iloc[1].tolist()
    raw_data = raw_df.iloc[2:].reset_index(drop=True)

    # Step 4: Get AI-powered column mappings
    print("🔍 Getting AI-powered column mappings...")
    mappings = suggest_column_mappings(raw_columns, template_columns)

    # Step 5: Show only mapped results
    mapped_only = {k: v for k, v in mappings.items() if v != "Not Mapped"}
    print("✅ Successfully mapped columns:")
    for template_col, raw_col in mapped_only.items():
        print(f"  {template_col} --> {raw_col}")

    # Step 6: Fill template with mapped data
    start_row = 4
    num_rows = raw_data.shape[0]

    for t_col_idx, t_col in enumerate(template_columns):
        if pd.isna(t_col) or t_col == "":
            continue

        raw_col_name = mappings.get(t_col)
        if raw_col_name and raw_col_name != "Not Mapped" and raw_col_name in raw_columns:
            r_col_idx = raw_columns.index(raw_col_name)
            data_series = raw_data.iloc[:, r_col_idx]

            if is_date_like(t_col) or is_date_like(raw_col_name):
                print(f"📅 Formatting dates for: {t_col}")
                data_series = format_date_column(data_series)

            template_df.iloc[start_row:start_row + num_rows, t_col_idx] = data_series.values

    # Step 7: Save the updated template
    output_file = "fbdi_output_filled.xlsx"
    template_df.to_excel(output_file, index=False, header=False)
    print(f"✅ Output saved to: {output_file}")

if __name__ == "__main__":
    main()
