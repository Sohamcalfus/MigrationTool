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
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Preformatted
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
import xml.etree.ElementTree as ET

 
# -------- STEP 0: INSTALL REQUIRED PACKAGES --------
# Run these before first time use:
# pip install zeep xlrd requests reportlab
 
# -------- CONFIGURATION --------
# WSDL and credentials
wsdl_url = 'https://miterbrands-ibayqy-test.fa.ocs.oraclecloud.com/xmlpserver/services/v2/ReportService?WSDL'
username = 'FUSTST.ITGUSR'
password = 'M1terFu81tgT%t'
 
# BI Publisher Report Input
report_request_id = '452800'  # <-- Parent request ID here
 
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
            'item': [
                {
                    'name': 'REQUESTID',
                    'values': {'item': [report_request_id]},
                    'templateParam': False,
                    'multiValuesAllowed': False,
                    'refreshParamOnChange': False,
                    'selectAll': False,
                    'useNullForAll': False
                }
            ]
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
    child_request_id = str(int(sheet.cell_value(0, 0)))  # Cell A1
    print(f"✅ Extracted Child Request ID: {child_request_id}")
except Exception as e:
    print(f"❌ Error reading XLS: {str(e)}")
    exit()

# -------- HELPER FUNCTION: FORMAT XML --------
def format_xml_content(xml_string):
    """Format XML string for better readability"""
    try:
        # Parse and prettify XML
        dom = minidom.parseString(xml_string)
        return dom.toprettyxml(indent="  ")
    except Exception:
        # If XML parsing fails, return as-is
        return xml_string

# -------- HELPER FUNCTION: CONVERT XML TO PDF --------
def create_pdf_from_xml_zip(zip_filename, pdf_filename, request_id):
    """Convert XML content from ZIP to a formatted PDF report"""
    try:
        print(f"📄 Creating PDF report from XML ZIP: {zip_filename}")
        
        # Create PDF document
        doc = SimpleDocTemplate(pdf_filename, pagesize=A4, 
                              rightMargin=72, leftMargin=72, 
                              topMargin=72, bottomMargin=18)
        
        # Get sample styles
        styles = getSampleStyleSheet()
        
        # Create custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=30,
            textColor=colors.darkblue,
            alignment=1  # Center alignment
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=12,
            textColor=colors.darkgreen
        )
        
        content_style = ParagraphStyle(
            'CustomContent',
            parent=styles['Normal'],
            fontSize=10,
            spaceAfter=6
        )
        
        xml_style = ParagraphStyle(
            'XMLStyle',
            parent=styles['Code'],
            fontSize=8,
            leftIndent=20,
            backgroundColor=colors.lightgrey,
            spaceAfter=12
        )
        
        # Build PDF content
        story = []
        
        # Title
        story.append(Paragraph(f"ESS Job Execution Report", title_style))
        story.append(Paragraph(f"Request ID: {request_id}", content_style))
        story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", content_style))
        story.append(Spacer(1, 20))
        
        # Process ZIP contents
        with zipfile.ZipFile(zip_filename, 'r') as zip_file:
            file_list = zip_file.namelist()
            
            # Summary section
            story.append(Paragraph("📋 Summary", heading_style))
            story.append(Paragraph(f"Total Files: {len(file_list)}", content_style))
            story.append(Paragraph(f"Files: {', '.join(file_list)}", content_style))
            story.append(Spacer(1, 20))
            
            # Process each XML file
            for file_name in file_list:
                try:
                    xml_content = zip_file.read(file_name).decode('utf-8')
                    
                    # Add file header
                    story.append(Paragraph(f"📄 File: {file_name}", heading_style))
                    
                    # Try to parse XML and extract meaningful content
                    try:
                        root = ET.fromstring(xml_content)
                        
                        # Extract key information based on XML structure
                        if root.tag == 'ESSJobMetadata':
                            story.append(Paragraph("📊 Metadata Information", content_style))
                            for child in root:
                                if child.text and child.text.strip():
                                    story.append(Paragraph(f"<b>{child.tag}:</b> {child.text}", content_style))
                        
                        elif root.tag == 'ESSJobFile':
                            story.append(Paragraph("📁 Job File Content", content_style))
                            for child in root:
                                if child.tag == 'Content':
                                    # Display content in a formatted way
                                    content_text = child.text[:2000] if child.text else "No content"
                                    if len(child.text or "") > 2000:
                                        content_text += "... (truncated)"
                                    story.append(Preformatted(content_text, xml_style))
                                else:
                                    if child.text and child.text.strip():
                                        story.append(Paragraph(f"<b>{child.tag}:</b> {child.text}", content_style))
                        
                        elif root.tag == 'ESSJobBinaryFile':
                            story.append(Paragraph("💾 Binary File Information", content_style))
                            for child in root:
                                if child.tag != 'Base64Content':  # Skip large base64 content
                                    if child.text and child.text.strip():
                                        story.append(Paragraph(f"<b>{child.tag}:</b> {child.text}", content_style))
                            story.append(Paragraph("<i>Binary content available in original file</i>", content_style))
                        
                        else:
                            # Generic XML display
                            story.append(Paragraph("🔧 XML Content", content_style))
                            # Show formatted XML (truncated for readability)
                            formatted_xml = format_xml_content(xml_content)
                            if len(formatted_xml) > 3000:
                                formatted_xml = formatted_xml[:3000] + "\n... (truncated for PDF display)"
                            story.append(Preformatted(formatted_xml, xml_style))
                    
                    except ET.ParseError:
                        # If XML parsing fails, show raw content
                        story.append(Paragraph("📝 Raw Content", content_style))
                        raw_content = xml_content[:2000]
                        if len(xml_content) > 2000:
                            raw_content += "... (truncated)"
                        story.append(Preformatted(raw_content, xml_style))
                    
                    story.append(Spacer(1, 20))
                
                except Exception as file_error:
                    story.append(Paragraph(f"❌ Error processing {file_name}: {str(file_error)}", content_style))
                    story.append(Spacer(1, 12))
        
        # Add footer information
        story.append(Spacer(1, 30))
        story.append(Paragraph("─" * 50, content_style))
        story.append(Paragraph(f"Report generated from ESS Job execution data", content_style))
        story.append(Paragraph(f"Source ZIP: {zip_filename}", content_style))
        
        # Build PDF
        doc.build(story)
        print(f"✅ PDF report created: {pdf_filename}")
        return True
        
    except Exception as e:
        print(f"❌ Error creating PDF: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

# -------- HELPER FUNCTION: CONVERT BASE64 TO XML AND CREATE ZIP --------
def create_xml_zip_from_base64(base64_content, zip_filename, request_id):
    """Convert base64 content to XML and package in ZIP"""
    try:
        print(f"📦 Processing base64 content (length: {len(base64_content)} characters)")
        
        # Decode base64 content
        clean_b64 = ''.join(base64_content.split())
        binary_data = base64.b64decode(clean_b64)
        
        print(f"✅ Base64 decoded successfully ({len(binary_data)} bytes)")
        
        # Check if the decoded content is already a ZIP file
        if binary_data.startswith(b'PK'):
            print("🗜️ Content detected as ZIP file - extracting and converting to XML ZIP")
            
            # Read the existing ZIP content
            with zipfile.ZipFile(io.BytesIO(binary_data), 'r') as existing_zip:
                zip_contents = existing_zip.namelist()
                print(f"📁 Original ZIP contains: {zip_contents}")
                
                # Create new ZIP with XML conversion
                with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as new_zip:
                    
                    for file_name in zip_contents:
                        file_content = existing_zip.read(file_name)
                        
                        # Try to convert each file to XML format
                        try:
                            # Decode file content
                            if file_name.lower().endswith(('.xml', '.log', '.txt')):
                                try:
                                    text_content = file_content.decode('utf-8')
                                except UnicodeDecodeError:
                                    text_content = file_content.decode('latin-1', errors='ignore')
                                
                                # Check if it's already XML
                                if text_content.strip().startswith('<?xml') or text_content.strip().startswith('<'):
                                    xml_content = format_xml_content(text_content)
                                    new_filename = file_name if file_name.endswith('.xml') else f"{os.path.splitext(file_name)[0]}.xml"
                                else:
                                    # Wrap non-XML content in XML structure
                                    xml_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<ESSJobFile>
    <OriginalFileName>{file_name}</OriginalFileName>
    <RequestId>{request_id}</RequestId>
    <ProcessedDate>{datetime.now().isoformat()}</ProcessedDate>
    <Content><![CDATA[{text_content}]]></Content>
</ESSJobFile>'''
                                    new_filename = f"{os.path.splitext(file_name)[0]}.xml"
                                
                                # Add XML file to new ZIP
                                new_zip.writestr(new_filename, xml_content.encode('utf-8'))
                                print(f"  ✅ Converted {file_name} → {new_filename}")
                                
                            else:
                                # For binary files, create XML wrapper with base64 content
                                b64_file_content = base64.b64encode(file_content).decode('utf-8')
                                xml_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<ESSJobBinaryFile>
    <OriginalFileName>{file_name}</OriginalFileName>
    <RequestId>{request_id}</RequestId>
    <ProcessedDate>{datetime.now().isoformat()}</ProcessedDate>
    <ContentType>binary</ContentType>
    <Base64Content>{b64_file_content}</Base64Content>
</ESSJobBinaryFile>'''
                                new_filename = f"{os.path.splitext(file_name)[0]}_binary.xml"
                                new_zip.writestr(new_filename, xml_content.encode('utf-8'))
                                print(f"  ✅ Wrapped binary {file_name} → {new_filename}")
                        
                        except Exception as file_error:
                            print(f"  ⚠️ Error processing {file_name}: {file_error}")
                            # Add problematic file as-is with XML wrapper
                            xml_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<ESSJobErrorFile>
    <OriginalFileName>{file_name}</OriginalFileName>
    <RequestId>{request_id}</RequestId>
    <ProcessedDate>{datetime.now().isoformat()}</ProcessedDate>
    <Error>{str(file_error)}</Error>
    <RawContentBase64>{base64.b64encode(file_content).decode('utf-8')}</RawContentBase64>
</ESSJobErrorFile>'''
                            new_zip.writestr(f"{file_name}_error.xml", xml_content.encode('utf-8'))
                    
                    # Add metadata file
                    metadata_xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<ESSJobMetadata>
    <RequestId>{request_id}</RequestId>
    <ProcessedDate>{datetime.now().isoformat()}</ProcessedDate>
    <OriginalFilesCount>{len(zip_contents)}</OriginalFilesCount>
    <OriginalFiles>
        {"".join([f"<File>{fname}</File>" for fname in zip_contents])}
    </OriginalFiles>
    <ConversionNote>All files converted to XML format for processing</ConversionNote>
</ESSJobMetadata>'''
                    new_zip.writestr("metadata.xml", metadata_xml.encode('utf-8'))
        
        else:
            print("📄 Content is not a ZIP file - treating as text and converting to XML")
            
            # Convert binary data to string
            try:
                content_str = binary_data.decode('utf-8')
            except UnicodeDecodeError:
                try:
                    content_str = binary_data.decode('latin-1')
                except UnicodeDecodeError:
                    content_str = binary_data.decode('utf-8', errors='ignore')
            
            # Create XML content
            if content_str.strip().startswith('<?xml') or content_str.strip().startswith('<'):
                xml_content = format_xml_content(content_str)
            else:
                xml_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<ESSJobOutput>
    <RequestId>{request_id}</RequestId>
    <ProcessedDate>{datetime.now().isoformat()}</ProcessedDate>
    <Content><![CDATA[{content_str}]]></Content>
</ESSJobOutput>'''
            
            # Create ZIP with XML content
            with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
                zipf.writestr(f"ESS_Job_Output_{request_id}.xml", xml_content.encode('utf-8'))
                
                # Add metadata
                metadata_xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<ESSJobMetadata>
    <RequestId>{request_id}</RequestId>
    <ProcessedDate>{datetime.now().isoformat()}</ProcessedDate>
    <ContentType>text</ContentType>
</ESSJobMetadata>'''
                zipf.writestr("metadata.xml", metadata_xml.encode('utf-8'))
        
        print(f"✅ XML ZIP package created: {zip_filename}")
        
        # Show final ZIP contents
        with zipfile.ZipFile(zip_filename, 'r') as final_zip:
            print("📁 Final ZIP Contents:")
            for filename in final_zip.namelist():
                file_info = final_zip.getinfo(filename)
                print(f"  📄 {filename} ({file_info.file_size} bytes)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating XML ZIP: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

# -------- STEP 3: FETCH BASE64 FROM JSON AND CONVERT TO XML ZIP --------
try:
    print("📥 Fetching ESS job execution data...")
 
    fusion_url = f"https://miterbrands-ibayqy-test.fa.ocs.oraclecloud.com/fscmRestApi/resources/11.13.18.05/erpintegrations?finder=ESSJobExecutionDetailsRF;requestId={child_request_id},fileType=ALL"
    
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }
    
    response = requests.get(fusion_url, auth=(username, password), headers=headers)
 
    if response.status_code == 200:
        print("✅ ESS job data retrieved successfully")
        
        try:
            json_data = response.json()
            print(f"📄 Response parsed as JSON with {len(json_data.get('items', []))} items")
            
            # Look specifically for DocumentContent field
            document_content = None
            
            if 'items' in json_data and json_data['items']:
                for idx, item in enumerate(json_data['items']):
                    if 'DocumentContent' in item and item['DocumentContent']:
                        document_content = item['DocumentContent']
                        print(f"✅ Found DocumentContent in item {idx + 1}")
                        print(f"📊 Request ID: {item.get('ReqstId', 'N/A')}")
                        print(f"📊 Operation: {item.get('OperationName', 'N/A')}")
                        break
            
            if document_content:
                print(f"📦 DocumentContent found (length: {len(document_content)} characters)")
                
                # Create XML ZIP from base64 content
                success = create_xml_zip_from_base64(document_content, xml_zip_output, child_request_id)
                
                if success:
                    print(f"🎉 Successfully created XML ZIP package: {xml_zip_output}")
                    
                    # -------- STEP 4: CONVERT XML ZIP TO PDF --------
                    print("📄 Converting XML content to PDF...")
                    pdf_success = create_pdf_from_xml_zip(xml_zip_output, pdf_output, child_request_id)
                    
                    if pdf_success:
                        print(f"🎉 Successfully created PDF report: {pdf_output}")
                        
                        # Show file sizes
                        xml_size = os.path.getsize(xml_zip_output)
                        pdf_size = os.path.getsize(pdf_output)
                        print(f"📊 XML ZIP size: {xml_size:,} bytes")
                        print(f"📊 PDF size: {pdf_size:,} bytes")
                    else:
                        print("❌ Failed to create PDF report")
                else:
                    print("❌ Failed to create XML ZIP package")
                
            else:
                print("⚠️ No DocumentContent found in response")
                print("Available fields in items:")
                if 'items' in json_data and json_data['items']:
                    for idx, item in enumerate(json_data['items']):
                        print(f"  Item {idx + 1}: {list(item.keys())}")
                
                # Save for debugging
                with open(f"ess_debug_{child_request_id}.json", "w") as f:
                    json.dump(json_data, f, indent=2)
                print(f"💾 Response saved for debugging")
                
        except json.JSONDecodeError:
            print("❌ Response is not valid JSON")
            print("Response content preview:", response.text[:500])
    
    else:
        print(f"❌ Failed to fetch ESS job data. Status: {response.status_code}")
        print("Response:", response.text[:500])
 
except Exception as e:
    print(f"❌ Error in ESS job data fetch: {str(e)}")
    import traceback
    traceback.print_exc()

print("\n🏁 Process completed!")
print(f"📁 Generated files:")
print(f"  📊 Excel Report: {xls_output_file}")
print(f"  🗜️ XML ZIP: {xml_zip_output}")
print(f"  📄 PDF Report: {pdf_output}")
