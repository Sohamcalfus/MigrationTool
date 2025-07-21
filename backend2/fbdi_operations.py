from flask import Blueprint, request, jsonify, send_file
from flask_cors import cross_origin
import base64
import requests
import json
import time
from datetime import datetime, timedelta
import os
import tempfile
from xml.etree import ElementTree as ET
import xml.dom.minidom

fbdi_bp = Blueprint('fbdi', __name__)

# Oracle Cloud Configuration
ORACLE_CLOUD_CONFIG = {
    'base_url': 'https://miterbrands-ibayqy-test.fa.ocs.oraclecloud.com',
    'username': 'FUSTST.CONVERSION',
    'password': 'M1terFu81tcO%n',
    'ucm_account': 'fin$/recievables$/import$',
    'ess_service_url': '/fscmService/ErpIntegrationService',
    'bi_service_url': '/xmlpserver/services/v2/ReportService'
}

def get_oracle_headers():
    """Get headers for Oracle Cloud REST API calls"""
    credentials = f"{ORACLE_CLOUD_CONFIG['username']}:{ORACLE_CLOUD_CONFIG['password']}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
    
    return {
        'Authorization': f'Basic {encoded_credentials}',
        'Content-Type': 'application/vnd.oracle.adf.resourceitem+json'
    }

def get_soap_headers():
    """Get headers for SOAP API calls"""
    credentials = f"{ORACLE_CLOUD_CONFIG['username']}:{ORACLE_CLOUD_CONFIG['password']}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
    
    return {
        'Authorization': f'Basic {encoded_credentials}',
        'Content-Type': 'text/xml; charset=utf-8',
        'SOAPAction': ''
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

def get_child_job_enhanced_rest_api(parent_request_id, report_path):
    """Enhanced method to find child job using REST API with better error handling"""
    try:
        base_url = ORACLE_CLOUD_CONFIG['base_url']
        headers = get_oracle_headers()
        
        print(f"🔍 Searching for child jobs using enhanced REST API method...")
        
        # Get all recent jobs (last 24 hours)
        all_jobs_resp = requests.get(
            f"{base_url}/fscmRestApi/resources/11.13.18.05/erpintegrations",
            headers=headers,
            params={'finder': 'ESSJobStatusRF'},
            timeout=30
        )
        
        if all_jobs_resp.status_code == 200:
            all_jobs = all_jobs_resp.json().get("items", [])
            print(f"📊 Found {len(all_jobs)} total jobs, filtering for child jobs...")
            
            # Look for potential child jobs
            potential_child_jobs = []
            
            for job in all_jobs:
                job_name = job.get("JobName", "") or ""
                job_def = job.get("JobDefName", "") or ""
                submission_date = job.get("SubmissionDate", "") or ""
                job_id = job.get("ReqstId", "") or ""
                
                # More comprehensive search patterns
                search_patterns = [
                    "AUTOINVOICE" in job_name.upper(),
                    "AUTO_INVOICE" in job_name.upper(),
                    "CHILD" in job_name.upper(),
                    "REPORT" in job_name.upper(),
                    "GENERATE" in job_name.upper(),
                    "EXECUTION" in job_name.upper(),
                    report_path.split('/')[-1].replace('.xdo', '').upper() in job_name.upper()
                ]
                
                if any(search_patterns):
                    potential_child_jobs.append({
                        'child_job_id': job_id,
                        'job_name': job_name,
                        'job_def': job_def,
                        'submission_date': submission_date,
                        'parent_request_id': parent_request_id,
                        'score': sum(search_patterns)  # Relevance score
                    })
            
            if potential_child_jobs:
                # Sort by relevance score and then by submission date
                potential_child_jobs.sort(key=lambda x: (x['score'], x['submission_date']), reverse=True)
                
                print(f"✅ Found {len(potential_child_jobs)} potential child jobs")
                for job in potential_child_jobs[:3]:  # Show top 3
                    print(f"   - {job['job_name']} (ID: {job['child_job_id']}, Score: {job['score']})")
                
                return potential_child_jobs[0]  # Return best match
        
        return None
        
    except Exception as e:
        print(f"❌ Error in enhanced REST API method: {e}")
        return None

def get_child_job_by_time_proximity(parent_request_id, parent_submission_time=None):
    """Find child job by looking for jobs submitted shortly after parent job"""
    try:
        base_url = ORACLE_CLOUD_CONFIG['base_url']
        headers = get_oracle_headers()
        
        print(f"🕐 Searching for child jobs by time proximity...")
        
        # If we don't have parent submission time, get it first
        if not parent_submission_time:
            parent_job_resp = requests.get(
                f"{base_url}/fscmRestApi/resources/11.13.18.05/erpintegrations",
                headers=headers,
                params={'finder': f"ESSJobStatusRF;requestId={parent_request_id}"},
                timeout=30
            )
            
            if parent_job_resp.status_code == 200:
                parent_items = parent_job_resp.json().get("items", [])
                if parent_items:
                    parent_submission_time = parent_items[0].get("SubmissionDate", "")
        
        if not parent_submission_time:
            print("❌ Could not determine parent job submission time")
            return None
        
        # Get all jobs
        all_jobs_resp = requests.get(
            f"{base_url}/fscmRestApi/resources/11.13.18.05/erpintegrations",
            headers=headers,
            params={'finder': 'ESSJobStatusRF'},
            timeout=30
        )
        
        if all_jobs_resp.status_code == 200:
            all_jobs = all_jobs_resp.json().get("items", [])
            
            # Find jobs submitted after parent job (within 1 hour)
            try:
                from datetime import datetime
                parent_time = datetime.fromisoformat(parent_submission_time.replace('Z', '+00:00'))
                time_window_end = parent_time + timedelta(hours=1)
                
                child_candidates = []
                
                for job in all_jobs:
                    job_submission = job.get("SubmissionDate", "")
                    job_name = job.get("JobName", "") or ""
                    
                    if job_submission:
                        try:
                            job_time = datetime.fromisoformat(job_submission.replace('Z', '+00:00'))
                            
                            # Check if job was submitted after parent and within time window
                            if parent_time < job_time <= time_window_end:
                                # Check if job name suggests it's related to AutoInvoice reporting
                                if any(keyword in job_name.upper() for keyword in ['REPORT', 'EXECUTION', 'AUTOINVOICE', 'CHILD']):
                                    child_candidates.append({
                                        'child_job_id': job.get("ReqstId"),
                                        'job_name': job_name,
                                        'submission_date': job_submission,
                                        'time_diff': (job_time - parent_time).total_seconds()
                                    })
                        except:
                            continue
                
                if child_candidates:
                    # Sort by time difference (closest to parent job)
                    child_candidates.sort(key=lambda x: x['time_diff'])
                    print(f"✅ Found {len(child_candidates)} time-based child job candidates")
                    return child_candidates[0]
                    
            except Exception as time_error:
                print(f"❌ Error in time-based search: {time_error}")
        
        return None
        
    except Exception as e:
        print(f"❌ Error in time proximity method: {e}")
        return None

def get_child_job_by_parent_relationship(parent_request_id):
    """Try to find child job using parent-child relationship in REST API"""
    try:
        base_url = ORACLE_CLOUD_CONFIG['base_url']
        headers = get_oracle_headers()
        
        print(f"👨‍👧‍👦 Searching for child jobs using parent-child relationship...")
        
        # Try different finder patterns for parent-child relationships
        parent_finders = [
            f"ESSJobStatusRF;parentRequestId={parent_request_id}",
            f"ESSJobStatusRF;rootRequestId={parent_request_id}",
            f"ESSJobStatusRF;requestSetId={parent_request_id}"
        ]
        
        for finder in parent_finders:
            try:
                resp = requests.get(
                    f"{base_url}/fscmRestApi/resources/11.13.18.05/erpintegrations",
                    headers=headers,
                    params={'finder': finder},
                    timeout=30
                )
                
                if resp.status_code == 200:
                    items = resp.json().get("items", [])
                    if items:
                        print(f"✅ Found {len(items)} related jobs using finder: {finder}")
                        for item in items:
                            job_name = item.get("JobName", "") or ""
                            if any(keyword in job_name.upper() for keyword in ['REPORT', 'EXECUTION', 'AUTOINVOICE']):
                                return {
                                    'child_job_id': item.get("ReqstId"),
                                    'job_name': job_name,
                                    'submission_date': item.get("SubmissionDate", ""),
                                    'found_via': finder
                                }
            except Exception as finder_error:
                print(f"❌ Finder {finder} failed: {finder_error}")
                continue
        
        return None
        
    except Exception as e:
        print(f"❌ Error in parent-child relationship method: {e}")
        return None

def fetch_child_job_comprehensive(parent_request_id, report_path):
    """Comprehensive method to fetch child job ID using multiple robust approaches"""
    
    print(f"🔍 Starting comprehensive search for child job")
    print(f"🎯 Parent ID: {parent_request_id}")
    print(f"📄 Report Path: {report_path}")
    
    # Method 1: Enhanced REST API search
    print("\n🔄 Method 1: Enhanced REST API search...")
    child_job = get_child_job_enhanced_rest_api(parent_request_id, report_path)
    if child_job:
        print(f"✅ Method 1 SUCCESS: Found child job: {child_job['child_job_id']}")
        return child_job
    
    # Method 2: Parent-child relationship
    print("\n🔄 Method 2: Parent-child relationship search...")
    child_job = get_child_job_by_parent_relationship(parent_request_id)
    if child_job:
        print(f"✅ Method 2 SUCCESS: Found child job: {child_job['child_job_id']}")
        return child_job
    
    # Method 3: Time proximity search
    print("\n🔄 Method 3: Time proximity search...")
    child_job = get_child_job_by_time_proximity(parent_request_id)
    if child_job:
        print(f"✅ Method 3 SUCCESS: Found child job: {child_job['child_job_id']}")
        return child_job
    
    # Method 4: SOAP API (keep as last resort)
    print("\n🔄 Method 4: SOAP API (last resort)...")
    try:
        child_job = get_child_job_id_soap(parent_request_id, report_path)
        if child_job:
            print(f"✅ Method 4 SUCCESS: Found child job: {child_job['child_job_id']}")
            return child_job
    except Exception as soap_error:
        print(f"❌ Method 4 FAILED: SOAP error: {soap_error}")
    
    print("❌ ALL METHODS FAILED: No child job found")
    return None

def get_child_job_id_soap(parent_request_id, report_path):
    """Fetch child job ID using SOAP API with better error handling"""
    
    soap_envelope = f"""<?xml version="1.0" encoding="UTF-8"?>
    <soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"
                   xmlns:typ="http://xmlns.oracle.com/apps/financials/commonModules/shared/model/erpIntegrationService/types/">
        <soap:Header/>
        <soap:Body>
            <typ:getESSJobStatus>
                <typ:requestId>{parent_request_id}</typ:requestId>
                <typ:includeChildJobs>true</typ:includeChildJobs>
            </typ:getESSJobStatus>
        </soap:Body>
    </soap:Envelope>"""
    
    try:
        response = requests.post(
            f"{ORACLE_CLOUD_CONFIG['base_url']}{ORACLE_CLOUD_CONFIG['ess_service_url']}",
            headers=get_soap_headers(),
            data=soap_envelope,
            timeout=60
        )
        
        print(f"🌐 SOAP Response Status: {response.status_code}")
        print(f"📝 SOAP Response Content (first 200 chars): {response.text[:200]}")
        
        if response.status_code == 200:
            # Check if response is valid XML
            try:
                root = ET.fromstring(response.content)
                
                # Look for child jobs in response
                for elem in root.iter():
                    if 'childJob' in elem.tag.lower() or 'child' in elem.tag.lower():
                        job_name = ""
                        request_id = ""
                        
                        # Extract job details
                        for child in elem:
                            if 'jobname' in child.tag.lower():
                                job_name = child.text
                            elif 'requestid' in child.tag.lower():
                                request_id = child.text
                        
                        # Check if this matches our report
                        if 'AUTOINVOICE_CHILD_ESS_JOB_REPORT' in job_name or report_path.split('/')[-1].replace('.xdo', '') in job_name:
                            return {
                                'child_job_id': request_id,
                                'job_name': job_name,
                                'report_path': report_path,
                                'parent_request_id': parent_request_id
                            }
            except ET.ParseError as parse_error:
                print(f"❌ SOAP XML Parse Error: {parse_error}")
                print(f"📝 Raw Response: {response.text}")
        
        return None
        
    except Exception as e:
        print(f"❌ SOAP call error: {e}")
        return None

def download_execution_report_from_child(child_job_id, parent_request_id):
    """Download the actual execution report using child job ID with multiple fallback methods"""
    
    try:
        base_url = ORACLE_CLOUD_CONFIG['base_url']
        headers = get_oracle_headers()
        
        print(f"📊 Downloading execution report for child job: {child_job_id}")
        
        # Method 1: Standard job output (most likely to work)
        print("🔄 Trying Method 1: Standard ESS job output...")
        standard_output_url = f"{base_url}/fscmRestApi/resources/11.13.18.05/erpintegrations/{child_job_id}/output"
        
        standard_response = requests.get(
            standard_output_url,
            headers=headers,
            timeout=60,
            stream=True
        )
        
        if standard_response.status_code == 200:
            print("✅ Downloaded report via standard ESS output")
            return standard_response
        
        # Method 2: Try with execution report path
        print("🔄 Trying Method 2: ESS execution report endpoint...")
        exec_report_url = f"{base_url}/fscmRestApi/resources/11.13.18.05/erpintegrations/{child_job_id}/executionReport"
        
        exec_response = requests.get(
            exec_report_url,
            headers=headers,
            timeout=60,
            stream=True
        )
        
        if exec_response.status_code == 200:
            print("✅ Downloaded execution report via ESS API")
            return exec_response
        
        # Method 3: Try BI Publisher approach
        print("🔄 Trying Method 3: BI Publisher REST API...")
        bi_report_url = f"{base_url}/xmlpserver/rest/v1/reports"
        
        # Generic BI Publisher job output request
        bi_response = requests.get(
            f"{bi_report_url}/{child_job_id}",
            headers=headers,
            timeout=60,
            stream=True
        )
        
        if bi_response.status_code == 200:
            print("✅ Downloaded report via BI Publisher")
            return bi_response
        
        print("❌ Could not download execution report via any method")
        print(f"   Standard output: {standard_response.status_code}")
        print(f"   Execution report: {exec_response.status_code}")
        print(f"   BI Publisher: {bi_response.status_code}")
        
        return None
        
    except Exception as e:
        print(f"❌ Error downloading execution report: {e}")
        return None

def get_oracle_config():
    """Get Oracle Cloud configuration"""
    return ORACLE_CLOUD_CONFIG

# EXISTING ROUTES - Keep all your existing functionality

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

# ENHANCED ENDPOINTS WITH BETTER ERROR HANDLING

@fbdi_bp.route('/get-child-job-soap', methods=['POST', 'OPTIONS'])
@cross_origin()
def get_child_job_soap():
    """Get child job ID using multiple approaches including SOAP API"""
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        return response
    
    try:
        data = request.get_json()
        parent_request_id = data.get('parent_request_id')
        report_path = data.get('report_path', '/Custom/MITER Reports/Receivables/Reports/AUTOINVOICE_CHILD_ESS_JOB_REPORT.xdo')
        
        if not parent_request_id:
            return jsonify({"error": "Missing parent_request_id parameter"}), 400
        
        print(f"🔍 Fetching child job for Parent ID: {parent_request_id}")
        print(f"📄 Report Path: {report_path}")
        
        # Call comprehensive method with enhanced error handling
        child_job_result = fetch_child_job_comprehensive(parent_request_id, report_path)
        
        if child_job_result:
            return jsonify({
                "status": "success",
                "parent_request_id": parent_request_id,
                "child_job_id": child_job_result.get('child_job_id'),
                "report_path": report_path,
                "job_details": child_job_result
            })
        else:
            return jsonify({
                "status": "not_found",
                "message": f"No child job found for parent ID {parent_request_id} with report path {report_path}",
                "parent_request_id": parent_request_id,
                "report_path": report_path,
                "suggestion": "Child job may not have been created yet, or the job name pattern may be different"
            }), 404
            
    except Exception as e:
        print(f"❌ Error in get_child_job_soap: {e}")
        return jsonify({"error": str(e)}), 500

@fbdi_bp.route('/autoinvoice-import-and-get-report', methods=['POST', 'OPTIONS'])
@cross_origin()
def autoinvoice_import_and_get_report():
    """Submit AutoInvoice Import job and download execution report XML using enhanced child job detection"""
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        return response
    
    try:
        data = request.get_json()
        ess_parameters = data.get('ess_parameters', '300000003170678,MILGARD EBS SPREADSHEET,2025-07-18,,,,,,,,,,,,,,,,,,,,Y,N')
        report_path = data.get('report_path', '/Custom/MITER Reports/Receivables/Reports/AUTOINVOICE_CHILD_ESS_JOB_REPORT.xdo')
        
        base_url = ORACLE_CLOUD_CONFIG['base_url']
        headers = get_oracle_headers()

        print(f"🚀 Starting AutoInvoice workflow with ENHANCED execution report download")

        # Step 1: Submit AutoInvoice Import
        print("📋 Step 1: Submitting AutoInvoice Import job...")
        
        auto_invoice_payload = {
            "OperationName": "submitESSJobRequest",
            "JobPackageName": "/oracle/apps/ess/financials/receivables/transactions/autoInvoices/",
            "JobDefName": "AutoInvoiceImportEss",
            "ESSParameters": ess_parameters
        }
        
        response = requests.post(
            f"{base_url}/fscmRestApi/resources/11.13.18.05/erpintegrations",
            headers=headers,
            json=auto_invoice_payload,
            timeout=60
        )
        
        if response.status_code not in [200, 201]:
            return jsonify({"error": f"Failed to submit AutoInvoice job: {response.status_code}"}), 500
        
        result = response.json()
        parent_request_id = result.get("ReqstId")
        
        print(f"✅ Step 1 Complete: AutoInvoice job submitted with ID: {parent_request_id}")

        # Step 2: Wait for AutoInvoice job completion
        print("⏳ Step 2: Waiting for AutoInvoice job to complete...")
        
        auto_job_status = poll_job_status(parent_request_id)
        if not auto_job_status or auto_job_status['RequestStatus'] not in ['SUCCEEDED', 'WARNING']:
            return jsonify({
                "error": "AutoInvoice job did not complete successfully",
                "status": auto_job_status.get('RequestStatus') if auto_job_status else 'TIMEOUT'
            }), 500
        
        print(f"✅ Step 2 Complete: AutoInvoice job completed with status: {auto_job_status['RequestStatus']}")

        # Step 3: Enhanced child job search with multiple wait attempts
        print("🔍 Step 3: Enhanced child job search...")
        
        child_job_result = None
        max_attempts = 3
        wait_times = [30, 60, 90]  # Progressive wait times
        
        for attempt in range(max_attempts):
            print(f"🔄 Attempt {attempt + 1}/{max_attempts}: Waiting {wait_times[attempt]} seconds for child job creation...")
            time.sleep(wait_times[attempt])
            
            child_job_result = fetch_child_job_comprehensive(parent_request_id, report_path)
            
            if child_job_result:
                break
            else:
                print(f"❌ Attempt {attempt + 1} failed, trying again...")
        
        if not child_job_result:
            # Return parent job output as fallback
            print("⚠️ Child job not found, downloading parent job output as fallback...")
            
            parent_output_url = f"{base_url}/fscmRestApi/resources/11.13.18.05/erpintegrations/{parent_request_id}/output"
            parent_output_resp = requests.get(parent_output_url, headers=headers, timeout=60, stream=True)
            
            if parent_output_resp.status_code == 200:
                tmpf = tempfile.NamedTemporaryFile(delete=False, suffix=".xml")
                for chunk in parent_output_resp.iter_content(1024*1024):
                    tmpf.write(chunk)
                tmpf.close()

                print("✅ Downloaded parent job output as fallback")

                response = send_file(
                    tmpf.name,
                    mimetype="application/xml",
                    as_attachment=True,
                    download_name=f"AutoInvoice_Parent_Output_{parent_request_id}.xml"
                )
                
                @response.call_on_close
                def cleanup():
                    if os.path.exists(tmpf.name):
                        os.remove(tmpf.name)
                
                return response
            else:
                return jsonify({
                    "error": "Child job not found and parent output not available",
                    "parent_request_id": parent_request_id,
                    "report_path": report_path,
                    "suggestion": "Check Oracle Cloud console for job execution details"
                }), 404
        
        child_job_id = child_job_result.get('child_job_id')
        
        print(f"✅ Step 3 Complete: Found child job with ID: {child_job_id}")

        # Step 4: Wait for child job completion
        print("⏳ Step 4: Waiting for child job to complete...")
        
        child_job_status = poll_job_status(child_job_id)
        if not child_job_status or child_job_status['RequestStatus'] not in ['SUCCEEDED', 'WARNING']:
            print(f"⚠️ Child job status: {child_job_status.get('RequestStatus') if child_job_status else 'TIMEOUT'}")
            
            # If child job fails, still try to download available output
            print("⚠️ Child job did not complete successfully, attempting to download available output...")
        else:
            print(f"✅ Step 4 Complete: Child job completed with status: {child_job_status['RequestStatus']}")

        # Step 5: Download execution report with enhanced error handling
        print("📊 Step 5: Downloading execution report...")
        
        execution_report_response = download_execution_report_from_child(child_job_id, parent_request_id)
        
        if not execution_report_response:
            return jsonify({
                "error": "Could not download execution report from child job",
                "child_job_id": child_job_id,
                "parent_request_id": parent_request_id,
                "suggestion": "Check Oracle Cloud console for job output availability"
            }), 500

        # Save execution report to temp file and return
        tmpf = tempfile.NamedTemporaryFile(delete=False, suffix=".xml")
        for chunk in execution_report_response.iter_content(1024*1024):
            tmpf.write(chunk)
        tmpf.close()

        print("✅ Step 5 Complete: EXECUTION REPORT downloaded successfully!")

        response = send_file(
            tmpf.name,
            mimetype="application/xml",
            as_attachment=True,
            download_name=f"AutoInvoice_EXECUTION_REPORT_{parent_request_id}_{child_job_id}.xml"
        )
        
        @response.call_on_close
        def cleanup():
            if os.path.exists(tmpf.name):
                os.remove(tmpf.name)
        
        return response

    except Exception as e:
        print(f"❌ Error in autoinvoice_import_and_get_report: {e}")
        return jsonify({"error": str(e)}), 500

@fbdi_bp.route('/complete-fbdi-workflow', methods=['POST', 'OPTIONS'])
@cross_origin()
def complete_fbdi_workflow():
    """Complete FBDI workflow: Generate -> Upload -> Load Interface -> Auto Invoice -> Get Child Job -> Download Execution Report"""
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
        report_path = request.form.get('report_path', '/Custom/MITER Reports/Receivables/Reports/AUTOINVOICE_CHILD_ESS_JOB_REPORT.xdo')
        
        if not raw_file or not fbdi_type or not project_name or not env_type:
            return jsonify({"error": "Missing required fields"}), 400

        print(f"🚀 Starting Enhanced Complete FBDI Workflow for {project_name}")
        
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
        
        # Step 4-8: Auto Invoice Import with Enhanced Child Job and Execution Report retrieval
        print("📋 Step 4-8: Running Auto Invoice Import and getting execution report...")
        ess_parameters = f"{business_unit},{batch_source},{gl_date},,,,,,,,,,,,,,,,,,,,Y,N"
        
        # Use the enhanced AutoInvoice with execution report endpoint
        execution_report_response = requests.post(
            f"http://localhost:5000/fbdi/autoinvoice-import-and-get-report",
            json={
                'ess_parameters': ess_parameters,
                'report_path': report_path
            }
        )
        
        if execution_report_response.status_code == 200:
            # Return the execution report file
            tmpf = tempfile.NamedTemporaryFile(delete=False, suffix=".xml")
            tmpf.write(execution_report_response.content)
            tmpf.close()
            
            print("✅ Enhanced Complete FBDI Workflow finished successfully!")
            
            response = send_file(
                tmpf.name,
                mimetype="application/xml",
                as_attachment=True,
                download_name=f"{project_name}_Complete_Workflow_ExecutionReport.xml"
            )
            
            @response.call_on_close
            def cleanup():
                if os.path.exists(tmpf.name):
                    os.remove(tmpf.name)
            
            return response
        else:
            error_data = execution_report_response.json() if execution_report_response.headers.get('content-type') == 'application/json' else {"error": "Unknown error"}
            return jsonify({"error": f"AutoInvoice and execution report workflow failed: {error_data.get('error')}"}), 500
        
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
        "message": "Enhanced FBDI Operations API with robust child job detection and execution report download",
        "oracle_base_url": ORACLE_CLOUD_CONFIG['base_url'],
        "features": [
            "Multiple child job detection methods",
            "Enhanced error handling",
            "Fallback to parent job output",
            "Progressive wait times",
            "Comprehensive logging"
        ],
        "endpoints": [
            "/fbdi/upload-to-ucm",
            "/fbdi/load-interface", 
            "/fbdi/auto-invoice-import",
            "/fbdi/get-child-job-soap",
            "/fbdi/autoinvoice-import-and-get-report",
            "/fbdi/complete-fbdi-workflow",
            "/fbdi/check-job-status/<job_id>",
            "/fbdi/list-all-jobs",
            "/fbdi/latest-ess-jobs"
        ]
    })
