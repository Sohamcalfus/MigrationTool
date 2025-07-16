import requests
import json
from requests.auth import HTTPBasicAuth

def submit_autoinvoice_ess_job():
    # Your configuration
    BASE_URL = "https://miterbrands-ibayqy-test.fa.ocs.oraclecloud.com"
    USERNAME = "FUSTST.CONVERSION"  # Replace with actual username
    PASSWORD = "M1terFu81tcO%n"  # Replace with actual password
    
    # Your exact payload from the conversation
    job_payload = {
        "OperationName": "submitESSJobRequest",
        "JobPackageName": "/oracle/apps/ess/financials/receivables/transactions/autoInvoice",
        "JobDefName": "AutoInvoiceImportESS",
        "ESSParameters": "300000003170678,MILGARD EBS SPREADSHEET,2025-07-10,,,,,,,,,,,,,,,,,,,,Y,N"
    }
    
    # Make the request
    response = requests.post(
        f"{BASE_URL}/fscmRestApi/resources/11.13.18.05/erpintegrations",
        auth=HTTPBasicAuth(USERNAME, PASSWORD),
        headers={'Content-Type': 'application/json'},
        data=json.dumps(job_payload)
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
