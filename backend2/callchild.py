from zeep import Client
from zeep.wsse.username import UsernameToken
 
# Replace these with your environment details
wsdl_url = 'https://miterbrands-ibayqy-test.fa.ocs.oraclecloud.com/xmlpserver/services/v2/ReportService?WSDL'
username = 'FUSTST.ITGUSR'
password = 'M1terFu81tgT%t'
 
# Initialize zeep client with WS-Security
client = Client(wsdl=wsdl_url, wsse=UsernameToken(username, password))
 
# Build reportRequest dictionary matching BI Publisher structure
report_request = {
    'reportAbsolutePath': '/Custom/MITER Reports/Receivables/Reports/AUTOINVOICE_CHILD_ESS_JOB_REPORT.xdo',
    'sizeOfDataChunkDownload': '-1',
    'byPassCache': True,
    'flattenXML': False,
    'parameterNameValues': {
        'listOfParamNameValues': {
            'item': [
                {
                    'name': 'REQUESTID',
                    'templateParam': False,
                    'multiValuesAllowed': False,
                    'refreshParamOnChange': False,
                    'selectAll': False,
                    'useNullForAll': False,   # 🔴 Add this line
                    'values': {
                        'item': ['452800']
                    }
                }
            ]
        }
    }
}
 
try:
    # Call the runReport operation with reportRequest, userID, password
    response = client.service.runReport(report_request, username, password)
   
    # The report is returned as base64 encoded data
    report_data = response.reportBytes
    output_file = "AutoInvoiceChildESSJobReport.xls"
 
    # Save report output to a PDF file
    with open(output_file, "wb") as f:
        f.write(report_data)
 
    print(f"✅ Report downloaded successfully as {output_file}")
 
except Exception as e:
    print(f"❌ Error while running BI Publisher report: {str(e)}")