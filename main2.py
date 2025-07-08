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
        for i in range(min(10, len(template_df))):
            row_values = template_df.iloc[i].astype(str).tolist()
            # Look for rows that contain actual column names (not "Unnamed" or empty)
            if any('BATCH_SOURCE' in str(val) or 'TRX_' in str(val) or 'AMOUNT' in str(val) for val in row_values):
                actual_headers = row_values
                header_row = i
                break
        
        if actual_headers:
            template_df = pd.read_excel(template_path, header=header_row)
            template_headers = template_df.columns.tolist()
            print(f"Template loaded successfully with {len(template_headers)} columns")
            print("First 10 template columns:", template_headers[:10])
        else:
            # If we can't find proper headers, create a basic structure
            print("Could not find proper headers in template. Using basic structure.")
            template_headers = ['BATCH_SOURCE_NAME', 'TRX_NUMBER', 'TRX_DATE', 'CURRENCY_CODE', 
                             'AMOUNT', 'LINE_TYPE', 'DESCRIPTION', 'CUST_TRX_TYPE_NAME']
        
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
        print("Raw data columns:", list(raw_df.columns)[:10])  # Show first 10 columns
        
    except Exception as e:
        print(f"Error loading raw data: {e}")
        return None, None
    
    # Step 3: Map raw data to RA_INTERFACE_LINES_ALL structure
    print("\nStep 3: Mapping data to RA_INTERFACE_LINES_ALL format...")
    
    # Create the mapped dataframe
    mapped_df = pd.DataFrame()
    
    # Updated column mappings based on what we might find in your raw data
    # You'll need to update these based on your actual column names
    column_mappings = {
        'BATCH_SOURCE_NAME': 'Transaction Batch Source Name',  # Remove the *
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
    
    # Debug: Print available columns for mapping
    print("\nAvailable raw data columns for mapping:")
    for i, col in enumerate(raw_df.columns):
        print(f"{i+1}. {col}")
    
    # Map the data
    mapped_count = 0
    for ra_column, raw_column in column_mappings.items():
        if raw_column and raw_column in raw_df.columns:
            mapped_df[ra_column] = raw_df[raw_column]
            mapped_count += 1
            print(f"✓ Mapped: {raw_column} -> {ra_column}")
        else:
            mapped_df[ra_column] = None
            print(f"✗ Not found: {raw_column}")
    
    print(f"\nSuccessfully mapped {mapped_count} columns")
    
    # Step 4: Apply data transformations and validations
    print("\nStep 4: Applying data transformations...")
    
    # Set default values for required fields
    default_values = {
        'LINE_TYPE': 'LINE',
        'CONVERSION_TYPE': 'Corporate',
        'QUANTITY_INVOICED': 1,
        'TAX_EXEMPT_FLAG': 'N',
    }
    
    for col, default_val in default_values.items():
        if col in mapped_df.columns:
            mapped_df[col] = mapped_df[col].fillna(default_val)
    
    # Generate line numbers
    if len(mapped_df) > 0:
        mapped_df['LINE_NUMBER'] = range(1, len(mapped_df) + 1)
    
    # Don't remove rows with missing data yet - let's see what we have
    print(f"Mapped data: {len(mapped_df)} records")
    
    # Step 5: Generate CSV file
    print("\nStep 5: Generating CSV file...")
    csv_filename = 'RA_INTERFACE_LINES_ALL_Data.csv'
    
    # Use only the columns we successfully mapped
    final_df = mapped_df.copy()
    
    # Save to CSV
    final_df.to_csv(csv_filename, index=False, encoding='utf-8')
    print(f"CSV file created: {csv_filename}")
    
    # Step 6: Create ZIP file
    print("\nStep 6: Creating ZIP file for Oracle Fusion upload...")
    zip_filename = f'RA_INTERFACE_LINES_ALL_{datetime.now().strftime("%Y%m%d_%H%M%S")}.zip'
    
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        zipf.write(csv_filename)
    
    print(f"ZIP file created: {zip_filename}")
    
    # Step 7: Data validation and summary
    print("\n" + "="*60)
    print("FBDI PROCESSING SUMMARY")
    print("="*60)
    print(f"Template: {template_path}")
    print(f"Raw data: {raw_data_path}")
    print(f"Records processed: {len(final_df)}")
    print(f"CSV file: {csv_filename}")
    print(f"ZIP file ready for upload: {zip_filename}")
    print(f"File size: {os.path.getsize(zip_filename)} bytes")
    
    # Display validation results
    validate_ra_interface_data(final_df)
    
    # Show sample data
    if len(final_df) > 0:
        print("\nSample of processed data (first 3 rows):")
        print(final_df.head(3).to_string())
    else:
        print("\nNo data to display - check column mappings")
    
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
        print(f"Columns with data: {df.count().sum()}")
        print(f"Columns: {list(df.columns)}")

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

VALIDATION CHECKLIST:
- All required fields populated
- Customer references valid
- Amounts and quantities correct
- Dates in proper format
- Currency codes valid
- No duplicate transaction numbers
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
