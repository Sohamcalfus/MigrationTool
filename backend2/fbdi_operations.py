from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
import base64
import requests
import time
from datetime import datetime

fbdi_bp = Blueprint('fbdi', __name__)

ORACLE_CLOUD_CONFIG = {
    'base_url': 'https://miterbrands-ibayqy-test.fa.ocs.oraclecloud.com',
    'username': 'FUSTST.CONVERSION',
    'password': 'Conversion@2025',
    'ucm_account': 'fin$/recievables$/import$',
    'ess_service_url': '/fscmRestApi/resources/11.13.18.05/erpintegrations'
}

def get_oracle_headers():
    creds = f"{ORACLE_CLOUD_CONFIG['username']}:{ORACLE_CLOUD_CONFIG['password']}"
    token = base64.b64encode(creds.encode()).decode()
    return {
        'Authorization': f'Basic {token}',
        'Content-Type': 'application/vnd.oracle.adf.resourceitem+json'
    }

def poll_job_status(request_id, timeout=600, interval=10):
    """Poll an ESS job until it reaches a terminal status."""
    url = ORACLE_CLOUD_CONFIG['base_url'] + ORACLE_CLOUD_CONFIG['ess_service_url']
    headers = get_oracle_headers()
    elapsed = 0

    while elapsed < timeout:
        resp = requests.get(url,
            headers=headers,
            params={'finder': f"ESSJobStatusRF;requestId={request_id}"},
            timeout=30)
        if resp.ok:
            items = resp.json().get('items', [])
            if items:
                status = items[0].get('RequestStatus')
                if status in ('SUCCEEDED','WARNING','ERROR','FAILED'):
                    return items[0]
        time.sleep(interval)
        elapsed += interval

    return None

@fbdi_bp.route('/process-fbdi', methods=['POST','OPTIONS'])
@cross_origin()
def process_fbdi():
    """
    Single‐shot endpoint:
    1) Uploads the posted FBDI ZIP to UCM
    2) Submits Interface Loader (using the returned documentId)
    3) Submits Auto Invoice Import
    4) Polls each to completion
    """
    if request.method == 'OPTIONS':
        resp = jsonify({'status':'ok'})
        resp.headers.update({
            'Access-Control-Allow-Origin':'*',
            'Access-Control-Allow-Headers':'Content-Type',
            'Access-Control-Allow-Methods':'POST,OPTIONS'
        })
        return resp

    # 1) Validate inputs
    fbdi_file = request.files.get('fbdi_file')
    if not fbdi_file:
        return jsonify({"error":"Missing field 'fbdi_file'"}), 400

    business_unit = request.form.get('business_unit','300000003170678')
    batch_source  = request.form.get('batch_source','MILGARD EBS SPREADSHEET')
    gl_date       = request.form.get('gl_date', datetime.now().strftime('%Y-%m-%d'))

    # Read & base64‐encode FBDI
    content = fbdi_file.read()
    b64 = base64.b64encode(content).decode()

    # 2) Upload to UCM
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    ucm_filename = f"RaInterfaceLinesAll{timestamp}.zip"
    ucm_payload = {
        "OperationName":   "uploadFileToUCM",
        "DocumentContent": b64,
        "DocumentAccount": ORACLE_CLOUD_CONFIG['ucm_account'],
        "ContentType":     "zip",
        "FileName":        ucm_filename,
        "DocumentId":      None
    }

    url = ORACLE_CLOUD_CONFIG['base_url'] + ORACLE_CLOUD_CONFIG['ess_service_url']
    upload_resp = requests.post(url,
        headers=get_oracle_headers(),
        json=ucm_payload,
        timeout=60)
    if not upload_resp.ok:
        return jsonify({"step":"upload","error":upload_resp.text}), upload_resp.status_code

    document_id = upload_resp.json().get('DocumentId')

    # 3) Submit Interface Loader
    ess_if_payload = {
        "OperationName": "submitESSJobRequest",
        "JobPackageName": "oracle/apps/ess/financials/commonModules/shared/common/interfaceLoader",
        "JobDefName": "InterfaceLoaderController",
        "ESSParameters": f"2,{document_id},N,N,N"
    }
    if_resp = requests.post(url,
        headers=get_oracle_headers(),
        json=ess_if_payload,
        timeout=30)
    if not if_resp.ok:
        return jsonify({"step":"interface_submit","error":if_resp.text}), if_resp.status_code

    interface_job_id = if_resp.json().get('ReqstId')
    interface_status = poll_job_status(interface_job_id)
    if not interface_status or interface_status['RequestStatus'] not in ('SUCCEEDED','WARNING'):
        return jsonify({
            "step":"interface_poll",
            "job_id":interface_job_id,
            "status": interface_status.get('RequestStatus') if interface_status else 'TIMEOUT'
        }), 500

    # 4) Submit Auto Invoice Import
    ess_ai_payload = {
        "OperationName": "submitESSJobRequest",
        "JobPackageName": "/oracle/apps/ess/financials/receivables/transactions/autoInvoices/",
        "JobDefName": "AutoInvoiceImportEss",
        "ESSParameters": f"{business_unit},{batch_source},{gl_date},,,,,,,,,,,,,,,,,,,,Y,N"
    }
    ai_resp = requests.post(url,
        headers=get_oracle_headers(),
        json=ess_ai_payload,
        timeout=30)
    if not ai_resp.ok:
        return jsonify({"step":"autoinvoice_submit","error":ai_resp.text}), ai_resp.status_code

    autoinvoice_job_id = ai_resp.json().get('ReqstId')
    invoice_status = poll_job_status(autoinvoice_job_id)
    if not invoice_status or invoice_status['RequestStatus'] not in ('SUCCEEDED','WARNING'):
        return jsonify({
            "step":"autoinvoice_poll",
            "job_id":autoinvoice_job_id,
            "status": invoice_status.get('RequestStatus') if invoice_status else 'TIMEOUT'
        }), 500

    # 5) Success
    return jsonify({
        "status":"success",
        "document_id": document_id,
        "ucm_filename": ucm_filename,
        "interface_job_id": interface_job_id,
        "interface_status": interface_status['RequestStatus'],
        "autoinvoice_job_id": autoinvoice_job_id,
        "autoinvoice_status": invoice_status['RequestStatus']
    }), 200
