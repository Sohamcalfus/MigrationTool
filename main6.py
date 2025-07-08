import pandas as pd
import zipfile
import os
from datetime import datetime
import numpy as np

def process_fbdi_receivables():
    """Complete FBDI processing for Oracle Fusion Receivables"""
    
    print("="*60)
    print("ORACLE FUSION RECEIVABLES FBDI PROCESSOR")
    print("="*60)
    
    # Step 1: Load the RA_INTERFACE_LINES_ALL template
    print("\nStep 1: Loading RA_INTERFACE_LINES_ALL template...")
    template_path = 'C:/Users/SohamKasurde/Conversion/AR_Normal_POC.xlsm'
    
    try:
        # Read the template - try different header rows to find the actual column names
        template_df = pd.read_excel(template_path, header=None)
        
        # Look for the actual column headers in the first few rows
        actual_headers = None
        hard_coded_row = None
        for i in range(min(10, len(template_df))):
            row_values = template_df.iloc[i].astype(str).tolist()
            # Look for rows that contain actual column names (not "Unnamed" or empty)
            if any('BATCH_SOURCE' in str(val) or 'TRX_' in str(val) or 'AMOUNT' in str(val) for val in row_values):
                actual_headers = row_values
                header_row = i
                
                # Look for hard-coded values in the next row
                if i + 1 < len(template_df):
                    hard_coded_row = template_df.iloc[i + 1].tolist()
                break
        
        if actual_headers:
            template_df = pd.read_excel(template_path, header=header_row)
            template_headers = template_df.columns.tolist()
            print(f"Template loaded successfully with {len(template_headers)} columns")
            print("First 10 template columns:", template_headers[:10])
            print("Last 10 template columns:", template_headers[-10:])
            
            # Extract hard-coded values
            hard_coded_values = {}
            if hard_coded_row:
                for idx, header in enumerate(template_headers):
                    if idx < len(hard_coded_row):
                        value = hard_coded_row[idx]
                        # Check if it's a meaningful hard-coded value (not NaN, empty, or placeholder)
                        if pd.notna(value) and str(value).strip() != '' and str(value) != 'nan':
                            hard_coded_values[header] = str(value).strip()
                            print(f"Hard-coded value found: {header} = {value}")
                
                print(f"Found {len(hard_coded_values)} hard-coded values in template")
            else:
                hard_coded_values = {}
                print("No hard-coded values row found")
                
        else:
            # If we can't find proper headers, create a basic structure
            print("Could not find proper headers in template. Using basic structure.")
            template_headers = ['BATCH_SOURCE_NAME', 'TRX_NUMBER', 'TRX_DATE', 'CURRENCY_CODE', 
                             'AMOUNT', 'Transaction Line Type', 'DESCRIPTION', 'CUST_TRX_TYPE_NAME']
            hard_coded_values = {}
        
    except Exception as e:
        print(f"Error loading template: {e}")
        return None, None
    
    # Step 2: Load and process raw data
    print("\nStep 2: Loading raw customer invoice data...")
    raw_data_path = 'C:/Users/SohamKasurde/Conversion/Customer Invoice Conversion Data - RAW File.xlsx'
    
    try:
        # First, read without header to inspect the structure
        raw_df_inspect = pd.read_excel(raw_data_path, header=None)
        print("First few rows of raw data:")
        print(raw_df_inspect.head())
        
        # Look for the actual column headers
        actual_raw_headers = None
        for i in range(min(5, len(raw_df_inspect))):
            row_values = raw_df_inspect.iloc[i].astype(str).tolist()
            # Look for meaningful column names (not "Hard Code Value" or "Unnamed")
            if any(val not in ['Hard Code Value', 'nan', ''] and 'Unnamed' not in str(val) and len(str(val)) > 3 for val in row_values):
                actual_raw_headers = row_values
                header_row = i
                break
        
        if actual_raw_headers:
            raw_df = pd.read_excel(raw_data_path, header=header_row)
            # Clean column names
            raw_df.columns = [str(col).strip() for col in raw_df.columns]
        else:
            # If no proper headers found, use the first row as headers
            raw_df = pd.read_excel(raw_data_path, header=0)
        
        # Remove rows that are all NaN or contain only "Hard Code Value"
        raw_df = raw_df.dropna(how='all')
        raw_df = raw_df[~raw_df.astype(str).apply(lambda x: x.str.contains('Hard Code Value').all(), axis=1)]
        
        print(f"Raw data loaded: {len(raw_df)} records")
        print(f"Raw data columns: {len(raw_df.columns)} columns")
        print("Raw data columns:", list(raw_df.columns))
        
    except Exception as e:
        print(f"Error loading raw data: {e}")
        return None, None
    
    # Step 3: Create comprehensive column equivalence mapping to handle ALL duplicates
    print("\nStep 3: Creating comprehensive column equivalence mapping...")
    
    # UPDATED: Define comprehensive column equivalence - keep "Transaction Line Type" as the standard
    column_equivalence = {
        # Transaction Number variations
        'Transaction Number': 'TRX_NUMBER',
        'TRX_NUMBER': 'TRX_NUMBER',
        'Trx Number': 'TRX_NUMBER',
        
        # Transaction Date variations
        'Transaction Date': 'TRX_DATE',
        'TRX_DATE': 'TRX_DATE',
        'Trx Date': 'TRX_DATE',
        
        # Amount variations
        'Transaction Line Amount': 'AMOUNT',
        'AMOUNT': 'AMOUNT',
        'Amount': 'AMOUNT',
        'Line Amount': 'AMOUNT',
        
        # Currency Code variations
        'Currency Code': 'CURRENCY_CODE',
        'CURRENCY_CODE': 'CURRENCY_CODE',
        
        # Description variations
        'Transaction Line Description': 'DESCRIPTION',
        'DESCRIPTION': 'DESCRIPTION',
        'Description': 'DESCRIPTION',
        
        # LINE TYPE variations - FIXED: Keep "Transaction Line Type" as standard
        'LINE_TYPE': 'Transaction Line Type',
        'Line Type': 'Transaction Line Type',
        'LINETYPE': 'Transaction Line Type',
        'Transaction Line Type': 'Transaction Line Type',  # Keep as is
        
        # Transaction Type variations
        'Transaction Type Name': 'CUST_TRX_TYPE_NAME',
        'CUST_TRX_TYPE_NAME': 'CUST_TRX_TYPE_NAME',
        'Transaction Type': 'CUST_TRX_TYPE_NAME',
        
        # Batch Source variations
        'Transaction Batch Source Name': 'BATCH_SOURCE_NAME',
        'BATCH_SOURCE_NAME': 'BATCH_SOURCE_NAME',
        'Batch Source Name': 'BATCH_SOURCE_NAME',
        
        # GL Date variations
        'Accounting Date': 'GL_DATE',
        'GL_DATE': 'GL_DATE',
        'GL Date': 'GL_DATE',
        
        # Quantity variations
        'Transaction Line Quantity': 'QUANTITY_INVOICED',
        'QUANTITY_INVOICED': 'QUANTITY_INVOICED',
        'Quantity Invoiced': 'QUANTITY_INVOICED',
        'Quantity': 'QUANTITY_INVOICED',
        
        # Unit Selling Price variations
        'Unit Selling Price': 'UNIT_SELLING_PRICE',
        'UNIT_SELLING_PRICE': 'UNIT_SELLING_PRICE',
        'Unit Price': 'UNIT_SELLING_PRICE',
        
        # Conversion Type variations
        'Currency Conversion Type': 'CONVERSION_TYPE',
        'CONVERSION_TYPE': 'CONVERSION_TYPE',
        'Conversion Type': 'CONVERSION_TYPE',
        
        # Conversion Date variations
        'Currency Conversion Date': 'CONVERSION_DATE',
        'CONVERSION_DATE': 'CONVERSION_DATE',
        'Conversion Date': 'CONVERSION_DATE',
        
        # Conversion Rate variations
        'Currency Conversion Rate': 'CONVERSION_RATE',
        'CONVERSION_RATE': 'CONVERSION_RATE',
        'Conversion Rate': 'CONVERSION_RATE',
        
        # Payment Terms variations
        'Payment Terms': 'TERM_NAME',
        'TERM_NAME': 'TERM_NAME',
        'Terms': 'TERM_NAME',
        
        # Customer Number variations
        'Bill-to Customer Number': 'ORIG_SYSTEM_BILL_CUSTOMER_REF',
        'ORIG_SYSTEM_BILL_CUSTOMER_REF': 'ORIG_SYSTEM_BILL_CUSTOMER_REF',
        'Customer Number': 'ORIG_SYSTEM_BILL_CUSTOMER_REF',
        
        # Customer Site variations
        'Bill-to Customer Site Number': 'ORIG_SYSTEM_BILL_ADDRESS_REF',
        'ORIG_SYSTEM_BILL_ADDRESS_REF': 'ORIG_SYSTEM_BILL_ADDRESS_REF',
        'Customer Site Number': 'ORIG_SYSTEM_BILL_ADDRESS_REF',
    }
    
    def normalize_columns(columns, equivalence_map):
        """Normalize column names and remove duplicates"""
        normalized = []
        seen = set()
        duplicates_found = []
        
        for col in columns:
            # Get normalized column name
            norm_col = equivalence_map.get(col, col)
            
            if norm_col not in seen:
                normalized.append(norm_col)
                seen.add(norm_col)
                print(f"✓ Added: {col} → {norm_col}")
            else:
                duplicates_found.append((col, norm_col))
                print(f"⚠ DUPLICATE SKIPPED: {col} → {norm_col} (already exists)")
        
        if duplicates_found:
            print(f"\nDuplicates eliminated: {len(duplicates_found)}")
            for orig, norm in duplicates_found:
                print(f"  {orig} → {norm}")
        
        return normalized
    
    # Normalize template columns
    normalized_template_headers = normalize_columns(template_headers, column_equivalence)
    print(f"\nNormalized template columns: {len(normalized_template_headers)} (was {len(template_headers)})")
    
    # Step 4: Create final dataframe with normalized unique columns
    print("\nStep 4: Creating final dataframe with unique normalized columns...")
    
    if len(raw_df) > 0:
        # Create dataframe with normalized template columns
        final_df = pd.DataFrame(index=range(len(raw_df)), columns=normalized_template_headers)
        # Initialize all columns with None/NaN
        for col in normalized_template_headers:
            final_df[col] = None
        print(f"✓ Created dataframe: {len(final_df)} rows × {len(final_df.columns)} unique columns")
    else:
        final_df = pd.DataFrame(columns=normalized_template_headers)
        print(f"✓ Created empty dataframe with {len(normalized_template_headers)} unique columns")
    
    # Step 5: Apply hard-coded values from template (using normalized names)
    print("\nStep 5: Applying hard-coded values from template...")
    
    hard_coded_count = 0
    if hard_coded_values:
        print("Applying hard-coded values:")
        for original_col, hard_value in hard_coded_values.items():
            # Normalize the column name
            normalized_col = column_equivalence.get(original_col, original_col)
            if normalized_col in final_df.columns:
                final_df[normalized_col] = hard_value
                hard_coded_count += 1
                print(f"✓ Hard-coded: {original_col} → {normalized_col} = {hard_value}")
    
    print(f"Applied {hard_coded_count} hard-coded values")
    
    # Step 6: Map raw data to normalized template columns
    print("\nStep 6: Mapping raw data to normalized template columns...")
    
    mapped_count = 0
    for raw_col in raw_df.columns:
        # Normalize the raw column name
        normalized_col = column_equivalence.get(raw_col, raw_col)
        
        if normalized_col in final_df.columns:
            # Only map if not already set by hard-coded values
            if final_df[normalized_col].isnull().all():
                final_df[normalized_col] = raw_df[raw_col].values
                mapped_count += 1
                print(f"✓ Mapped: {raw_col} → {normalized_col}")
            else:
                print(f"⚠ Skipped (hard-coded): {raw_col} → {normalized_col}")
        else:
            print(f"ℹ No template mapping for: {raw_col}")
    
    print(f"Successfully mapped {mapped_count} raw data columns")
    
    # Step 7: Apply default values for Oracle required fields
    print("\nStep 7: Applying default values for required Oracle fields...")
    
    default_values = {
        'Transaction Line Type': 'LINE',  # Updated to use "Transaction Line Type"
        'CONVERSION_TYPE': 'Corporate',
        'QUANTITY_INVOICED': 1,
        'TAX_EXEMPT_FLAG': 'N',
    }
    
    defaults_applied = 0
    for col, default_val in default_values.items():
        if col in final_df.columns:
            null_count_before = final_df[col].isnull().sum()
            final_df[col] = final_df[col].fillna(default_val)
            null_count_after = final_df[col].isnull().sum()
            if null_count_before > null_count_after:
                defaults_applied += 1
                print(f"✓ Default applied: {col} = {default_val} ({null_count_before - null_count_after} rows)")
    
    # Step 8: Add any unmapped raw data columns (that don't have equivalents)
    print("\nStep 8: Adding unmapped raw data columns...")
    
    additional_columns = []
    for raw_col in raw_df.columns:
        normalized_col = column_equivalence.get(raw_col, raw_col)
        # Add if it's not already in our final dataframe
        if normalized_col not in final_df.columns:
            final_df[normalized_col] = raw_df[raw_col].values
            additional_columns.append(raw_col)
            print(f"✓ Added additional column: {raw_col}")
    
    if additional_columns:
        print(f"Added {len(additional_columns)} additional unique columns")
    else:
        print("No additional columns needed - all raw data was mapped")
    
    # REMOVED: Line number generation (as requested)
    print("\nSkipping line number generation as requested...")
    
    # Step 9: Final verification and CSV generation
    print(f"\nStep 9: Final verification...")
    print(f"Final dataframe columns: {len(final_df.columns)}")
    print(f"Original template columns: {len(template_headers)}")
    print(f"Normalized template columns: {len(normalized_template_headers)}")
    print(f"Raw data columns: {len(raw_df.columns)}")
    print(f"Records: {len(final_df)}")
    
    # Show columns with data
    columns_with_data = [col for col in final_df.columns if final_df[col].notna().any()]
    print(f"Columns with data: {len(columns_with_data)}")
    
    # Generate CSV file
    print("\nStep 10: Generating CSV file...")
    csv_filename = 'RA_INTERFACE_LINES_ALL_Data.csv'
    
    # Save with all unique columns
    final_df.to_csv(csv_filename, index=False, encoding='utf-8')
    print(f"✓ CSV file created: {csv_filename}")
    
    # Verify saved CSV
    verify_df = pd.read_csv(csv_filename)
    print(f"✓ Verification: CSV has {len(verify_df.columns)} unique columns")
    
    # Create ZIP file
    print("\nStep 11: Creating ZIP file...")
    zip_filename = f'RA_INTERFACE_LINES_ALL_{datetime.now().strftime("%Y%m%d_%H%M%S")}.zip'
    
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        zipf.write(csv_filename)
    
    print(f"ZIP file created: {zip_filename}")
    
    # Final summary
    print("\n" + "="*60)
    print("FBDI PROCESSING SUMMARY")
    print("="*60)
    print(f"Original template columns: {len(template_headers)}")
    print(f"Normalized unique columns: {len(normalized_template_headers)}")
    print(f"Raw data columns: {len(raw_df.columns)}")
    print(f"Final CSV columns: {len(verify_df.columns)}")
    print(f"Columns with data: {len(columns_with_data)}")
    print(f"Records: {len(final_df)}")
    print(f"Hard-coded values: {hard_coded_count}")
    print(f"Mapped columns: {mapped_count}")
    print(f"Additional columns: {len(additional_columns)}")
    print(f"CSV file: {csv_filename}")
    print(f"ZIP file: {zip_filename}")
    print(f"✅ Kept 'Transaction Line Type' (not LINE_TYPE)")
    print(f"✅ Removed auto-generated LINE_NUMBER")
    print(f"✅ ALL duplicate columns eliminated!")
    
    if hard_coded_values:
        print(f"\nHard-coded values applied:")
        for col, val in hard_coded_values.items():
            normalized_col = column_equivalence.get(col, col)
            print(f"  {col} → {normalized_col}: {val}")
    
    return zip_filename, csv_filename

def create_control_file():
    """Create a control file with processing instructions"""
    control_content = """
# Oracle Fusion Receivables FBDI Control File
# Generated: """ + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + """

UPLOAD INSTRUCTIONS:
1. Log into Oracle Fusion Cloud
2. Navigate to: Receivables > Billing > Import AutoInvoice
3. Click "Import Transactions"
4. Upload the ZIP file: RA_INTERFACE_LINES_ALL_*.zip
5. Select appropriate batch source and run the import
6. Monitor the import process in Scheduled Processes

IMPORTANT NOTES:
- Kept "Transaction Line Type" as standard (not LINE_TYPE)
- Removed auto-generated LINE_NUMBER column
- ALL duplicate columns eliminated
- Hard-coded values from template applied
- All unique raw data columns preserved
"""
    
    with open('FBDI_Control_Instructions.txt', 'w', encoding='utf-8') as f:
        f.write(control_content)
    
    print("Control file created: FBDI_Control_Instructions.txt")

# Main execution
if __name__ == "__main__":
    try:
        print("Starting Oracle Fusion Receivables FBDI Processing...")
        
        # Process the data
        zip_file, csv_file = process_fbdi_receivables()
        
        # Create control file
        create_control_file()
        
        if zip_file and csv_file:
            print(f"\n🎉 FBDI processing completed!")
            print(f"📁 Kept 'Transaction Line Type' and removed LINE_NUMBER!")
            print(f"📤 Upload this file to Oracle Fusion: {zip_file}")
        else:
            print("❌ FBDI processing failed!")
            
    except Exception as e:
        print(f"❌ Error during FBDI processing: {str(e)}")
        import traceback
        traceback.print_exc()
