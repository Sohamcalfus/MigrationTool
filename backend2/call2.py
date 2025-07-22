from zeep import Client
from zeep.wsse.username import UsernameToken
import base64
import requests
import xlrd
import os
import json
import zipfile
import io
import xml.dom.minidom as minidom
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import inch
import xml.etree.ElementTree as ET

# -------- CONFIGURATION --------
wsdl_url = 'https://miterbrands-ibayqy-test.fa.ocs.oraclecloud.com/xmlpserver/services/v2/ReportService?WSDL'
username = 'FUSTST.ITGUSR'
password = 'M1terFu81tgT%t'
report_request_id = '452800'

# Output filenames
xls_output_file = "AutoInvoiceChildESSJobReport.xls"
xml_zip_output = "ESSJobExecutionOutput.zip"
pdf_output = "ESSJobExecutionReport.pdf"

# -------- STEP 1: CALL BI PUBLISHER REPORT --------
print("📡 Connecting to BI Publisher...")

client = Client(wsdl=wsdl_url, wsse=UsernameToken(username, password))

report_request = {
    'reportAbsolutePath': '/Custom/MITER Reports/Receivables/Reports/AUTOINVOICE_CHILD_ESS_JOB_REPORT.xdo',
    'sizeOfDataChunkDownload': '-1',
    'byPassCache': True,
    'flattenXML': False,
    'parameterNameValues': {
        'listOfParamNameValues': {
            'item': [{
                'name': 'REQUESTID',
                'values': {'item': [report_request_id]},
                'templateParam': False,
                'multiValuesAllowed': False,
                'refreshParamOnChange': False,
                'selectAll': False,
                'useNullForAll': False
            }]
        }
    }
}

try:
    response = client.service.runReport(report_request, username, password)
    with open(xls_output_file, "wb") as f:
        f.write(response.reportBytes)
    print(f"✅ Report downloaded: {xls_output_file}")
except Exception as e:
    print(f"❌ Error downloading BI report: {str(e)}")
    exit()

# -------- STEP 2: EXTRACT CHILD ID FROM XLS --------
try:
    wb = xlrd.open_workbook(xls_output_file)
    sheet = wb.sheet_by_index(0)
    child_request_id = str(int(sheet.cell_value(0, 0)))
    print(f"✅ Extracted Child Request ID: {child_request_id}")
except Exception as e:
    print(f"❌ Error reading XLS: {str(e)}")
    exit()

# -------- HELPER FUNCTIONS --------
def create_xml_zip_from_base64(base64_content, zip_filename, request_id):
    """Convert base64 content to XML and package in ZIP"""
    try:
        print(f"📦 Processing base64 content (length: {len(base64_content)} characters)")
        
        clean_b64 = ''.join(base64_content.split())
        binary_data = base64.b64decode(clean_b64)
        
        if binary_data.startswith(b'PK'):
            print("🗜️ Content detected as ZIP file - extracting and converting to XML ZIP")
            
            with zipfile.ZipFile(io.BytesIO(binary_data), 'r') as existing_zip:
                zip_contents = existing_zip.namelist()
                print(f"📁 Original ZIP contains: {zip_contents}")
                
                with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as new_zip:
                    for file_name in zip_contents:
                        file_content = existing_zip.read(file_name)
                        
                        if file_name.lower().endswith(('.xml', '.log', '.txt')):
                            try:
                                text_content = file_content.decode('utf-8')
                            except UnicodeDecodeError:
                                text_content = file_content.decode('latin-1', errors='ignore')
                            
                            if text_content.strip().startswith(('<?xml', '<')):
                                xml_content = minidom.parseString(text_content).toprettyxml(indent="  ")
                                new_filename = file_name if file_name.endswith('.xml') else f"{os.path.splitext(file_name)[0]}.xml"
                            else:
                                xml_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<ESSJobFile>
    <OriginalFileName>{file_name}</OriginalFileName>
    <RequestId>{request_id}</RequestId>
    <ProcessedDate>{datetime.now().isoformat()}</ProcessedDate>
    <Content><![CDATA[{text_content}]]></Content>
</ESSJobFile>'''
                                new_filename = f"{os.path.splitext(file_name)[0]}.xml"
                            
                            new_zip.writestr(new_filename, xml_content.encode('utf-8'))
                            print(f"  ✅ Converted {file_name} → {new_filename}")
        
        print(f"✅ XML ZIP package created: {zip_filename}")
        return True
        
    except Exception as e:
        print(f"❌ Error creating XML ZIP: {str(e)}")
        return False

def convert_xml_to_bip_pdf(xml_file, pdf_file):
    """Convert XML file to PDF in BIP format"""
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()

        doc = SimpleDocTemplate(pdf_file, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []

        # Title
        story.append(Paragraph("AutoInvoice Execution Report", styles['h1']))
        story.append(Spacer(1, 0.2*inch))

        # General Information
        story.append(Paragraph("General Information", styles['h2']))
        
        general_info_data = []
        for field, display_name in [
            ('P_AI_REQUEST_ID', 'Request ID:'),
            ('P_BATCH_SOURCE_NAME', 'Batch Source:'),
            ('P_DEFAULT_DATE', 'Default Date:'),
            ('P_RUNNING_MODE', 'Running Mode:'),
            ('P_ORG_ID', 'Organization ID:')
        ]:
            elem = root.find(field)
            value = elem.text if elem is not None else 'N/A'
            if field == 'P_DEFAULT_DATE' and 'T' in value:
                value = value.split('T')[0]
            general_info_data.append([display_name, value])

        general_table = Table(general_info_data, colWidths=[1.5*inch, 6*inch])
        general_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(general_table)
        story.append(Spacer(1, 0.2*inch))

        # Lines with Errors
        lines_with_errors = root.findall('.//G_LINES_WITH_ERRORS')
        if lines_with_errors:
            story.append(Paragraph("Lines with Errors", styles['h2']))

            for line in lines_with_errors:
                line_id = line.find('INTERFACE_LINE_ID')
                description = line.find('DESCRIPTION')
                amount = line.find('AMOUNT_DISP')
                currency = line.find('CURRENCY_CODE')

                line_text = f"<b>Interface Line ID:</b> {line_id.text if line_id is not None else 'N/A'} | "
                line_text += f"<b>Description:</b> {description.text if description is not None else 'N/A'} | "
                line_text += f"<b>Amount:</b> {amount.text if amount is not None else 'N/A'} {currency.text if currency is not None else ''}"
                
                story.append(Paragraph(line_text, styles['Normal']))
                story.append(Spacer(1, 0.1*inch))

                # Errors table
                errors_data = [['Error No.', 'Error Message']]
                line_errors = line.findall('.//G_LINE_ERRORS')
                for error in line_errors:
                    error_num = error.find('LINE_ERR_NUM')
                    error_text = error.find('ERROR_TEXT')
                    errors_data.append([
                        error_num.text if error_num is not None else 'N/A',
                        Paragraph(error_text.text if error_text is not None else 'N/A', styles['Normal'])
                    ])

                errors_table = Table(errors_data, colWidths=[0.8*inch, 6.2*inch], repeatRows=1)
                errors_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0,0), (-1,-1), 1, colors.black)
                ]))
                story.append(errors_table)
                story.append(Spacer(1, 0.2*inch))

        story.append(PageBreak())

        # Summary Section
        summary_info = root.find('.//G_SUMMARY_INFO')
        if summary_info is not None:
            story.append(Paragraph("Summary Information", styles['h2']))
            
            summary_fields = [
                ('NO_OF_LINES', 'Total Lines:'),
                ('INV_CURR_AMOUNT_DSP', 'Invoice Amount:'),
                ('.//SALES_COUNT', 'Sales Count:'),
                ('.//DIST_COUNT', 'Distribution Count:')
            ]
            
            summary_data = []
            for field, label in summary_fields:
                elem = summary_info.find(field)
                value = elem.text if elem is not None else 'N/A'
                
                if field == 'INV_CURR_AMOUNT_DSP':
                    curr_elem = summary_info.find('CURR_CODE')
                    curr_code = curr_elem.text if curr_elem is not None else ''
                    value = f"{value} {curr_code}"
                
                summary_data.append([label, value])

            summary_table = Table(summary_data, colWidths=[1.5*inch, 6*inch])
            summary_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            story.append(summary_table)

        doc.build(story)
        print(f"✅ BIP PDF report created: {pdf_file}")
        return True

    except Exception as e:
        print(f"❌ Error creating BIP PDF: {str(e)}")
        return False

# -------- STEP 3: FETCH BASE64 AND PROCESS --------
try:
    print("📥 Fetching ESS job execution data...")
    
    fusion_url = f"https://miterbrands-ibayqy-test.fa.ocs.oraclecloud.com/fscmRestApi/resources/11.13.18.05/erpintegrations?finder=ESSJobExecutionDetailsRF;requestId={child_request_id},fileType=ALL"
    
    response = requests.get(fusion_url, auth=(username, password), headers={'Accept': 'application/json'})
    
    if response.status_code == 200:
        print("✅ ESS job data retrieved successfully")
        json_data = response.json()
        
        document_content = None
        if 'items' in json_data and json_data['items']:
            for item in json_data['items']:
                if 'DocumentContent' in item and item['DocumentContent']:
                    document_content = item['DocumentContent']
                    print(f"✅ Found DocumentContent - Request ID: {item.get('ReqstId', 'N/A')}")
                    break
        
        if document_content:
            print(f"📦 DocumentContent found (length: {len(document_content)} characters)")
            
            # Create XML ZIP
            success = create_xml_zip_from_base64(document_content, xml_zip_output, child_request_id)
            
            if success:
                print(f"🎉 Successfully created XML ZIP package: {xml_zip_output}")
                
                # Convert each XML in ZIP to BIP format PDF
                print("📄 Converting XML content to BIP format PDF...")
                
                with zipfile.ZipFile(xml_zip_output, 'r') as zip_file:
                    xml_files = [f for f in zip_file.namelist() if f.endswith('.xml')]
                    
                    if xml_files:
                        # Use the first XML file for BIP conversion
                        first_xml = xml_files[0]
                        xml_content = zip_file.read(first_xml)
                        
                        # Save XML temporarily for processing
                        temp_xml = f"temp_{first_xml}"
                        with open(temp_xml, 'wb') as f:
                            f.write(xml_content)
                        
                        # Convert to BIP PDF
                        pdf_success = convert_xml_to_bip_pdf(temp_xml, pdf_output)
                        
                        # Clean up temp file
                        os.remove(temp_xml)
                        
                        if pdf_success:
                            print(f"🎉 Successfully created BIP format PDF: {pdf_output}")
                            print(f"📊 XML ZIP size: {os.path.getsize(xml_zip_output):,} bytes")
                            print(f"📊 PDF size: {os.path.getsize(pdf_output):,} bytes")
                        else:
                            print("❌ Failed to create BIP format PDF")
                    else:
                        print("⚠️ No XML files found in ZIP package")
            else:
                print("❌ Failed to create XML ZIP package")
        else:
            print("⚠️ No DocumentContent found in response")
    else:
        print(f"❌ Failed to fetch ESS job data. Status: {response.status_code}")

except Exception as e:
    print(f"❌ Error in process: {str(e)}")

print("\n🏁 Process completed!")
print(f"📁 Generated files:")
print(f"  📊 Excel Report: {xls_output_file}")
print(f"  🗜️ XML ZIP: {xml_zip_output}")
print(f"  📄 BIP Format PDF: {pdf_output}")
