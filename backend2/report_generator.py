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
username = 'FUSTST.CONVERSION'
password = 'M1terFu81tcO%n'


def get_execution_report_and_generate_pdf(autoinvoice_request_id, output_dir=None):
    """
    Main function to fetch execution report and generate PDF using AutoInvoice request ID
    
    Args:
        autoinvoice_request_id (str): The AutoInvoice import job request ID
        output_dir (str): Optional output directory for files
    
    Returns:
        dict: Status and file paths of generated files
    """
    
    if output_dir is None:
        output_dir = os.getcwd()
    
    # Output filenames
    xls_output_file = os.path.join(output_dir, f"AutoInvoiceChildESSJobReport_{autoinvoice_request_id}.xls")
    xml_zip_output = os.path.join(output_dir, f"ESSJobExecutionOutput_{autoinvoice_request_id}.zip")
    pdf_output = os.path.join(output_dir, f"ESSJobExecutionReport_{autoinvoice_request_id}.pdf")
    
    try:
        # -------- STEP 1: CALL BI PUBLISHER REPORT --------
        print(f"📡 Connecting to BI Publisher for AutoInvoice Request ID: {autoinvoice_request_id}")
        
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
                        'values': {'item': [autoinvoice_request_id]},
                        'templateParam': False,
                        'multiValuesAllowed': False,
                        'refreshParamOnChange': False,
                        'selectAll': False,
                        'useNullForAll': False
                    }]
                }
            }
        }
        
        response = client.service.runReport(report_request, username, password)
        with open(xls_output_file, "wb") as f:
            f.write(response.reportBytes)
        print(f"✅ Report downloaded: {xls_output_file}")
        
        # -------- STEP 2: EXTRACT CHILD ID FROM XLS --------
        wb = xlrd.open_workbook(xls_output_file)
        sheet = wb.sheet_by_index(0)
        child_request_id = str(int(sheet.cell_value(0, 0)))
        print(f"✅ Extracted Child Request ID: {child_request_id}")
        
        # -------- STEP 3: FETCH BASE64 AND PROCESS --------
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
                    
                    # Convert XML to BIP format PDF - UPDATED LOGIC
                    print("📄 Converting XML content to BIP format PDF...")
                    
                    with zipfile.ZipFile(xml_zip_output, 'r') as zip_file:
                        xml_files = [f for f in zip_file.namelist() if f.endswith('.xml')]
                        
                        if xml_files:
                            print(f"📋 Found {len(xml_files)} XML files: {xml_files}")
                            
                            # Find the BIP XML file specifically (format: ESS_O_<child_id>_BIP.xml)
                            bip_xml_file = None
                            for xml_file in xml_files:
                                if f"ESS_O_{child_request_id}_BIP.xml" == xml_file:
                                    bip_xml_file = xml_file
                                    break
                            
                            # Fallback: if exact match not found, look for any BIP file
                            if not bip_xml_file:
                                bip_candidates = [f for f in xml_files if 'BIP.xml' in f]
                                if bip_candidates:
                                    bip_xml_file = bip_candidates[0]
                                    print(f"⚠️ Exact BIP file not found, using: {bip_xml_file}")
                            
                            if bip_xml_file:
                                print(f"✅ Found BIP XML file: {bip_xml_file}")
                                xml_content = zip_file.read(bip_xml_file)
                                
                                # Show preview of the BIP XML content
                                try:
                                    preview_content = xml_content.decode('utf-8')
                                    print(f"\n📄 Preview of {bip_xml_file} (first 500 chars):")
                                    print(preview_content[:500])
                                    print("..." if len(preview_content) > 500 else "")
                                except UnicodeDecodeError:
                                    print("⚠️ Could not decode XML content for preview")
                                
                                # Save BIP XML temporarily for processing
                                temp_xml = os.path.join(output_dir, f"temp_{bip_xml_file}")
                                with open(temp_xml, 'wb') as f:
                                    f.write(xml_content)
                                
                                # Convert to BIP PDF
                                pdf_success = convert_xml_to_bip_pdf(temp_xml, pdf_output)
                                
                                # Clean up temp file
                                if os.path.exists(temp_xml):
                                    os.remove(temp_xml)
                                
                                if pdf_success:
                                    print(f"🎉 Successfully created BIP format PDF: {pdf_output}")
                                    
                                    return {
                                        "status": "success",
                                        "autoinvoice_request_id": autoinvoice_request_id,
                                        "child_request_id": child_request_id,
                                        "bip_xml_file": bip_xml_file,
                                        "files": {
                                            "xls_report": xls_output_file,
                                            "xml_zip": xml_zip_output,
                                            "pdf_report": pdf_output
                                        },
                                        "file_sizes": {
                                            "xls_size": os.path.getsize(xls_output_file),
                                            "xml_zip_size": os.path.getsize(xml_zip_output),
                                            "pdf_size": os.path.getsize(pdf_output)
                                        }
                                    }
                                else:
                                    raise Exception("Failed to create BIP format PDF")
                            else:
                                raise Exception(f"No BIP XML file found. Available files: {xml_files}")
                        else:
                            raise Exception("No XML files found in ZIP package")
                else:
                    raise Exception("Failed to create XML ZIP package")
            else:
                raise Exception("No DocumentContent found in response")
        else:
            raise Exception(f"Failed to fetch ESS job data. Status: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error in get_execution_report_and_generate_pdf: {str(e)}")
        return {
            "status": "error",
            "error": str(e),
            "autoinvoice_request_id": autoinvoice_request_id
        }


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
                                # Keep original XML content without pretty printing to preserve structure
                                xml_content = text_content
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
    """Convert XML file to PDF - handles both BIP format and generic ESS execution data"""
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()

        doc = SimpleDocTemplate(pdf_file, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []

        # Title
        story.append(Paragraph("AutoInvoice Execution Report", styles['h1']))
        story.append(Spacer(1, 0.2*inch))

        print(f"🔍 XML root tag: {root.tag}")
        print(f"🔍 XML structure preview: {[child.tag for child in root][:10]}")

        # Check if this is the expected BIP XML structure
        if root.find('P_AI_REQUEST_ID') is not None:
            print("✅ Detected BIP AutoInvoice XML structure")
            # Original BIP format parsing
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
                if field == 'P_DEFAULT_DATE' and value != 'N/A' and 'T' in value:
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
            else:
                story.append(Paragraph("✅ No errors found in the processing", styles['Normal']))
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
                    
                    if field == 'INV_CURR_AMOUNT_DSP' and value != 'N/A':
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
            else:
                story.append(Paragraph("Summary information not available", styles['Normal']))

        else:
            print("⚠️ Generic XML structure detected - creating generic report")
            # Handle generic XML structure
            story.append(Paragraph("Execution Information", styles['h2']))
            
            # Create a generic display of XML content
            info_data = []
            
            # Extract basic information from any XML structure
            if root.tag == 'ESSJobFile':
                # Handle wrapped ESS job file
                for child in root:
                    if child.tag != 'Content' and child.text and len(child.text.strip()) < 200:
                        info_data.append([f"{child.tag}:", child.text.strip()])
                
                # Extract content if it's CDATA
                content_elem = root.find('Content')
                if content_elem is not None and content_elem.text:
                    story.append(Paragraph("Job Output Content:", styles['h2']))
                    content_lines = content_elem.text.strip().split('\n')[:50]  # First 50 lines
                    for line in content_lines:
                        if line.strip():
                            story.append(Paragraph(line.strip(), styles['Normal']))
            else:
                # Handle any other XML structure
                def extract_xml_data(element, level=0, max_level=3):
                    if level > max_level:
                        return
                    
                    for child in element:
                        if child.text and child.text.strip() and len(child.text.strip()) < 500:
                            # Skip very long text content
                            indent = "  " * level
                            info_data.append([f"{indent}{child.tag}:", child.text.strip()[:200]])
                        
                        if len(child) > 0:
                            extract_xml_data(child, level + 1, max_level)
                
                extract_xml_data(root)
            
            if info_data:
                info_table = Table(info_data, colWidths=[2*inch, 5.5*inch])
                info_table.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ]))
                story.append(info_table)
            else:
                story.append(Paragraph("No structured data found in the execution report.", styles['Normal']))
                
                # Show raw XML structure as fallback
                story.append(Spacer(1, 0.2*inch))
                story.append(Paragraph("Raw XML Structure:", styles['h2']))
                
                xml_str = ET.tostring(root, encoding='unicode')[:2000]  # First 2000 chars
                formatted_xml = xml_str.replace('<', '&lt;').replace('>', '&gt;')
                
                story.append(Paragraph(f"<font face='Courier' size='8'>{formatted_xml}</font>", styles['Normal']))

        # Add footer
        story.append(Spacer(1, 0.5*inch))
        story.append(Paragraph("─" * 80, styles['Normal']))
        story.append(Paragraph(f"Report generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
        story.append(Paragraph(f"Source file: {os.path.basename(xml_file)}", styles['Normal']))

        doc.build(story)
        print(f"✅ BIP PDF report created: {pdf_file}")
        return True

    except Exception as e:
        print(f"❌ Error creating BIP PDF: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


# For testing purposes - can be removed in production
if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) > 1:
        test_request_id = sys.argv[1]
    else:
        test_request_id = "462331"  # Default test ID
        
    result = get_execution_report_and_generate_pdf(test_request_id)
    print(json.dumps(result, indent=2))
