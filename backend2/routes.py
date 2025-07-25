from flask import Blueprint, request, send_file, jsonify
import pandas as pd
import tempfile
import shutil
import zipfile
import io
import os
from models import ColumnMapping
from utils import format_date_for_column, is_date_column, get_latest_mappings
from report_generator import get_execution_report_and_generate_pdf  # Add this import
# Add these imports to your existing imports
from werkzeug.utils import secure_filename
import uuid
from datetime import datetime
from reconreport import ReconciliationReportGenerator, generate_reconciliation_report, RAW_FILE_PATH, SOAP_CONFIG

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
                zipf.write(tmp_csv.name, arcname="RaInterfaceLinesAll.csv")
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

@main_bp.route('/generate-execution-report', methods=['POST'])
def generate_execution_report():
    """Generate execution report PDF from AutoInvoice request ID"""
    try:
        data = request.get_json()
        autoinvoice_request_id = data.get('autoinvoice_request_id')
        
        if not autoinvoice_request_id:
            return jsonify({"error": "Missing autoinvoice_request_id parameter"}), 400
        
        print(f"📄 Generating execution report for AutoInvoice Request ID: {autoinvoice_request_id}")
        
        # Call your report generation function
        result = get_execution_report_and_generate_pdf(autoinvoice_request_id)
        
        if result["status"] == "success":
            # Return the PDF file
            pdf_path = result["files"]["pdf_report"]
            
            return send_file(
                pdf_path,
                mimetype="application/pdf",
                as_attachment=True,
                download_name=f"AutoInvoice_Execution_Report_{autoinvoice_request_id}.pdf"
            )
        else:
            return jsonify(result), 500
            
    except Exception as e:
        print(f"Error in generate_execution_report: {e}")
        return jsonify({"error": str(e)}), 500

# UPDATED RECONCILIATION ROUTES - NO FILE UPLOAD REQUIRED

@main_bp.route('/reconreport/generate', methods=['POST'])
def generate_reconciliation_report_endpoint():
    """Generate reconciliation report using predefined raw file path"""
    try:
        print("🚀 Starting reconciliation report generation with predefined raw file...")
        
        # Verify that the predefined raw file exists
        if not os.path.exists(RAW_FILE_PATH):
            return jsonify({
                'status': 'error',
                'error': f'Predefined raw file not found at: {RAW_FILE_PATH}'
            }), 404
        
        print(f"📊 Using predefined raw file: {RAW_FILE_PATH}")
        
        # Option 1: Use the standalone function (simpler approach)
        result = generate_reconciliation_report()
        
        if result['status'] == 'success':
            # Extract filename from the full path
            output_filename = os.path.basename(result['output_file'])
            
            print(f"✅ Reconciliation report generated successfully: {output_filename}")
            
            return jsonify({
                'status': 'success',
                'message': 'Reconciliation report generated successfully',
                'filename': output_filename,
                'total_records': result['total_records'],
                'matched_records': result['matched_records'],
                'match_percentage': round((result['matched_records'] / result['total_records']) * 100, 2) if result['total_records'] > 0 else 0,
                'download_url': f"/reconreport/download/{output_filename}",
                'source_file': result['source_file']
            })
        else:
            print(f"❌ Reconciliation report generation failed: {result['error']}")
            return jsonify({
                'status': 'error',
                'error': result['error']
            }), 500
            
    except Exception as e:
        print(f"Error in generate_reconciliation_report_endpoint: {e}")
        return jsonify({'status': 'error', 'error': str(e)}), 500

@main_bp.route('/reconreport/download/<filename>', methods=['GET'])
def download_reconciliation_report(filename):
    """Download generated reconciliation report"""
    try:
        # Try multiple possible locations for the file
        possible_locations = [
            # Original output directory (same as raw file directory)
            os.path.join(os.path.dirname(RAW_FILE_PATH), filename),
            # Temp directory
            os.path.join(tempfile.gettempdir(), filename),
            # Current working directory
            filename
        ]
        
        file_path = None
        for location in possible_locations:
            if os.path.exists(location):
                file_path = location
                break
        
        if not file_path:
            return jsonify({'error': f'File not found: {filename}. Searched in: {possible_locations}'}), 404
        
        print(f"📥 Downloading reconciliation report from: {file_path}")
        
        return send_file(
            file_path,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
    except Exception as e:
        print(f"Error in download_reconciliation_report: {e}")
        return jsonify({'error': str(e)}), 500

@main_bp.route('/reconreport/status', methods=['GET'])
def get_reconciliation_status():
    """Get status of reconciliation service"""
    try:
        # Check if raw file exists
        raw_file_exists = os.path.exists(RAW_FILE_PATH)
        
        return jsonify({
            'status': 'ready' if raw_file_exists else 'error',
            'message': 'Reconciliation service is ready' if raw_file_exists else 'Raw file not found',
            'service': 'Reconciliation Report Generator',
            'raw_file_path': RAW_FILE_PATH,
            'raw_file_exists': raw_file_exists,
            'soap_config': {
                'wsdl_url': SOAP_CONFIG['wsdl_url'],
                'username': SOAP_CONFIG['username'],
                'target_report_path': SOAP_CONFIG['target_report_path']
            }
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        })

@main_bp.route('/reconreport/test', methods=['GET'])
def test_reconciliation_service():
    """Test endpoint to verify reconciliation service is working"""
    try:
        # Test that we can import and initialize the reconciliation generator
        generator = ReconciliationReportGenerator(SOAP_CONFIG)
        
        # Check if raw file exists
        raw_file_exists = os.path.exists(RAW_FILE_PATH)
        
        return jsonify({
            'status': 'success',
            'message': 'Reconciliation service is operational',
            'raw_file_exists': raw_file_exists,
            'raw_file_path': RAW_FILE_PATH,
            'soap_config': {
                'wsdl_url': SOAP_CONFIG['wsdl_url'],
                'username': SOAP_CONFIG['username'],
                'target_report_path': SOAP_CONFIG['target_report_path']
            }
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

# OPTIONAL: Alternative endpoint using the class-based approach
@main_bp.route('/reconreport/generate-class', methods=['POST'])
def generate_reconciliation_report_class():
    """Alternative endpoint using ReconciliationReportGenerator class"""
    try:
        print("🚀 Starting reconciliation report generation using class approach...")
        
        # Verify that the predefined raw file exists
        if not os.path.exists(RAW_FILE_PATH):
            return jsonify({
                'status': 'error',
                'error': f'Predefined raw file not found at: {RAW_FILE_PATH}'
            }), 404
        
        # Initialize the reconciliation generator
        generator = ReconciliationReportGenerator(SOAP_CONFIG)
        
        # Generate report using the class method
        result = generator.generate_reconciliation_report(RAW_FILE_PATH, tempfile.gettempdir())
        
        if result['status'] == 'success':
            print(f"✅ Reconciliation report generated successfully: {result['output_filename']}")
            
            return jsonify({
                'status': 'success',
                'message': 'Reconciliation report generated successfully',
                'filename': result['output_filename'],
                'total_records': result['total_records'],
                'matched_records': result['matched_records'],
                'match_percentage': result['match_percentage'],
                'download_url': f"/reconreport/download/{result['output_filename']}"
            })
        else:
            print(f"❌ Reconciliation report generation failed: {result['error']}")
            return jsonify({
                'status': 'error',
                'error': result['error']
            }), 500
            
    except Exception as e:
        print(f"Error in generate_reconciliation_report_class: {e}")
        return jsonify({'status': 'error', 'error': str(e)}), 500
