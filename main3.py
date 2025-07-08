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
        print("Raw data columns:", list(raw_df.columns))  # Show ALL columns
        
    except Exception as e:
        print(f"Error loading raw data: {e}")
        return None, None
    
    # Step 3: Create final dataframe with ALL data
    print("\nStep 3: Creating final dataframe with ALL raw data and template structure...")
    
    # Start with ALL raw data - this preserves everything from your raw file
    final_df = raw_df.copy()
    print(f"Starting with {len(final_df)} records and {len(final_df.columns)} columns from raw data")
    
    # Add any missing template columns that aren't in raw data
    template_columns_added = 0
    for col in template_headers:
        if col not in final_df.columns:
            final_df[col] = None
            template_columns_added += 1
    
    print(f"Added {template_columns_added} additional template columns")
    
    # Step 4: Apply hard-coded values from template
    print("\nStep 4: Applying hard-coded values from template...")
    
    hard_coded_count = 0
    if hard_coded_values:
        print("\nApplying hard-coded values from template:")
        for column, hard_value in hard_coded_values.items():
            if column in final_df.columns:
                # Apply hard-coded value to all rows (this may overwrite raw data where applicable)
                final_df[column] = hard_value
                hard_coded_count += 1
                print(f"✓ Hard-coded: {column} = {hard_value}")
            else:
                # Add new column with hard-coded value
                final_df[column] = hard_value
                hard_coded_count += 1
                print(f"✓ Hard-coded (new column): {column} = {hard_value}")
    
    print(f"Applied {hard_coded_count} hard-coded values")
    
    # Step 5: Apply default values for Oracle required fields (only where needed)
    print("\nStep 5: Applying default values for required Oracle fields...")
    
    default_values = {
        'LINE_TYPE': 'LINE',
        'CONVERSION_TYPE': 'Corporate',
        'QUANTITY_INVOICED': 1,
        'TAX_EXEMPT_FLAG': 'N',
    }
    
    defaults_applied = 0
    for col, default_val in default_values.items():
        if col in final_df.columns:
            # Only fill NaN values, don't overwrite existing data or hard-coded values
            null_count_before = final_df[col].isnull().sum()
            final_df[col] = final_df[col].fillna(default_val)
            null_count_after = final_df[col].isnull().sum()
            if null_count_before > null_count_after:
                defaults_applied += 1
                print(f"✓ Default applied: {col} = {default_val} ({null_count_before - null_count_after} rows)")
        else:
            # Add column with default value if it doesn't exist
            final_df[col] = default_val
            defaults_applied += 1
            print(f"✓ Default added: {col} = {default_val}")
    
    # Generate line numbers
    if len(final_df) > 0:
        final_df['LINE_NUMBER'] = range(1, len(final_df) + 1)
    
    print(f"Final data: {len(final_df)} records with {len(final_df.columns)} total columns")
    
    # Step 6: Reorder columns to match template structure (template columns first, then raw data columns)
    print("\nStep 6: Organizing column order...")
    
    # Get columns in preferred order: template columns first, then remaining raw data columns
    ordered_columns = []
    
    # Add template columns first (in template order)
    for col in template_headers:
        if col in final_df.columns:
            ordered_columns.append(col)
    
    # Add remaining raw data columns that aren't in template
    for col in raw_df.columns:
        if col not in ordered_columns:
            ordered_columns.append(col)
    
    # Add any other columns that might have been created
    for col in final_df.columns:
        if col not in ordered_columns:
            ordered_columns.append(col)
    
    # Reorder the dataframe
    final_df = final_df[ordered_columns]
    
    print(f"Column order organized: {len(ordered_columns)} total columns")
    
    # Step 7: Generate CSV file
    print("\nStep 7: Generating CSV file...")
    csv_filename = 'RA_INTERFACE_LINES_ALL_Data.csv'
    
    # Save to CSV with ALL data
    final_df.to_csv(csv_filename, index=False, encoding='utf-8')
    print(f"CSV file created: {csv_filename}")
    
    # Step 8: Create ZIP file
    print("\nStep 8: Creating ZIP file for Oracle Fusion upload...")
    zip_filename = f'RA_INTERFACE_LINES_ALL_{datetime.now().strftime("%Y%m%d_%H%M%S")}.zip'
    
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        zipf.write(csv_filename)
    
    print(f"ZIP file created: {zip_filename}")
    
    # Step 9: Data validation and summary
    print("\n" + "="*60)
    print("FBDI PROCESSING SUMMARY")
    print("="*60)
    print(f"Template: {template_path}")
    print(f"Raw data: {raw_data_path}")
    print(f"Records processed: {len(final_df)}")
    print(f"Raw data columns: {len(raw_df.columns)}")
    print(f"Template columns: {len(template_headers)}")
    print(f"Total final columns: {len(final_df.columns)}")
    print(f"Hard-coded values: {hard_coded_count}")
    print(f"CSV file: {csv_filename}")
    print(f"ZIP file ready for upload: {zip_filename}")
    print(f"File size: {os.path.getsize(zip_filename)} bytes")
    
    # Display validation results
    validate_ra_interface_data(final_df)
    
    # Show sample data
    if len(final_df) > 0:
        print("\nSample of processed data (first 3 rows, first 10 columns):")
        print(final_df.iloc[:3, :10].to_string())
        
        print(f"\nAll columns included in final output:")
        for i, col in enumerate(final_df.columns, 1):
            has_data = "✓" if final_df[col].notna().any() else "✗"
            print(f"{i:3d}. {has_data} {col}")
        
        # Show summary of hard-coded values
        if hard_coded_values:
            print(f"\nHard-coded values applied to all {len(final_df)} records:")
            for col, val in hard_coded_values.items():
                print(f"  {col}: {val}")
    else:
        print("\nNo data to display")
    
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
    
    # Summary statistics
    print(f"\nSUMMARY STATISTICS:")
    print(f"Total records: {len(df)}")
    if len(df) > 0:
        print(f"Total columns: {len(df.columns)}")
        print(f"Columns with data: {sum(df.count() > 0)}")
        print(f"Completely empty columns: {sum(df.count() == 0)}")

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
- Ensure all required setups are complete in Oracle Fusion
- Verify customer and site references exist
- Check currency and conversion rates
- Review tax classifications if applicable
- All raw data columns have been preserved
- Hard-coded values from template have been applied automatically

VALIDATION CHECKLIST:
- All required fields populated
- Customer references valid
- Amounts and quantities correct
- Dates in proper format
- Currency codes valid
- No duplicate transaction numbers
- All raw data preserved
- Template structure included
- Hard-coded values applied
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
            print(f"Review instructions in: FBDI_Control_Instructions.txt")
        else:
            print("FBDI processing failed!")
            
    except Exception as e:
        print(f"Error during FBDI processing: {str(e)}")
        import traceback
        traceback.print_exc()
