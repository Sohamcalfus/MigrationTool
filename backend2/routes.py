from flask import Blueprint, request, send_file, jsonify
import pandas as pd
import tempfile
import shutil
import zipfile
import io
import os
from models import ColumnMapping
from utils import format_date_for_column, is_date_column, get_latest_mappings

main_bp = Blueprint('main', __name__)

@main_bp.route('/preview-mappings', methods=['POST'])
def preview_mappings():
    try:
        raw_file = request.files.get('raw_file')
        fbdi_type = request.form.get('fbdi_type')

        if not raw_file or not fbdi_type:
            return jsonify({"error": "Missing raw file or FBDI type"}), 400

        template_path = f"templates/{fbdi_type}_template.xlsm"
        if not os.path.exists(template_path):
            return jsonify({"error": f"Template for type '{fbdi_type}' not found"}), 404

        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp_raw, \
             tempfile.NamedTemporaryFile(delete=False, suffix=".xlsm") as tmp_template:
            shutil.copyfileobj(raw_file.stream, tmp_raw)
            shutil.copyfile(template_path, tmp_template.name)

        template_df = pd.read_excel(tmp_template.name, sheet_name="RA_INTERFACE_LINES_ALL", header=None)
        raw_df = pd.read_excel(tmp_raw.name, sheet_name=0, header=None)

        template_columns = template_df.iloc[3].tolist()
        raw_columns = raw_df.iloc[1].tolist()

        stored_mappings = get_latest_mappings()
        mappings = []

        for template_col in template_columns:
            if pd.isna(template_col) or template_col == "":
                continue
            if template_col == "*Buisness Unit Name":
                continue
            mapped_raw_col = None
            if template_col == "Comments" and "*Buisness Unit Name" in raw_columns:
                mapped_raw_col = "*Buisness Unit Name"
            elif template_col in stored_mappings:
                mapped_raw_col = stored_mappings[template_col]
            mappings.append({
                "template_column": template_col,
                "raw_column": mapped_raw_col or "Not Mapped"
            })

        os.remove(tmp_raw.name)
        os.remove(tmp_template.name)

        return jsonify({"status": "success", "mappings": mappings})

    except Exception as e:
        print(f"Error in preview_mappings: {e}")
        return jsonify({"error": str(e)}), 500

@main_bp.route('/generate-fbdi-from-type', methods=['POST'])
def generate_fbdi_from_type():
    try:
        raw_file = request.files.get('raw_file')
        fbdi_type = request.form.get('fbdi_type')
        project_name = request.form.get('project_name')
        env_type = request.form.get('env_type')

        print(f"✓ Generating FBDI for: {fbdi_type}, Project={project_name}, Env={env_type}")

        if not raw_file or not fbdi_type:
            return jsonify({"error": "Missing raw file or FBDI type"}), 400

        template_path = f"templates/{fbdi_type}_template.xlsm"
        if not os.path.exists(template_path):
            return jsonify({"error": f"Template for type '{fbdi_type}' not found"}), 404

        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp_raw, \
             tempfile.NamedTemporaryFile(delete=False, suffix=".xlsm") as tmp_template:
            shutil.copyfileobj(raw_file.stream, tmp_raw)
            shutil.copyfile(template_path, tmp_template.name)

        # Read files without automatically parsing dates
        template_df = pd.read_excel(tmp_template.name, sheet_name="RA_INTERFACE_LINES_ALL", header=None)
        raw_df = pd.read_excel(tmp_raw.name, sheet_name=0, header=None)

        template_columns = template_df.iloc[3].tolist()
        raw_columns = raw_df.iloc[1].tolist()
        raw_data = raw_df.iloc[2:].reset_index(drop=True)

        start_row = 4
        num_rows = raw_data.shape[0]

        if template_df.shape[0] < start_row + num_rows:
            empty_rows = pd.DataFrame([[""] * template_df.shape[1]] * (start_row + num_rows - template_df.shape[0]))
            template_df = pd.concat([template_df, empty_rows], ignore_index=True)

        stored_mappings = get_latest_mappings()
        has_bu_col = "*Buisness Unit Name" in raw_columns

        for col_idx, template_col in enumerate(template_columns):
            if pd.isna(template_col) or template_col == "" or template_col == "*Buisness Unit Name":
                continue
            
            if template_col == "Comments" and has_bu_col:
                raw_idx = raw_columns.index("*Buisness Unit Name")
                template_df.iloc[start_row:start_row + num_rows, col_idx] = raw_data.iloc[:, raw_idx].values
                continue
            
            if template_col in stored_mappings:
                raw_col_name = stored_mappings[template_col]
                if raw_col_name in raw_columns:
                    raw_idx = raw_columns.index(raw_col_name)
                    data = raw_data.iloc[:, raw_idx]
                    
                    # Apply date formatting to any column that might contain dates
                    if is_date_column(template_col) or is_date_column(raw_col_name):
                        print(f"Formatting dates for column: {template_col}")
                        data = format_date_for_column(data, template_col)
                    
                    template_df.iloc[start_row:start_row + num_rows, col_idx] = data.values

        if "*Buisness Unit Name" in template_columns:
            col_idx = template_columns.index("*Buisness Unit Name")
            template_df = template_df.drop(columns=col_idx, axis=1)

        final_df = template_df.iloc[start_row:start_row + num_rows]

        with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp_csv:
            # Ensure no automatic date parsing when saving to CSV
            final_df.to_csv(tmp_csv.name, index=False, header=False, date_format='%Y/%m/%d')
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
                zipf.write(tmp_csv.name, arcname="fbdi_output.csv")
            zip_buffer.seek(0)

        os.remove(tmp_raw.name)
        os.remove(tmp_template.name)
        os.remove(tmp_csv.name)

        return send_file(
            zip_buffer,
            mimetype='application/zip',
            as_attachment=True,
            download_name='fbdi_output.zip'
        )

    except Exception as e:
        print(f"Error in generate_fbdi_from_type: {e}")
        return jsonify({"error": str(e)}), 500

@main_bp.route('/test-db')
def test_db():
    try:
        count = ColumnMapping.query.count()
        return jsonify({"status": "ok", "mapping_count": count})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
