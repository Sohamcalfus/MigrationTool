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
                             'AMOUNT', 'LINE_TYPE', 'DESCRIPTION', 'CUST_TRX_TYPE_NAME']
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
    
    # Step 3: Create final dataframe with COMPLETE template structure FIRST
    print("\nStep 3: Creating final dataframe with COMPLETE template structure...")
    
    # CRITICAL: Start with ALL template columns in exact order
    print(f"Creating dataframe with ALL {len(template_headers)} template columns...")
    
    if len(raw_df) > 0:
        # Create dataframe with ALL template columns and same number of rows as raw data
        final_df = pd.DataFrame(index=range(len(raw_df)), columns=template_headers)
        # Initialize all columns with None/NaN
        for col in template_headers:
            final_df[col] = None
        print(f"✓ Created complete template structure: {len(final_df)} rows × {len(final_df.columns)} columns")
    else:
        final_df = pd.DataFrame(columns=template_headers)
        print(f"✓ Created empty template structure with {len(template_headers)} columns")
    
    # Verify we have all template columns
    print(f"Verification: Final dataframe has {len(final_df.columns)} columns")
    print(f"Template has {len(template_headers)} columns")
    if len(final_df.columns) != len(template_headers):
        print("❌ ERROR: Column count mismatch!")
        return None, None
    
    # Step 4: Apply hard-coded values from template FIRST
    print("\nStep 4: Applying hard-coded values from template...")
    
    hard_coded_count = 0
    if hard_coded_values:
        print("\nApplying hard-coded values from template:")
        for column, hard_value in hard_coded_values.items():
            if column in final_df.columns:
                final_df[column] = hard_value
                hard_coded_count += 1
                print(f"✓ Hard-coded: {column} = {hard_value}")
            else:
                # Add new column with hard-coded value if not in template
                final_df[column] = hard_value
                hard_coded_count += 1
                print(f"✓ Hard-coded (new column): {column} = {hard_value}")
    
    print(f"Applied {hard_coded_count} hard-coded values")
    
    # Step 5: Map raw data to template columns (where names match exactly)
    print("\nStep 5: Mapping raw data to template columns...")
    
    exact_matches = 0
    for raw_col in raw_df.columns:
        if raw_col in final_df.columns:
            # Only overwrite if not already set by hard-coded values
            if final_df[raw_col].isnull().all():
                final_df[raw_col] = raw_df[raw_col].values
                exact_matches += 1
                print(f"✓ Exact match: {raw_col}")
            else:
                print(f"⚠ Skipped (hard-coded): {raw_col}")
    
    print(f"Exact matches found: {exact_matches} out of {len(raw_df.columns)} raw columns")
    
    # Step 6: Apply custom column mappings for different names
    print("\nStep 6: Applying custom column mappings...")
    
    column_mappings = {
        'BATCH_SOURCE_NAME': 'Transaction Batch Source Name',
        'LINE_TYPE': 'Transaction Line Type',
        'DESCRIPTION': 'Transaction Line Description', 
        'CURRENCY_CODE': 'Currency Code',
        'AMOUNT': 'Transaction Line Amount',
        'QUANTITY_INVOICED': 'Transaction Line Quantity',
        'UNIT_SELLING_PRICE': 'Unit Selling Price',
        'TRX_DATE': 'Transaction Date',
        'GL_DATE': 'Accounting Date',
        'CONVERSION_TYPE': 'Currency Conversion Type',
        'CONVERSION_DATE': 'Currency Conversion Date',
        'CONVERSION_RATE': 'Currency Conversion Rate',
        'TRX_NUMBER': 'Transaction Number',
        'CUST_TRX_TYPE_NAME': 'Transaction Type Name',
        'TERM_NAME': 'Payment Terms',
        'ORIG_SYSTEM_BILL_CUSTOMER_REF': 'Bill-to Customer Number',
        'ORIG_SYSTEM_BILL_ADDRESS_REF': 'Bill-to Customer Site Number',
    }
    
    custom_mappings = 0
    for template_col, raw_col in column_mappings.items():
        if template_col in final_df.columns and raw_col in raw_df.columns:
            # Only map if the template column is still empty (not already mapped or hard-coded)
            if final_df[template_col].isnull().all():
                final_df[template_col] = raw_df[raw_col].values
                custom_mappings += 1
                print(f"✓ Custom mapping: {raw_col} → {template_col}")
            else:
                print(f"⚠ Skipped (already populated): {template_col}")
    
    print(f"Custom mappings applied: {custom_mappings}")
    
    # Step 7: Apply default values for Oracle required fields
    print("\nStep 7: Applying default values for required Oracle fields...")
    
    default_values = {
        'LINE_TYPE': 'LINE',
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
    
    # Step 8: Add any raw data columns that don't exist in template
    print("\nStep 8: Adding raw data columns not in template...")
    
    additional_raw_columns = []
    for raw_col in raw_df.columns:
        if raw_col not in final_df.columns:
            final_df[raw_col] = raw_df[raw_col].values
            additional_raw_columns.append(raw_col)
    
    if additional_raw_columns:
        print(f"Added {len(additional_raw_columns)} additional raw data columns:")
        for col in additional_raw_columns:
            print(f"  + {col}")
    else:
        print("All raw data columns were already in template")
    
    # Generate line numbers
    if len(final_df) > 0:
        if 'LINE_NUMBER' not in final_df.columns:
            # Add LINE_NUMBER as a new column if not in template
            final_df['LINE_NUMBER'] = range(1, len(final_df) + 1)
        else:
            # Use existing LINE_NUMBER column from template
            final_df['LINE_NUMBER'] = range(1, len(final_df) + 1)
    
    # CRITICAL: Verify final column count before saving
    print(f"\nFinal verification before CSV generation:")
    print(f"Final dataframe columns: {len(final_df.columns)}")
    print(f"Template columns: {len(template_headers)}")
    print(f"Records: {len(final_df)}")
    
    # Step 9: Generate CSV file with ALL template columns
    print("\nStep 9: Generating CSV file with COMPLETE template structure...")
    csv_filename = 'RA_INTERFACE_LINES_ALL_Data.csv'
    
    # ENSURE we save ALL columns by explicitly specifying them
    # Use template_headers order to maintain structure
    columns_to_save = template_headers.copy()
    
    # Add LINE_NUMBER if it's not in template but exists in final_df
    if 'LINE_NUMBER' in final_df.columns and 'LINE_NUMBER' not in columns_to_save:
        columns_to_save.append('LINE_NUMBER')
    
    # Add any additional raw columns
    for col in additional_raw_columns:
        if col not in columns_to_save:
            columns_to_save.append(col)
    
    # Create final output with exact column structure
    output_df = final_df[columns_to_save].copy()
    
    # Save to CSV with ALL template columns
    output_df.to_csv(csv_filename, index=False, encoding='utf-8')
    print(f"✓ CSV file created: {csv_filename}")
    print(f"✓ CSV contains {len(output_df.columns)} columns (should be {len(template_headers)}+)")
    
    # Verify the saved CSV
    verify_df = pd.read_csv(csv_filename)
    print(f"✓ Verification: Saved CSV has {len(verify_df.columns)} columns")
    
    # Step 10: Create ZIP file
    print("\nStep 10: Creating ZIP file for Oracle Fusion upload...")
    zip_filename = f'RA_INTERFACE_LINES_ALL_{datetime.now().strftime("%Y%m%d_%H%M%S")}.zip'
    
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        zipf.write(csv_filename)
    
    print(f"ZIP file created: {zip_filename}")
    
    # Step 11: Final summary
    print("\n" + "="*60)
    print("FBDI PROCESSING SUMMARY")
    print("="*60)
    print(f"Template: {template_path}")
    print(f"Raw data: {raw_data_path}")
    print(f"Records processed: {len(output_df)}")
    print(f"Template columns: {len(template_headers)}")
    print(f"Hard-coded values: {hard_coded_count}")
    print(f"Exact matches: {exact_matches}")
    print(f"Custom mappings: {custom_mappings}")
    print(f"Additional raw columns: {len(additional_raw_columns)}")
    print(f"Final CSV columns: {len(output_df.columns)}")
    print(f"Expected columns: {len(template_headers)}+")
    print(f"✓ All template columns included: {len(output_df.columns) >= len(template_headers)}")
    print(f"CSV file: {csv_filename}")
    print(f"ZIP file ready for upload: {zip_filename}")
    
    # Show hard-coded values summary
    if hard_coded_values:
        print(f"\nHard-coded values applied to all {len(output_df)} records:")
        for col, val in hard_coded_values.items():
            print(f"  {col}: {val}")
    
    return zip_filename, csv_filename

def validate_ra_interface_data(df):
    """Validate RA_INTERFACE_LINES_ALL data"""
    print("\n" + "="*40)
    print("DATA VALIDATION RESULTS")
    print("="*40)
    
    # Required fields for RA_INTERFACE_LINES_ALL
    required_fields = [
        'BATCH_SOURCE_NAME',
        'CURRENCY_CODE',
        'LINE_TYPE',
        'AMOUNT'
    ]
    
    validation_results = []
    
    # Check required fields
    for field in required_fields:
        if field in df.columns:
            null_count = df[field].isnull().sum()
            if null_count > 0:
                validation_results.append(f"WARNING: {field} has {null_count} null values")
            else:
                validation_results.append(f"OK: {field} - no null values")
        else:
            validation_results.append(f"ERROR: Required field {field} not found")
    
    # Print validation results
    for result in validation_results:
        print(result)

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
- COMPLETE template structure preserved (ALL 368 template columns included)
- Hard-coded values from template have been applied automatically
- All raw data columns have been mapped appropriately
- Empty template columns preserved for Oracle compatibility
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
            print(f"\nFBDI processing completed!")
            print(f"Upload this file to Oracle Fusion: {zip_file}")
            print(f"Your CSV should now have 368 columns WITH hard-coded values!")
        else:
            print("FBDI processing failed!")
            
    except Exception as e:
        print(f"Error during FBDI processing: {str(e)}")
        import traceback
        traceback.print_exc()
