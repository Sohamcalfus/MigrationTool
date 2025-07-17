from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
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

@fbdi_bp.route('/upload-to-ucm', methods=['POST', 'OPTIONS'])
@cross_origin()
def upload_to_ucm():
    """Upload generated FBDI file to Oracle UCM"""
    if request.method == 'OPTIONS':
        # Handle preflight request
        response = jsonify({'status': 'ok'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        return response
    
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

@fbdi_bp.route('/load-interface', methods=['POST', 'OPTIONS'])
@cross_origin()
def load_interface():
    """Submit Interface Loader job"""
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        return response
    
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

@fbdi_bp.route('/auto-invoice-import', methods=['POST', 'OPTIONS'])
@cross_origin()
def auto_invoice_import():
    """Submit Auto Invoice Import job"""
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        return response
    
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

@fbdi_bp.route('/check-job-status/<job_id>', methods=['GET', 'OPTIONS'])
@cross_origin()
def check_job_status(job_id):
    """Check the status of a submitted job"""
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        return response
    
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

# Add a health check endpoint for the FBDI operations
@fbdi_bp.route('/health', methods=['GET', 'OPTIONS'])
@cross_origin()
def health_check():
    """Health check endpoint"""
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        return response
    
    return jsonify({
        "status": "ok",
        "message": "FBDI Operations API is running",
        "oracle_base_url": ORACLE_CLOUD_CONFIG['base_url']
    })

@fbdi_bp.route('/list-all-jobs', methods=['GET', 'OPTIONS'])
@cross_origin()
def list_all_jobs():
    """
    Fetch all job requests submitted.
    You can enhance this with pagination/filters as needed.
    """
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200

    try:
        # Optionally filter jobs by status, start date, etc.
        params = {
            "finder": "ESSJobStatusRF"
        }
        oracle_config = get_oracle_config()
        response = requests.get(
            f"{oracle_config['base_url']}/fscmRestApi/resources/11.13.18.05/erpintegrations",
            headers=get_oracle_headers(),
            params=params,
            timeout=30
        )
        if response.status_code == 200:
            items = response.json().get("items", [])
            job_list = []
            for item in items:
                job_list.append({
                    "ReqstId": item.get("ReqstId"),
                    "JobName": item.get("JobName"),
                    "RequestStatus": item.get("RequestStatus"),
                    "JobSetName": item.get("JobSetName"),
                    "SubmissionDate": item.get("SubmissionDate")
                })
            return jsonify({"jobs": job_list})
        else:
            return jsonify({"error": "Failed to fetch jobs", "details": response.text}), response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@fbdi_bp.route('/autoinvoice-execution-report/<auto_invoice_job_id>', methods=['GET', 'OPTIONS'])
@cross_origin()
def get_autoinvoice_execution_report(auto_invoice_job_id):
    """
    Fetch the execution report job Request ID(s) related to a given AutoInvoiceImportEss job Request ID.
    """
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200

    try:
        # Oracle API base URL & headers
        base_url = ORACLE_CLOUD_CONFIG['base_url']
        headers = get_oracle_headers()

        # First, validate the AutoInvoiceImportEss job exists (optional)
        params = {
            "finder": f"ESSJobStatusRF;requestId={auto_invoice_job_id}"
        }

        resp = requests.get(
            f"{base_url}/fscmRestApi/resources/11.13.18.05/erpintegrations",
            headers=headers,
            params=params,
            timeout=30
        )

        if resp.status_code != 200:
            return jsonify({
                "error": "Failed to find AutoInvoiceImportEss job",
                "details": resp.text
            }), resp.status_code

        job_info = resp.json().get('items', [])
        if not job_info:
            return jsonify({
                "error": f"AutoInvoiceImportEss job with ID '{auto_invoice_job_id}' not found"
            }), 404

        # Query for execution report jobs related to this job
        # Usually, Oracle Cloud links related jobs via 'ParentRequestId' or similar; 
        # but if not available, you may have to rely on JobName/JobDefName + SubmissionDate filtering
        # Check if 'ParentRequestId' exists in job items to use as filter
        # Here, we try to find jobs with ParentRequestId = auto_invoice_job_id

        params_report = {
            "finder": f"ESSJobStatusRF;parentRequestId={auto_invoice_job_id}"
        }

        resp_report = requests.get(
            f"{base_url}/fscmRestApi/resources/11.13.18.05/erpintegrations",
            headers=headers,
            params=params_report,
            timeout=30
        )

        if resp_report.status_code != 200:
            return jsonify({
                "error": "Failed to fetch execution report jobs",
                "details": resp_report.text
            }), resp_report.status_code

        report_items = resp_report.json().get('items', [])

        if not report_items:
            # If ParentRequestId filtering doesn't work, attempt alternative approach:
            # For example, filter jobs by JobName = 'AutoInvoiceImportEss' + suffix or similar
            # Or time-based proximity filtering

            return jsonify({
                "message": "No execution report jobs found for given AutoInvoiceImportEss request ID"
            }), 200

        # Return list of report job Request IDs
        reports = []
        for report_job in report_items:
            reports.append({
                "ReqstId": report_job.get("ReqstId"),
                "JobName": report_job.get("JobName"),
                "RequestStatus": report_job.get("RequestStatus"),
                "SubmissionDate": report_job.get("SubmissionDate")
            })

        return jsonify({
            "auto_invoice_job_id": auto_invoice_job_id,
            "execution_reports": reports
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500
