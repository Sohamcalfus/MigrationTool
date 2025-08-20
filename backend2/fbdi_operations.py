from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
import base64
import requests
import time
from datetime import datetime
 
 
fbdi_bp = Blueprint('fbdi', __name__)
 
    
ORACLE_CLOUD_CONFIG = {
    'base_url': 'https://fa-eqje-dev7-saasfademo1.ds-fa.oraclepdemos.com:443/',
    'username': 'Harsh.Itkar',
    'password': 'Welcome@123',
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
 
 
def poll_job_status(request_id, job_name, timeout=600, interval=10):
    """Poll an ESS job until it reaches a terminal status with status updates."""
    url = ORACLE_CLOUD_CONFIG['base_url'] + ORACLE_CLOUD_CONFIG['ess_service_url']
    headers = get_oracle_headers()
    elapsed = 0
   
    print(f"\n{'='*60}")
    print(f"Starting to monitor {job_name} (Job ID: {request_id})")
    print(f"{'='*60}")
 
    while elapsed < timeout:
        resp = requests.get(url,
            headers=headers,
            params={'finder': f"ESSJobStatusRF;requestId={request_id}"},
            timeout=30)
       
        if resp.ok:
            items = resp.json().get('items', [])
            if items:
                status_info = items[0]
                status = status_info.get('RequestStatus')
                phase = status_info.get('RequestPhase', 'N/A')
                state = status_info.get('RequestState', 'N/A')
               
                # Print current status with timestamp
                current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                print(f"[{current_time}] {job_name} Status:")
                print(f"  └─ Status: {status}")
                print(f"  └─ Phase: {phase}")
                print(f"  └─ State: {state}")
                print(f"  └─ Elapsed Time: {elapsed} seconds")
               
                if status in ('SUCCEEDED','WARNING','ERROR','FAILED'):
                    print(f"\n🎯 {job_name} completed with status: {status}")
                    if status in ('SUCCEEDED','WARNING'):
                        print("✅ Job completed successfully!")
                    else:
                        print("❌ Job failed!")
                    print(f"{'='*60}\n")
                    return status_info
                   
                print(f"  └─ Still running... (will check again in {interval} seconds)")
                print("-" * 40)
        else:
            print(f"[ERROR] Failed to get status for {job_name}: {resp.text}")
           
        time.sleep(interval)
        elapsed += interval
 
    print(f"\n⏰ TIMEOUT: {job_name} did not complete within {timeout} seconds")
    print(f"{'='*60}\n")
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
 
    print(f"\n🚀 Starting FBDI Processing Pipeline at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
 
    # 1) Validate inputs
    print("📋 Step 1: Validating inputs...")
    fbdi_file = request.files.get('fbdi_file')
    if not fbdi_file:
        print("❌ ERROR: Missing field 'fbdi_file'")
        return jsonify({"error":"Missing field 'fbdi_file'"}), 400
 
    business_unit = request.form.get('business_unit','300000003170678')
    batch_source  = request.form.get('batch_source','MILGARD EBS SPREADSHEET')
    gl_date       = request.form.get('gl_date', datetime.now().strftime('%Y-%m-%d'))
   
    print(f"✅ Inputs validated:")
    print(f"  └─ File: {fbdi_file.filename}")
    print(f"  └─ Business Unit: {business_unit}")
    print(f"  └─ Batch Source: {batch_source}")
    print(f"  └─ GL Date: {gl_date}")
 
    # Read & base64‐encode FBDI
    print("\n📁 Reading and encoding file...")
    content = fbdi_file.read()
    b64 = base64.b64encode(content).decode()
    print(f"✅ File encoded successfully (Size: {len(content)} bytes)")
 
    # 2) Upload to UCM
    print(f"\n📤 Step 2: Uploading to UCM...")
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
    print(f"🔄 Uploading file: {ucm_filename}")
    upload_resp = requests.post(url,
        headers=get_oracle_headers(),
        json=ucm_payload,
        timeout=60)
   
    if not upload_resp.ok:
        print(f"❌ Upload failed: {upload_resp.text}")
        return jsonify({"step":"upload","error":upload_resp.text}), upload_resp.status_code
 
    document_id = upload_resp.json().get('DocumentId')
    print(f"✅ File uploaded successfully!")
    print(f"  └─ Document ID: {document_id}")
    print(f"  └─ UCM Filename: {ucm_filename}")
 
    # 3) Submit Interface Loader
    print(f"\n🔧 Step 3: Submitting Interface Loader...")
    ess_if_payload = {
        "OperationName": "submitESSJobRequest",
        "JobPackageName": "oracle/apps/ess/financials/commonModules/shared/common/interfaceLoader",
        "JobDefName": "InterfaceLoaderController",
        "ESSParameters": f"2,{document_id},N,N,N"
    }
   
    print("🔄 Submitting Interface Loader job...")
    if_resp = requests.post(url,
        headers=get_oracle_headers(),
        json=ess_if_payload,
        timeout=30)
   
    if not if_resp.ok:
        print(f"❌ Interface Loader submission failed: {if_resp.text}")
        return jsonify({"step":"interface_submit","error":if_resp.text}), if_resp.status_code
 
    interface_job_id = if_resp.json().get('ReqstId')
    print(f"✅ Interface Loader submitted successfully!")
    print(f"  └─ Job ID: {interface_job_id}")
   
    # Poll Interface Loader status
    interface_status = poll_job_status(interface_job_id, "Interface Loader")
    if not interface_status or interface_status['RequestStatus'] not in ('SUCCEEDED','WARNING'):
        final_status = interface_status.get('RequestStatus') if interface_status else 'TIMEOUT'
        print(f"❌ Interface Loader failed with status: {final_status}")
        return jsonify({
            "step":"interface_poll",
            "job_id":interface_job_id,
            "status": final_status
        }), 500
 
    print(f"✅ Interface Loader completed successfully with status: {interface_status['RequestStatus']}")
 
    # 4) Submit Auto Invoice Import
    print(f"\n💰 Step 4: Submitting Auto Invoice Import...")
    ess_ai_payload = {
        "OperationName": "submitESSJobRequest",
        "JobPackageName": "/oracle/apps/ess/financials/receivables/transactions/autoInvoices/",
        "JobDefName": "AutoInvoiceImportEss",
        "ESSParameters": f"{business_unit},{batch_source},{gl_date},,,,,,,,,,,,,,,,,,,,Y,N"
    }
   
    print("🔄 Submitting Auto Invoice Import job...")
    ai_resp = requests.post(url,
        headers=get_oracle_headers(),
        json=ess_ai_payload,
        timeout=30)
   
    if not ai_resp.ok:
        print(f"❌ Auto Invoice Import submission failed: {ai_resp.text}")
        return jsonify({"step":"autoinvoice_submit","error":ai_resp.text}), ai_resp.status_code
 
    autoinvoice_job_id = ai_resp.json().get('ReqstId')
    print(f"✅ Auto Invoice Import submitted successfully!")
    print(f"  └─ Job ID: {autoinvoice_job_id}")
   
    # Poll Auto Invoice Import status
    invoice_status = poll_job_status(autoinvoice_job_id, "Auto Invoice Import")
    if not invoice_status or invoice_status['RequestStatus'] not in ('SUCCEEDED','WARNING'):
        final_status = invoice_status.get('RequestStatus') if invoice_status else 'TIMEOUT'
        print(f"❌ Auto Invoice Import failed with status: {final_status}")
        return jsonify({
            "step":"autoinvoice_poll",
            "job_id":autoinvoice_job_id,
            "status": final_status
        }), 500
 
    print(f"✅ Auto Invoice Import completed successfully with status: {invoice_status['RequestStatus']}")
 
    # 5) Success
    print(f"\n🎉 SUCCESS: All operations completed successfully!")
    print(f"Pipeline completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
   
    return jsonify({
        "status":"success",
        "document_id": document_id,
        "ucm_filename": ucm_filename,
        "interface_job_id": interface_job_id,
        "interface_status": interface_status['RequestStatus'],
        "autoinvoice_job_id": autoinvoice_job_id,
        "autoinvoice_status": invoice_status['RequestStatus']
    }), 200