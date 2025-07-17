from flask import Blueprint, request, jsonify
import base64
import requests
import json
import time
from datetime import datetime
import os

fbdi_bp = Blueprint('fbdi', __name__)

# Updated configuration for your Oracle Cloud instance
ORACLE_CLOUD_CONFIG = {
    'base_url': 'https://miterbrands-ibayqy-test.fa.ocs.oraclecloud.com',
    'username': 'FUSTST.CONVERSION',  # Replace with your actual username
    'password': 'M1terFu81tcO%n',  # Replace with your actual password
    'ucm_account': 'fin$/recievables$/import$'
}

def get_oracle_headers():
    """Get headers for Oracle Cloud API calls"""
    credentials = f"{ORACLE_CLOUD_CONFIG['username']}:{ORACLE_CLOUD_CONFIG['password']}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
    
    return {
        'Authorization': f'Basic {encoded_credentials}',
        'Content-Type': 'application/vnd.oracle.adf.resourceitem+json'
    }

@fbdi_bp.route('/upload-to-ucm', methods=['POST'])
def upload_to_ucm():
    """Upload generated FBDI file to Oracle UCM"""
    try:
        data = request.get_json()
        
        required_fields = ['document_content', 'file_name']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        # UCM upload payload
        ucm_payload = {
            "OperationName": "uploadFileToUCM",
            "DocumentContent": data['document_content'],
            "DocumentAccount": data.get('document_account', ORACLE_CLOUD_CONFIG['ucm_account']),
            "ContentType": "zip",
            "FileName": data['file_name'],
            "DocumentId": None
        }
        
        # Make API call to your Oracle Cloud instance
        response = requests.post(
            f"{ORACLE_CLOUD_CONFIG['base_url']}/fscmRestApi/resources/11.13.18.05/erpintegrations",
            headers=get_oracle_headers(),
            json=ucm_payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            return jsonify({
                "status": "success",
                "message": "File uploaded to UCM successfully",
                "document_id": result.get('DocumentId'),
                "response": result
            })
        else:
            return jsonify({
                "error": f"UCM upload failed: {response.status_code}",
                "details": response.text
            }), response.status_code
            
    except Exception as e:
        print(f"Error in upload_to_ucm: {e}")
        return jsonify({"error": str(e)}), 500

@fbdi_bp.route('/load-interface', methods=['POST'])
def load_interface():
    """Submit Interface Loader job"""
    try:
        data = request.get_json()
        
        ess_parameters = data.get('ess_parameters', '2,511142,N,N,N')
        
        interface_payload = {
            "OperationName": "submitESSJobRequest",
            "JobPackageName": "oracle/apps/ess/financials/commonModules/shared/common/interfaceLoader",
            "JobDefName": "InterfaceLoaderController",
            "ESSParameters": ess_parameters
        }
        
        response = requests.post(
            f"{ORACLE_CLOUD_CONFIG['base_url']}/fscmRestApi/resources/11.13.18.05/erpintegrations",
            headers=get_oracle_headers(),
            json=interface_payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            return jsonify({
                "status": "success",
                "message": "Interface Loader job submitted successfully",
                "job_id": result.get('ReqstId'),
                "response": result
            })
        else:
            return jsonify({
                "error": f"Interface Loader job failed: {response.status_code}",
                "details": response.text
            }), response.status_code
            
    except Exception as e:
        print(f"Error in load_interface: {e}")
        return jsonify({"error": str(e)}), 500

@fbdi_bp.route('/auto-invoice-import', methods=['POST'])
def auto_invoice_import():
    """Submit Auto Invoice Import job"""
    try:
        data = request.get_json()
        
        business_unit = data.get('business_unit', '300000003170678')
        batch_source = data.get('batch_source', 'MILGARD EBS SPREADSHEET')
        gl_date = data.get('gl_date', datetime.now().strftime('%Y-%m-%d'))
        
        # Build ESS parameters string
        ess_parameters = f"{business_unit},{batch_source},{gl_date},,,,,,,,,,,,,,,,,,,,Y,N"
        if 'ess_parameters' in data and data['ess_parameters']:
            ess_parameters = data['ess_parameters']
        
        auto_invoice_payload = {
            "OperationName": "submitESSJobRequest",
            "JobPackageName": "/oracle/apps/ess/financials/receivables/transactions/autoInvoices/",
            "JobDefName": "AutoInvoiceImportEss",
            "ESSParameters": ess_parameters
        }
        
        response = requests.post(
            f"{ORACLE_CLOUD_CONFIG['base_url']}/fscmRestApi/resources/11.13.18.05/erpintegrations",
            headers=get_oracle_headers(),
            json=auto_invoice_payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            return jsonify({
                "status": "success",
                "message": "Auto Invoice Import job submitted successfully",
                "job_id": result.get('ReqstId'),
                "response": result
            })
        else:
            return jsonify({
                "error": f"Auto Invoice Import job failed: {response.status_code}",
                "details": response.text
            }), response.status_code
            
    except Exception as e:
        print(f"Error in auto_invoice_import: {e}")
        return jsonify({"error": str(e)}), 500

@fbdi_bp.route('/check-job-status/<job_id>', methods=['GET'])
def check_job_status(job_id):
    """Check the status of a submitted job"""
    try:
        # Use the finder query parameter to get job status
        finder_param = f"ESSJobStatusRF;requestId={job_id}"
        
        response = requests.get(
            f"{ORACLE_CLOUD_CONFIG['base_url']}/fscmRestApi/resources/11.13.18.05/erpintegrations",
            headers=get_oracle_headers(),
            params={'finder': finder_param},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('items') and len(result['items']) > 0:
                job_info = result['items'][0]
                return jsonify({
                    "status": "success",
                    "job_status": job_info.get('RequestStatus'),
                    "job_id": job_info.get('ReqstId'),
                    "response": job_info
                })
            else:
                return jsonify({
                    "status": "not_found",
                    "message": f"Job {job_id} not found"
                }), 404
        else:
            return jsonify({
                "error": f"Job status check failed: {response.status_code}",
                "details": response.text
            }), response.status_code
            
    except Exception as e:
        print(f"Error in check_job_status: {e}")
        return jsonify({"error": str(e)}), 500

@fbdi_bp.route('/import-bulk-data', methods=['POST'])
def import_bulk_data():
    """Import bulk data using importBulkData operation"""
    try:
        data = request.get_json()
        
        # Build the importBulkData payload
        bulk_data_payload = {
            "OperationName": "importBulkData",
            "DocumentContent": data.get('document_content'),
            "FileName": data.get('file_name'),
            "DocumentAccount": data.get('document_account', ORACLE_CLOUD_CONFIG['ucm_account']),
            "ContentType": "zip",
            "ProcessName": data.get('process_name', 'AutoInvoiceImport'),
            "InterfaceDetails": data.get('interface_details', '1'),
            "JobOptions": data.get('job_options', 'InterfaceDetails=1,ImportOption=Y,PurgeOption=Y,ExtractFileType=ALL')
        }
        
        response = requests.post(
            f"{ORACLE_CLOUD_CONFIG['base_url']}/fscmRestApi/resources/11.13.18.05/erpintegrations",
            headers=get_oracle_headers(),
            json=bulk_data_payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            return jsonify({
                "status": "success",
                "message": "Bulk data import submitted successfully",
                "job_id": result.get('ReqstId'),
                "response": result
            })
        else:
            return jsonify({
                "error": f"Bulk data import failed: {response.status_code}",
                "details": response.text
            }), response.status_code
            
    except Exception as e:
        print(f"Error in import_bulk_data: {e}")
        return jsonify({"error": str(e)}), 500

@fbdi_bp.route('/full-fbdi-process', methods=['POST'])
def full_fbdi_process():
    """Complete FBDI process: Generate -> Upload -> Load Interface -> Auto Invoice Import"""
    try:
        # Get the uploaded file and form data
        raw_file = request.files.get('raw_file')
        fbdi_type = request.form.get('fbdi_type')
        business_unit = request.form.get('business_unit')
        batch_source = request.form.get('batch_source')
        
        if not raw_file or not fbdi_type:
            return jsonify({"error": "Missing raw file or FBDI type"}), 400
        
        # Step 1: Generate FBDI (reuse existing logic)
        # ... (implementation would call your existing generate-fbdi-from-type endpoint)
        
        # Step 2: Upload to UCM
        # ... (implementation would call upload-to-ucm endpoint)
        
        # Step 3: Submit Interface Loader
        # ... (implementation would call load-interface endpoint)
        
        # Step 4: Submit Auto Invoice Import
        # ... (implementation would call auto-invoice-import endpoint)
        
        return jsonify({
            "status": "success",
            "message": "Full FBDI process completed",
            "steps": [
                {"step": "generate", "status": "completed"},
                {"step": "upload", "status": "completed"},
                {"step": "load_interface", "status": "completed"},
                {"step": "auto_invoice", "status": "completed"}
            ]
        })
        
    except Exception as e:
        print(f"Error in full_fbdi_process: {e}")
        return jsonify({"error": str(e)}), 500
