from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import pandas as pd
import tempfile
import shutil
import zipfile
import io
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)

# === CONFIG ===
instance_path = os.path.join(os.path.dirname(__file__), 'instance')
os.makedirs(instance_path, exist_ok=True)
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(instance_path, "db.sqlite3")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
print(f"Database path: {app.config['SQLALCHEMY_DATABASE_URI']}")

# === DB SETUP ===
from models import db, ColumnMapping
db.init_app(app)

def format_date_for_column(data_series, column_name):
    def format_single_date(date_value):
        if pd.isna(date_value) or date_value == "":
            return date_value
        try:
            if isinstance(date_value, str):
                for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%Y/%m/%d', '%m-%d-%Y', '%d-%m-%Y']:
                    try:
                        parsed_date = datetime.strptime(date_value, fmt)
                        break
                    except ValueError:
                        continue
                else:
                    return date_value
            elif isinstance(date_value, datetime):
                parsed_date = date_value
            else:
                parsed_date = pd.to_datetime(date_value)
            if column_name == "Currency Conversion Date":
                return parsed_date.strftime('%Y/%m/%d')
            elif column_name == "Line Transactions Flexfield Segment 10":
                return parsed_date.strftime('%-m/%-d/%y')
            else:
                return date_value
        except Exception as e:
            print(f"Error formatting date {date_value}: {e}")
            return date_value
    return data_series.apply(format_single_date)

def get_latest_mappings():
    try:
        mappings = ColumnMapping.query.filter(ColumnMapping.status == 'Y')\
            .order_by(ColumnMapping.created_at.desc()).all()
        mapping_dict = {m.template_column: m.raw_column for m in mappings}
        return mapping_dict
    except Exception as e:
        print(f"Error getting mappings: {e}")
        return {}

@app.route('/generate-fbdi-from-type', methods=['POST'])
def generate_fbdi_from_type():
    try:
        raw_file = request.files.get('raw_file')
        fbdi_type = request.form.get('fbdi_type')
        project_name = request.form.get('project_name')
        env_type = request.form.get('env_type')

        print(f"✓ Received request for: FBDI Type={fbdi_type}, Project={project_name}, Env={env_type}")

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
        raw_sheets = pd.read_excel(tmp_raw.name, sheet_name=None)
        raw_df = pd.read_excel(tmp_raw.name, sheet_name=list(raw_sheets.keys())[0], header=None)

        template_header_row = 3
        raw_header_row = 1
        template_columns = template_df.iloc[template_header_row].tolist()
        raw_columns = raw_df.iloc[raw_header_row].tolist()
        raw_data = raw_df.iloc[raw_header_row + 1:].reset_index(drop=True)

        start_row = template_header_row + 1
        num_rows = raw_data.shape[0]
        rows_needed = start_row + num_rows

        if template_df.shape[0] < rows_needed:
            empty_rows = pd.DataFrame([[""] * template_df.shape[1]] * (rows_needed - template_df.shape[0]))
            template_df = pd.concat([template_df, empty_rows], ignore_index=True)

        stored_mappings = get_latest_mappings()
        has_buisness_unit_in_raw = "*Buisness Unit Name" in raw_columns

        for col_idx, template_col in enumerate(template_columns):
            if pd.isna(template_col) or template_col == "":
                continue
            if template_col == "*Buisness Unit Name":
                continue
            if template_col == "Comments" and has_buisness_unit_in_raw:
                raw_idx = raw_columns.index("*Buisness Unit Name")
                template_df.iloc[start_row:start_row + num_rows, col_idx] = raw_data.iloc[:, raw_idx].values
                continue
            if template_col in stored_mappings:
                raw_col_name = stored_mappings[template_col]
                if raw_col_name in raw_columns:
                    raw_idx = raw_columns.index(raw_col_name)
                    raw_col_data = raw_data.iloc[:, raw_idx]
                    if template_col in ["Currency Conversion Date", "Line Transactions Flexfield Segment 10"]:
                        formatted = format_date_for_column(raw_col_data, template_col)
                        template_df.iloc[start_row:start_row + num_rows, col_idx] = formatted.values
                    else:
                        template_df.iloc[start_row:start_row + num_rows, col_idx] = raw_col_data.values

        if "*Buisness Unit Name" in template_columns:
            col_idx = template_columns.index("*Buisness Unit Name")
            template_df = template_df.drop(columns=col_idx, axis=1)

        data_only_df = template_df.iloc[start_row:start_row + num_rows]

        with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp_csv:
            data_only_df.to_csv(tmp_csv.name, index=False, header=False)
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
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/test-db')
def test_db():
    try:
        count = ColumnMapping.query.count()
        return jsonify({"status": "ok", "mapping_count": count})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def create_tables():
    with app.app_context():
        db.create_all()
        print("✓ Tables ensured")

if __name__ == '__main__':
    print("🚀 Starting Flask server...")
    create_tables()
    app.run(debug=True)
