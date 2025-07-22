from flask import Blueprint, request, jsonify, send_file
from flask_cors import cross_origin
import base64
import requests
import json
import time
from datetime import datetime, timedelta
import os
import tempfile

fbdi_bp = Blueprint('fbdi', __name__)

# Oracle Cloud Configuration
ORACLE_CLOUD_CONFIG = {
    'base_url': 'https://miterbrands-ibayqy-test.fa.ocs.oraclecloud.com',
    'username': 'FUSTST.CONVERSION',
    'password': 'M1terFu81tcO%n',
    'ucm_account': 'fin$/recievables$/import$',
    'ess_service_url': '/fscmService/ErpIntegrationService'
}

def get_oracle_headers():
    """Get headers for Oracle Cloud REST API calls"""
    credentials = f"{ORACLE_CLOUD_CONFIG['username']}:{ORACLE_CLOUD_CONFIG['password']}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
    
    return {
        'Authorization': f'Basic {encoded_credentials}',
        'Content-Type': 'application/vnd.oracle.adf.resourceitem+json'
    }

def poll_job_status(req_id, timeout=600, poll_interval=15):
    """Poll job status until completion"""
    base_url = ORACLE_CLOUD_CONFIG['base_url']
    headers = get_oracle_headers()
    elapsed = 0
    
    while elapsed < timeout:
        try:
            status_resp = requests.get(
                f"{base_url}/fscmRestApi/resources/11.13.18.05/erpintegrations",
                headers=headers,
                params={'finder': f"ESSJobStatusRF;requestId={req_id}"},
                timeout=30
            )
            
            if status_resp.status_code == 200:
                items = status_resp.json().get("items", [])
                if items:
                    job_status = items[0]
                    status = job_status.get('RequestStatus', '')
                    
                    if status in ['SUCCEEDED', 'WARNING', 'ERROR', 'FAILED']:
                        return job_status
                    
                    print(f"Job {req_id} status: {status}, waiting...")
            
            time.sleep(poll_interval)
            elapsed += poll_interval
            
        except Exception as e:
            print(f"Error polling job {req_id}: {e}")
            time.sleep(poll_interval)
            elapsed += poll_interval
    
    return None

def get_oracle_config():
    """Get Oracle Cloud configuration"""
    return ORACLE_CLOUD_CONFIG

@fbdi_bp.route('/upload-to-ucm', methods=['POST', 'OPTIONS'])
@cross_origin()
def upload_to_ucm():
    """Upload generated FBDI file to Oracle UCM"""
    if request.method == 'OPTIONS':
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
        
        ucm_payload = {
            "OperationName": "uploadFileToUCM",
            "DocumentContent": data['document_content'],
            "DocumentAccount": data.get('document_account', ORACLE_CLOUD_CONFIG['ucm_account']),
            "ContentType": "zip",
            "FileName": data['file_name'],
            "DocumentId": None
        }
        
        response = requests.post(
            f"{ORACLE_CLOUD_CONFIG['base_url']}/fscmRestApi/resources/11.13.18.05/erpintegrations",
            headers=get_oracle_headers(),
            json=ucm_payload,
            timeout=30
        )
        
        if response.status_code in [200, 201]:
            result = response.json()
            return jsonify({
                "status": "success",
                "message": "File uploaded to UCM successfully",
                "document_id": result.get('DocumentId'),
                "response": result
            }), 201
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
        
        if response.status_code in [200, 201]:
            result = response.json()
            return jsonify({
                "status": "success",
                "message": "Interface Loader job submitted successfully",
                "job_id": result.get('ReqstId'),
                "response": result
            }), 201
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
        
        if response.status_code in [200, 201]:
            result = response.json()
            return jsonify({
                "status": "success",
                "message": "Auto Invoice Import job submitted successfully",
                "job_id": result.get('ReqstId'),
                "response": result
            }), 201
        else:
            return jsonify({
                "error": f"Auto Invoice Import job failed: {response.status_code}",
                "details": response.text
            }), response.status_code
            
    except Exception as e:
        print(f"Error in auto_invoice_import: {e}")
        return jsonify({"error": str(e)}), 500

@fbdi_bp.route('/complete-fbdi-workflow', methods=['POST', 'OPTIONS'])
@cross_origin()
def complete_fbdi_workflow():
    """Complete FBDI workflow: Generate -> Upload -> Load Interface -> Auto Invoice Import"""
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        return response
    
    try:
        # Get form data
        raw_file = request.files.get('raw_file')
        fbdi_type = request.form.get('fbdi_type')
        project_name = request.form.get('project_name')
        env_type = request.form.get('env_type')
        business_unit = request.form.get('business_unit', '300000003170678')
        batch_source = request.form.get('batch_source', 'MILGARD EBS SPREADSHEET')
        gl_date = request.form.get('gl_date', datetime.now().strftime('%Y-%m-%d'))
        
        if not raw_file or not fbdi_type or not project_name or not env_type:
            return jsonify({"error": "Missing required fields"}), 400

        print(f"🚀 Starting Complete FBDI Workflow for {project_name}")
        
        # Step 1: Generate FBDI
        print("📝 Step 1: Generating FBDI...")
        generate_response = requests.post(
            f"http://localhost:5000/generate-fbdi-from-type",
            files={'raw_file': raw_file},
            data={
                'fbdi_type': fbdi_type,
                'project_name': project_name,
                'env_type': env_type
            }
        )
        
        if generate_response.status_code != 200:
            return jsonify({"error": "Failed to generate FBDI"}), 500
        
        fbdi_content = generate_response.content
        fbdi_base64 = base64.b64encode(fbdi_content).decode()
        
        print("✅ Step 1 Complete: FBDI generated")
        
        # Step 2: Upload to UCM
        print("📤 Step 2: Uploading to UCM...")
        upload_response = requests.post(
            f"http://localhost:5000/fbdi/upload-to-ucm",
            json={
                'document_content': fbdi_base64,
                'file_name': f"{project_name}_{fbdi_type}_FBDI.zip",
                'document_account': ORACLE_CLOUD_CONFIG['ucm_account']
            }
        )
        
        if upload_response.status_code != 201:
            return jsonify({"error": "Failed to upload to UCM"}), 500
        
        upload_data = upload_response.json()
        document_id = upload_data.get('document_id')
        
        print(f"✅ Step 2 Complete: Uploaded to UCM, Document ID: {document_id}")
        
        # Step 3: Load Interface
        print("🔄 Step 3: Loading Interface...")
        interface_response = requests.post(
            f"http://localhost:5000/fbdi/load-interface",
            json={'ess_parameters': '2,511142,N,N,N'}
        )
        
        if interface_response.status_code != 201:
            return jsonify({"error": "Failed to load interface"}), 500
        
        interface_data = interface_response.json()
        interface_job_id = interface_data.get('job_id')
        
        print(f"✅ Step 3 Complete: Interface job submitted, Job ID: {interface_job_id}")
        
        # Wait for interface job to complete
        print("⏳ Waiting for Interface Loader to complete...")
        interface_status = poll_job_status(interface_job_id)
        if not interface_status or interface_status['RequestStatus'] not in ['SUCCEEDED', 'WARNING']:
            return jsonify({"error": "Interface Loader job failed"}), 500
        
        print("✅ Interface Loader completed successfully")
        
        # Step 4: Auto Invoice Import
        print("📋 Step 4: Running Auto Invoice Import...")
        ess_parameters = f"{business_unit},{batch_source},{gl_date},,,,,,,,,,,,,,,,,,,,Y,N"
        
        auto_invoice_response = requests.post(
            f"http://localhost:5000/fbdi/auto-invoice-import",
            json={'ess_parameters': ess_parameters}
        )
        
        if auto_invoice_response.status_code != 201:
            return jsonify({"error": "Failed to submit AutoInvoice Import job"}), 500
        
        auto_invoice_data = auto_invoice_response.json()
        autoinvoice_job_id = auto_invoice_data.get('job_id')
        
        print(f"✅ Step 4 Complete: AutoInvoice job submitted, Job ID: {autoinvoice_job_id}")
        
        # Wait for AutoInvoice job to complete
        print("⏳ Waiting for AutoInvoice job to complete...")
        autoinvoice_status = poll_job_status(autoinvoice_job_id)
        if not autoinvoice_status or autoinvoice_status['RequestStatus'] not in ['SUCCEEDED', 'WARNING']:
            return jsonify({
                "error": "AutoInvoice job failed",
                "job_id": autoinvoice_job_id,
                "status": autoinvoice_status.get('RequestStatus') if autoinvoice_status else 'TIMEOUT'
            }), 500
        
        print("✅ AutoInvoice Import completed successfully")
        
        return jsonify({
            "status": "success",
            "message": "Complete FBDI workflow finished successfully",
            "job_ids": {
                "interface_loader": interface_job_id,
                "autoinvoice_import": autoinvoice_job_id
            },
            "project_name": project_name,
            "fbdi_type": fbdi_type,
            "document_id": document_id
        }), 200
        
    except Exception as e:
        print(f"❌ Error in complete_fbdi_workflow: {e}")
        return jsonify({"error": str(e)}), 500

# UTILITY ENDPOINTS

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

@fbdi_bp.route('/list-all-jobs', methods=['GET', 'OPTIONS'])
@cross_origin()
def list_all_jobs():
    """Fetch all job requests submitted"""
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200

    try:
        params = {"finder": "ESSJobStatusRF"}
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

@fbdi_bp.route('/latest-ess-jobs', methods=['GET', 'OPTIONS'])
@cross_origin()
def latest_ess_jobs():
    """Fetch the last few ESS jobs"""
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200

    try:
        params = {"finder": "ESSJobStatusRF"}
        response = requests.get(
            f"{ORACLE_CLOUD_CONFIG['base_url']}/fscmRestApi/resources/11.13.18.05/erpintegrations",
            headers=get_oracle_headers(),
            params=params,
            timeout=30
        )
        if response.status_code == 200:
            items = response.json().get("items", [])
            if not items:
                return jsonify({"jobs": []})

            # Sort by submission date
            items.sort(key=lambda job: job.get("SubmissionDate", ""), reverse=True)

            # Return last 10 jobs
            jobs = []
            for job in items[:10]:
                jobs.append({
                    "ReqstId": job.get("ReqstId"),
                    "JobName": job.get("JobName"),
                    "JobDefName": job.get("JobDefName"),
                    "RequestStatus": job.get("RequestStatus"),
                    "SubmissionDate": job.get("SubmissionDate")
                })

            return jsonify({"jobs": jobs})

        else:
            return jsonify({
                "error": "Failed to fetch jobs",
                "details": response.text
            }), response.status_code

    except Exception as e:
        return jsonify({"error": str(e)}), 500

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
        "message": "FBDI Operations API",
        "oracle_base_url": ORACLE_CLOUD_CONFIG['base_url'],
        "endpoints": [
            "/fbdi/upload-to-ucm",
            "/fbdi/load-interface", 
            "/fbdi/auto-invoice-import",
            "/fbdi/complete-fbdi-workflow",
            "/fbdi/check-job-status/<job_id>",
            "/fbdi/list-all-jobs",
            "/fbdi/latest-ess-jobs"
        ]
    })
