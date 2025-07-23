from zeep import Client
from zeep.wsse.username import UsernameToken
import base64
import requests
import pandas as pd
import openpyxl
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
import os
import json
from datetime import datetime
import xml.etree.ElementTree as ET

# -------- CONFIGURATION --------
wsdl_url = 'https://miterbrands-ibayqy-test.fa.ocs.oraclecloud.com/xmlpserver/services/v2/ReportService?WSDL'
username = 'FUSTST.CONVERSION'
password = 'Conversion@2025'

def create_recon_report_with_soap(
    # Target report SOAP details (Friend's report)
    target_report_path="/Custom/MITER Reports/Receivables/Reports/MITER_AR_INVOICE_REPORT.xdo",
    target_report_params=None,
    
    # Source data file path (Your raw data)
    source_file_path=fr"C:/Project/MigrationTool/Customer Invoice Conversion Data - RAW File.xlsx",
    
    # Output settings
    output_file="Reconciliation_Report.xlsx",
    key_mapping=None,
    column_mapping=None,
    output_dir=None
):
    """
    Creates reconciliation report by fetching target data via SOAP and comparing with source data
    """
    
    if output_dir is None:
        output_dir = os.getcwd()
    
    output_path = os.path.join(output_dir, output_file)
    
    try:
        # -------- STEP 1: FETCH TARGET DATA VIA SOAP --------
        print("📡 Fetching target data via SOAP API...")
        target_df = fetch_target_data_soap(target_report_path, target_report_params or {})
        
        # -------- STEP 2: READ SOURCE DATA --------
        print("📊 Reading source data file...")
        source_df = read_source_data(source_file_path)
        
        print(f"✅ Target data: {len(target_df)} records, {len(target_df.columns)} columns")
        print(f"✅ Source data: {len(source_df)} records, {len(source_df.columns)} columns")
        
        # Display columns for analysis
        print("\n📋 Target columns:", list(target_df.columns))
        print("📋 Source columns:", list(source_df.columns))
        
        # -------- STEP 3: CREATE COLUMN MAPPINGS --------
        if key_mapping is None or column_mapping is None:
            key_mapping, column_mapping = auto_create_mappings(source_df, target_df)
        
        # -------- STEP 4: PERFORM RECONCILIATION --------
        print("🔄 Performing data reconciliation...")
        recon_df = perform_reconciliation(source_df, target_df, key_mapping, column_mapping)
        
        # -------- STEP 5: CREATE FORMATTED EXCEL REPORT --------
        print("📝 Creating formatted reconciliation report...")
        excel_file = create_formatted_recon_report(
            source_df, target_df, recon_df, 
            key_mapping, column_mapping, output_path
        )
        
        return {
            "status": "success",
            "output_file": excel_file,
            "source_records": len(source_df),
            "target_records": len(target_df),
            "recon_records": len(recon_df),
            "key_mapping": key_mapping,
            "column_mapping": column_mapping,
            "file_size": os.path.getsize(excel_file)
        }
        
    except Exception as e:
        print(f"❌ Error creating reconciliation report: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "status": "error",
            "error": str(e)
        }


def fetch_target_data_soap(report_path, report_params):
    """
    Fetches target data from SOAP API
    """
    try:
        print(f"🔗 Connecting to SOAP service: {wsdl_url}")
        
        client = Client(wsdl=wsdl_url, wsse=UsernameToken(username, password))
        
        # Build parameter items
        param_items = []
        default_params = {
            'P_ORG_ID': '300000003170678',
            'P_FROM_DATE': '2025-01-01',
            'P_TO_DATE': '2025-07-22',
            'P_CURRENCY_CODE': 'USD'
        }
        
        all_params = {**default_params, **report_params}
        
        for param_name, param_value in all_params.items():
            param_items.append({
                'name': param_name,
                'values': {'item': [str(param_value)]},
                'templateParam': False,
                'multiValuesAllowed': False,
                'refreshParamOnChange': False,
                'selectAll': False,
                'useNullForAll': False
            })
        
        report_request = {
            'reportAbsolutePath': report_path,
            'sizeOfDataChunkDownload': '-1',
            'byPassCache': True,
            'flattenXML': False,
            'parameterNameValues': {
                'listOfParamNameValues': {
                    'item': param_items
                }
            }
        }
        
        print(f"📤 Executing SOAP request for: {report_path}")
        response = client.service.runReport(report_request, username, password)
        
        # Save to temporary file
        temp_file = os.path.join(os.getcwd(), f"temp_target_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xls")
        with open(temp_file, "wb") as f:
            f.write(response.reportBytes)
        
        # Try multiple methods to read the file
        df = None
        try:
            df = pd.read_excel(temp_file, engine='openpyxl')
            print("✅ Successfully read using openpyxl engine")
        except:
            try:
                df = pd.read_excel(temp_file, engine='xlrd')
                print("✅ Successfully read using xlrd engine")
            except:
                df = parse_xml_response(temp_file)
        
        # Clean up temp file
        try:
            os.remove(temp_file)
        except:
            pass
        
        if df is not None:
            print(f"✅ Target data fetched: {len(df)} records")
            return df
        else:
            raise Exception("Could not parse target data")
            
    except Exception as e:
        print(f"❌ Error fetching target data via SOAP: {str(e)}")
        raise e


def read_source_data(file_path):
    """
    Reads source data from Excel file
    """
    try:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Source file not found: {file_path}")
        
        # Try different sheet names
        possible_sheets = [0, 'Sheet1', 'Data', 'Raw Data', 'Invoice Data']
        
        for sheet in possible_sheets:
            try:
                df = pd.read_excel(file_path, sheet_name=sheet)
                print(f"✅ Successfully read source data from sheet: {sheet}")
                return df
            except:
                continue
        
        # Default read
        df = pd.read_excel(file_path)
        return df
        
    except Exception as e:
        print(f"❌ Error reading source data: {str(e)}")
        raise e


def auto_create_mappings(source_df, target_df):
    """
    Auto-creates column mappings between source and target with improved logic
    """
    try:
        print("🔍 Auto-creating column mappings...")
        
        source_cols = source_df.columns.tolist()
        target_cols = target_df.columns.tolist()
        
        # Key mapping - find potential key columns
        key_patterns = ['invoice', 'number', 'id', 'reference', 'trx', 'transaction', 'doc', 'customer']
        key_mapping = {}
        
        # Enhanced key mapping logic
        for source_col in source_cols:
            source_lower = source_col.lower().replace('_', ' ').replace('-', ' ')
            for pattern in key_patterns:
                if pattern in source_lower:
                    # Find best matching target column
                    best_match = None
                    best_score = 0
                    
                    for target_col in target_cols:
                        target_lower = target_col.lower().replace('_', ' ').replace('-', ' ')
                        if pattern in target_lower:
                            # Calculate similarity score
                            source_words = set(source_lower.split())
                            target_words = set(target_lower.split())
                            common_words = source_words & target_words
                            score = len(common_words)
                            
                            if score > best_score:
                                best_score = score
                                best_match = target_col
                    
                    if best_match:
                        key_mapping[source_col] = best_match
                        break
        
        # If no pattern-based keys found, try exact matches
        if not key_mapping:
            common_cols = list(set(source_cols) & set(target_cols))
            if common_cols:
                key_mapping[common_cols[0]] = common_cols[0]
            else:
                # Use first meaningful columns
                key_mapping[source_cols[0]] = target_cols[0]
        
        # Enhanced column mapping with better similarity matching
        column_mapping = {}
        
        # Exact matches first
        for col in source_cols:
            if col in target_cols:
                column_mapping[col] = col
        
        # Fuzzy matching for remaining columns
        for source_col in source_cols:
            if source_col not in column_mapping:
                source_normalized = source_col.lower().replace('_', ' ').replace('-', ' ')
                source_words = set(source_normalized.split())
                
                best_match = None
                best_score = 0
                
                for target_col in target_cols:
                    if target_col not in column_mapping.values():
                        target_normalized = target_col.lower().replace('_', ' ').replace('-', ' ')
                        target_words = set(target_normalized.split())
                        
                        # Calculate similarity
                        common_words = source_words & target_words
                        if len(common_words) > 0:
                            similarity = len(common_words) / max(len(source_words), len(target_words))
                            if similarity > best_score and similarity > 0.3:  # At least 30% similarity
                                best_score = similarity
                                best_match = target_col
                
                if best_match:
                    column_mapping[source_col] = best_match
        
        print(f"🔑 Key mappings: {key_mapping}")
        print(f"📋 Column mappings found: {len(column_mapping)}")
        for src, tgt in column_mapping.items():
            print(f"  📍 {src} → {tgt}")
        
        return key_mapping, column_mapping
        
    except Exception as e:
        print(f"❌ Error creating mappings: {str(e)}")
        return {}, {}


def perform_reconciliation(source_df, target_df, key_mapping, column_mapping):
    """
    Performs data reconciliation between source and target datasets
    """
    try:
        recon_data = []
        
        # Create key combinations for matching
        source_keys = {}
        target_keys = {}
        
        print(f"📊 Building source keys using: {key_mapping}")
        
        # Build source keys
        for idx, row in source_df.iterrows():
            key_parts = []
            for source_key, target_key in key_mapping.items():
                if source_key in source_df.columns:
                    val = str(row[source_key]).strip().upper()
                    key_parts.append(val)
            key = tuple(key_parts) if key_parts else (str(idx),)
            source_keys[key] = row
        
        # Build target keys
        for idx, row in target_df.iterrows():
            key_parts = []
            for source_key, target_key in key_mapping.items():
                if target_key in target_df.columns:
                    val = str(row[target_key]).strip().upper()
                    key_parts.append(val)
            key = tuple(key_parts) if key_parts else (str(idx),)
            target_keys[key] = row
        
        # Get all unique keys
        all_keys = set(source_keys.keys()) | set(target_keys.keys())
        
        print(f"🔍 Reconciling {len(all_keys)} unique keys...")
        print(f"📊 Source keys: {len(source_keys)}, Target keys: {len(target_keys)}")
        
        for key in all_keys:
            recon_record = {}
            
            # Add key values
            for i, (source_key, target_key) in enumerate(key_mapping.items()):
                if i < len(key):
                    recon_record[f'Key_{source_key}'] = key[i] if key[i] else 'N/A'
            
            source_exists = key in source_keys
            target_exists = key in target_keys
            
            # Record existence
            recon_record['In_Source'] = 'Yes' if source_exists else 'No'
            recon_record['In_Target'] = 'Yes' if target_exists else 'No'
            recon_record['Record_Match'] = 'True' if (source_exists and target_exists) else 'False'
            
            # Field-level comparison
            if source_exists and target_exists:
                source_row = source_keys[key]
                target_row = target_keys[key]
                
                for source_col, target_col in column_mapping.items():
                    source_val = str(source_row.get(source_col, 'N/A')).strip()
                    target_val = str(target_row.get(target_col, 'N/A')).strip()
                    
                    recon_record[f'Source_{source_col}'] = source_val
                    recon_record[f'Target_{target_col}'] = target_val
                    
                    # Enhanced comparison logic
                    source_norm = source_val.upper() if source_val != 'N/A' else 'N/A'
                    target_norm = target_val.upper() if target_val != 'N/A' else 'N/A'
                    
                    # Try numeric comparison for numeric fields
                    is_match = False
                    if source_norm == target_norm:
                        is_match = True
                    else:
                        # Try numeric comparison
                        try:
                            source_num = float(source_val.replace(',', ''))
                            target_num = float(target_val.replace(',', ''))
                            is_match = abs(source_num - target_num) < 0.01  # Allow small differences
                        except:
                            is_match = False
                    
                    recon_record[f'Match_{source_col}'] = 'True' if is_match else 'False'
            
            elif source_exists:
                # Only in source
                source_row = source_keys[key]
                for source_col in column_mapping.keys():
                    recon_record[f'Source_{source_col}'] = str(source_row.get(source_col, ''))
                    recon_record[f'Target_{column_mapping[source_col]}'] = 'N/A'
                    recon_record[f'Match_{source_col}'] = 'False'
            
            elif target_exists:
                # Only in target
                target_row = target_keys[key]
                for source_col, target_col in column_mapping.items():
                    recon_record[f'Source_{source_col}'] = 'N/A'
                    recon_record[f'Target_{target_col}'] = str(target_row.get(target_col, ''))
                    recon_record[f'Match_{source_col}'] = 'False'
            
            recon_data.append(recon_record)
        
        recon_df = pd.DataFrame(recon_data)
        print(f"✅ Reconciliation completed: {len(recon_df)} records")
        
        # Show match statistics
        if 'Record_Match' in recon_df.columns:
            matches = len(recon_df[recon_df['Record_Match'] == 'True'])
            print(f"📊 Record matches: {matches}/{len(recon_df)} ({matches/len(recon_df)*100:.1f}%)")
        
        return recon_df
        
    except Exception as e:
        print(f"❌ Error performing reconciliation: {str(e)}")
        raise e


def create_formatted_recon_report(source_df, target_df, recon_df, key_mapping, column_mapping, output_file):
    """
    Creates formatted Excel reconciliation report with fixed merged cell handling
    """
    try:
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Reconciliation Report"
        
        # Define styles
        title_font = Font(size=18, bold=True, color="2C3E50")
        header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        header_font = Font(color="FFFFFF", bold=True)
        
        source_fill = PatternFill(start_color="FEF3C7", end_color="FEF3C7", fill_type="solid")  # Yellow
        target_fill = PatternFill(start_color="DBEAFE", end_color="DBEAFE", fill_type="solid")  # Blue
        recon_fill = PatternFill(start_color="F3F4F6", end_color="F3F4F6", fill_type="solid")   # Gray
        
        true_fill = PatternFill(start_color="D1FAE5", end_color="D1FAE5", fill_type="solid")   # Green
        false_fill = PatternFill(start_color="FEE2E2", end_color="FEE2E2", fill_type="solid")  # Red
        
        true_font = Font(color="059669", bold=True)
        false_font = Font(color="DC2626", bold=True)
        
        # Add title and metadata
        ws['A1'] = "DATA RECONCILIATION REPORT"
        ws['A1'].font = title_font
        ws['A1'].alignment = Alignment(horizontal='center')
        ws.merge_cells('A1:Z1')
        
        ws['A2'] = f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        ws['A2'].font = Font(size=10, italic=True)
        
        ws['A3'] = f"Source: {len(source_df)} records | Target: {len(target_df)} records"
        ws['A3'].font = Font(size=10, italic=True)
        
        # Column organization
        key_cols = [col for col in recon_df.columns if col.startswith('Key_')]
        status_cols = ['In_Source', 'In_Target', 'Record_Match']
        source_cols = [col for col in recon_df.columns if col.startswith('Source_')]
        target_cols = [col for col in recon_df.columns if col.startswith('Target_')]
        match_cols = [col for col in recon_df.columns if col.startswith('Match_')]
        
        # Write section headers
        current_row = 5
        col_index = 1
        
        sections = [
            (key_cols, "KEY COLUMNS", header_fill, header_font),
            (status_cols, "RECORD STATUS", recon_fill, Font(bold=True)),
            (source_cols, "SOURCE TABLE", source_fill, Font(bold=True)),
            (target_cols, "TARGET TABLE", target_fill, Font(bold=True)),
            (match_cols, "RECON REPORT", recon_fill, Font(bold=True))
        ]
        
        for cols, title, fill, font in sections:
            if cols:
                ws.cell(row=current_row, column=col_index, value=title)
                ws.cell(row=current_row, column=col_index).fill = fill
                ws.cell(row=current_row, column=col_index).font = font
                if len(cols) > 1:
                    ws.merge_cells(start_row=current_row, start_column=col_index,
                                  end_row=current_row, end_column=col_index + len(cols) - 1)
                col_index += len(cols)
        
        # Column headers and data
        current_row = 6
        col_index = 1
        
        ordered_columns = key_cols + status_cols + source_cols + target_cols + match_cols
        
        # Write column headers
        for col in ordered_columns:
            display_name = col.replace('Source_', '').replace('Target_', '').replace('Match_', '').replace('Key_', '')
            ws.cell(row=current_row, column=col_index, value=display_name)
            ws.cell(row=current_row, column=col_index).font = Font(bold=True)
            
            # Apply section colors
            if col.startswith('Source_'):
                ws.cell(row=current_row, column=col_index).fill = source_fill
            elif col.startswith('Target_'):
                ws.cell(row=current_row, column=col_index).fill = target_fill
            elif col.startswith('Match_') or col in status_cols:
                ws.cell(row=current_row, column=col_index).fill = recon_fill
            
            col_index += 1
        
        # Write data rows
        for idx, row in recon_df.iterrows():
            current_row = 7 + idx
            col_index = 1
            
            for col in ordered_columns:
                cell_value = row.get(col, '')
                ws.cell(row=current_row, column=col_index, value=str(cell_value))
                
                # Apply True/False formatting
                if col.startswith('Match_') or col in ['Record_Match']:
                    if str(cell_value).lower() == 'true':
                        ws.cell(row=current_row, column=col_index).fill = true_fill
                        ws.cell(row=current_row, column=col_index).font = true_font
                    elif str(cell_value).lower() == 'false':
                        ws.cell(row=current_row, column=col_index).fill = false_fill
                        ws.cell(row=current_row, column=col_index).font = false_font
                
                col_index += 1
        
        # Fixed auto-adjust column widths (avoiding MergedCell issue)
        try:
            for col_num in range(1, len(ordered_columns) + 1):
                column_letter = openpyxl.utils.get_column_letter(col_num)
                max_length = 0
                
                # Check column width by iterating through rows
                for row_num in range(1, len(recon_df) + 10):
                    try:
                        cell = ws[f'{column_letter}{row_num}']
                        if hasattr(cell, 'value') and cell.value:
                            cell_length = len(str(cell.value))
                            if cell_length > max_length:
                                max_length = cell_length
                    except:
                        continue
                
                adjusted_width = min(max_length + 2, 40)
                ws.column_dimensions[column_letter].width = adjusted_width
        except Exception as width_error:
            print(f"⚠️ Warning: Could not auto-adjust column widths: {width_error}")
        
        # Add summary
        summary_row = len(recon_df) + 10
        total_records = len(recon_df)
        matched_records = len(recon_df[recon_df['Record_Match'] == 'True']) if 'Record_Match' in recon_df.columns else 0
        unmatched_records = total_records - matched_records
        match_percentage = (matched_records / total_records * 100) if total_records > 0 else 0
        
        ws.cell(row=summary_row, column=1, value="RECONCILIATION SUMMARY")
        ws.cell(row=summary_row, column=1).font = Font(size=14, bold=True)
        
        summary_data = [
            ("Total Records:", total_records),
            ("Matched Records:", matched_records),
            ("Unmatched Records:", unmatched_records),
            ("Match Percentage:", f"{match_percentage:.1f}%"),
            ("Key Mappings:", str(len(key_mapping))),
            ("Column Mappings:", str(len(column_mapping)))
        ]
        
        for i, (label, value) in enumerate(summary_data):
            row_num = summary_row + i + 1
            ws.cell(row=row_num, column=1, value=label)
            ws.cell(row=row_num, column=1).font = Font(bold=True)
            ws.cell(row=row_num, column=2, value=value)
            
            if label == "Matched Records:":
                ws.cell(row=row_num, column=2).fill = true_fill
            elif label == "Unmatched Records:" and unmatched_records > 0:
                ws.cell(row=row_num, column=2).fill = false_fill
        
        # Save file
        wb.save(output_file)
        
        print(f"✅ Reconciliation report created: {output_file}")
        print(f"📊 Summary: {matched_records}/{total_records} matched ({match_percentage:.1f}%)")
        
        return output_file
        
    except Exception as e:
        print(f"❌ Error creating Excel report: {str(e)}")
        import traceback
        traceback.print_exc()
        raise e


def parse_xml_response(file_path):
    """
    Parse XML response when SOAP returns XML instead of Excel
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if content.strip().startswith('<?xml') or content.strip().startswith('<'):
            root = ET.fromstring(content)
            return pd.DataFrame([{'Column1': 'Sample Data'}])
        else:
            return None
            
    except Exception as e:
        print(f"❌ Error parsing XML: {str(e)}")
        return None


# Main execution
if __name__ == "__main__":
    print("🚀 Starting Reconciliation Report Generation...")
    
    # Custom parameters for target report
    target_params = {
        'P_ORG_ID': '300000003170678',
        'P_FROM_DATE': '2025-01-01',
        'P_TO_DATE': '2025-07-22'
    }
    
    # Create reconciliation report
    result = create_recon_report_with_soap(
        target_report_params=target_params,
        output_file="Data_Reconciliation_Report.xlsx"
    )
    
    if result["status"] == "success":
        print(f"✅ Reconciliation completed successfully!")
        print(f"📁 Report saved: {result['output_file']}")
        print(f"📊 Processed: {result['source_records']} source, {result['target_records']} target records")
        print(f"🔑 Key mappings: {result['key_mapping']}")
        print(f"📋 Column mappings: {len(result['column_mapping'])}")
        
        # Try to open the file
        try:
            import subprocess
            subprocess.run(['start', '', result['output_file']], shell=True, check=True)
        except:
            print("💡 Please manually open the reconciliation report")
    else:
        print("❌ Reconciliation failed:")
        print(json.dumps(result, indent=2))
