import requests
import time
import json
from requests.auth import HTTPBasicAuth

class OracleERPESSJobSubmitter:
    def __init__(self, base_url, username, password):
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password

    def submit_ess_job(self, job_package_name, job_def_name, ess_parameters):
        """Submit Oracle ESS job and return the response."""
        url = f"{self.base_url}/fscmRestApi/resources/11.13.18.05/erpintegrations"
        payload = {
            "OperationName": "submitESSJobRequest",
            "JobPackageName": job_package_name,
            "JobDefName": job_def_name,
            "ESSParameters": ess_parameters
        }

        print("Submitting ESS Job...")
        resp = requests.post(
            url,
            auth=HTTPBasicAuth(self.username, self.password),
            headers={
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            data=json.dumps(payload)
        )
        try:
            resp.raise_for_status()
            data = resp.json()
            print(f"Initial ReqstId: {data.get('ReqstId')}")
        except Exception as e:
            print("ERROR submitting job:", e)
            print("Response:", resp.text)
            raise
        return data

    def get_real_request_id(self, resp_data):
        """
        Try to determine the usable Request ID from the initial response.
        Oracle may return "-1" initially, so find the correct ReqstId from the response or poll for it.
        """
        req_id = resp_data.get('ReqstId')
        if req_id and req_id != "-1":
            return req_id

        # Sometimes, Oracle schedules the job asynchronously and returns "-1".
        # In some implementations, you may need to query for recent jobs, but for this
        # ESS API, the only way is to use the status API and possibly correlate on your parameters.

        print("The ESS RequestId is '-1'. It may take a few seconds to assign the real job ID.")
        return None

    def check_job_status(self, request_id):
        """Check ESS job status by Request ID using erpintegrations/getESSJobStatus."""
        url = f"{self.base_url}/fscmRestApi/resources/11.13.18.05/erpintegrations/getESSJobStatus?finder=ESSJobStatusRF;requestId={request_id}"
        resp = requests.get(
            url,
            auth=HTTPBasicAuth(self.username, self.password),
            headers={'Accept': 'application/json'}
        )
        try:
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print("ERROR querying job status:", e)
            print("Response:", resp.text)
            raise

    def monitor_job_until_complete(self, request_id, poll_interval=30, timeout_minutes=30):
        """Poll job status until complete or timeout."""
        print(f"Monitoring ESS job {request_id} status...")
        waited = 0
        timeout_seconds = timeout_minutes * 60

        while waited < timeout_seconds:
            status_info = self.check_job_status(request_id)
            status = status_info.get("RequestStatus", "")
            print(f"[{time.strftime('%H:%M:%S')}] Job Status: {status}")

            if status in ["SUCCEEDED", "SUCCESS", "COMPLETED"]:
                print("Job completed successfully.")
                return status_info
            elif status in ["ERROR", "FAILED", "WARNING"]:
                print("Job failed or completed with warning.")
                return status_info

            print(f"Waiting {poll_interval}s before next status check...")
            time.sleep(poll_interval)
            waited += poll_interval

        print("Timeout while waiting for job completion.")
        return {"Timeout": True}

# -------------------------------------
# USAGE EXAMPLE
# -------------------------------------

if __name__ == "__main__":
    # 1. UPDATE these with your actual Oracle Cloud values
    BASE_URL = 'https://miterbrands-ibayqy-test.fa.ocs.oraclecloud.com'
    USERNAME = 'FUSTST.CONVERSION'
    PASSWORD = 'M1terFu81tcO%n'

    # 2. Job details (use your real parameters)
    JOB_PACKAGE = "/oracle/apps/ess/financials/receivables/transactions/autoInvoice"
    JOB_DEF = "AutoInvoiceImportESS"
    ESS_PARAMS = "300000003170678,MILGARD EBS SPREADSHEET,2025-07-10,,,,,,,,,,,,,,,,,,,,Y,N"

    # 3. Initialize submitter
    submitter = OracleERPESSJobSubmitter(BASE_URL, USERNAME, PASSWORD)

    # 4. Submit job
    response = submitter.submit_ess_job(JOB_PACKAGE, JOB_DEF, ESS_PARAMS)

    # 5. Try to get request ID
    request_id = submitter.get_real_request_id(response)
    if not request_id:
        print("Check Oracle UI for recent jobs and get the real Request ID,")
        print("or add advanced status polling logic as needed for your environment.")
        exit(1)
    
    # 6. Monitor job (will poll until completion or error)
    job_result = submitter.monitor_job_until_complete(request_id)
    print("Final job status/results:", job_result)
