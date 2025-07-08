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
        # Read the template to understand the structure
        template_df = pd.read_excel(template_path)
        print(f"Template loaded successfully with {len(template_df.columns)} columns")
        print("Template columns:", list(template_df.columns))
        
        # Get the template structure (usually first few rows contain metadata)
        template_headers = template_df.columns.tolist()
        
        
        
    except Exception as e:
        print(f"Error loading template: {e}")
        return None, None
    
    # Step 2: Load and process raw data
    print("\nStep 2: Loading raw customer invoice data...")
    raw_data_path = 'C:/Users/SohamKasurde/Conversion/Customer Invoice Conversion Data - RAW File.xlsx'
    
    try:
        # Load raw data
        raw_df = pd.read_excel(raw_data_path)
        
        # Clean the raw data (remove header row if needed)
        if raw_df.iloc[0].astype(str).str.contains('Hard Code Value').any():
            new_header = raw_df.iloc[0]
            raw_df = raw_df[1:]
            raw_df.columns = new_header
            raw_df.reset_index(drop=True, inplace=True)
        
        print(f"Raw data loaded: {len(raw_df)} records")
        print("Raw data columns:", list(raw_df.columns))
        
    except Exception as e:
        print(f"Error loading raw data: {e}")
        return None, None
    
    # Step 3: Map raw data to RA_INTERFACE_LINES_ALL structure
    print("\nStep 3: Mapping data to RA_INTERFACE_LINES_ALL format...")
    
    # Create the mapped dataframe with RA_INTERFACE_LINES_ALL structure
    mapped_df = pd.DataFrame()
    
    # Standard RA_INTERFACE_LINES_ALL column mappings
    column_mappings = {
        # Required fields for RA_INTERFACE_LINES_ALL
        'BATCH_SOURCE_NAME': '*Transaction Batch Source Name',
        'SET_OF_BOOKS_ID': None,  # Will be populated based on business unit
        'LINE_TYPE': '*Transaction Line Type',
        'DESCRIPTION': '*Transaction Line Description',
        'CURRENCY_CODE': '*Currency Code',
        'AMOUNT': 'Transaction Line Amount',
        'QUANTITY_INVOICED': 'Transaction Line Quantity',
        'UNIT_SELLING_PRICE': 'Unit Selling Price',
        'TRX_DATE': 'Transaction Date',
        'GL_DATE': 'Accounting Date',
        'CONVERSION_TYPE': '*Currency Conversion Type',
        'CONVERSION_DATE': 'Currency Conversion Date',
        'CONVERSION_RATE': 'Currency Conversion Rate',
        
        # Customer information
        'ORIG_SYSTEM_BILL_CUSTOMER_REF': 'Bill-to Customer Number',
        'ORIG_SYSTEM_BILL_ADDRESS_REF': 'Bill-to Customer Site Number',
        'ORIG_SYSTEM_SHIP_CUSTOMER_REF': 'Ship-to Customer Number',
        'ORIG_SYSTEM_SHIP_ADDRESS_REF': 'Ship-to Customer Site Number',
        
        # Transaction details
        'TRX_NUMBER': 'Transaction Number',
        'CUST_TRX_TYPE_NAME': '*Transaction Type Name',
        'TERM_NAME': 'Payment Terms',
        'INVOICE_CURRENCY_CODE': '*Currency Code',
        
        # Additional fields
        'INTERFACE_LINE_CONTEXT': 'Interface Line Context',
        'INTERFACE_LINE_ATTRIBUTE1': 'Interface Line Attribute1',
        'INTERFACE_LINE_ATTRIBUTE2': 'Interface Line Attribute2',
        'INTERFACE_LINE_ATTRIBUTE3': 'Interface Line Attribute3',
        'INTERFACE_LINE_ATTRIBUTE4': 'Interface Line Attribute4',
        'INTERFACE_LINE_ATTRIBUTE5': 'Interface Line Attribute5',
        
        # Accounting information
        'ACCOUNTING_RULE_NAME': 'Accounting Rule Name',
        'RULE_START_DATE': 'Rule Start Date',
        'RULE_END_DATE': 'Rule End Date',
        
        # Tax information
        'TAX_CLASSIFICATION_CODE': 'Tax Classification Code',
        'TAX_EXEMPT_FLAG': 'Tax Exempt Flag',
        'TAX_EXEMPT_REASON_CODE': 'Tax Exempt Reason Code',
        
        # Reference fields
        'REFERENCE_LINE_CONTEXT': 'Reference Line Context',
        'REFERENCE_LINE_ATTRIBUTE1': 'Reference Line Attribute1',
        'REFERENCE_LINE_ATTRIBUTE2': 'Reference Line Attribute2',
        'REFERENCE_LINE_ATTRIBUTE3': 'Reference Line Attribute3',
        'REFERENCE_LINE_ATTRIBUTE4': 'Reference Line Attribute4',
        'REFERENCE_LINE_ATTRIBUTE5': 'Reference Line Attribute5',
    }
    
    # Map the data
    for ra_column, raw_column in column_mappings.items():
        if raw_column and raw_column in raw_df.columns:
            mapped_df[ra_column] = raw_df[raw_column]
        else:
            mapped_df[ra_column] = None
    
    # Step 4: Apply data transformations and validations
    print("\nStep 4: Applying data transformations...")
    
    # Date formatting
    date_columns = ['TRX_DATE', 'GL_DATE', 'CONVERSION_DATE', 'RULE_START_DATE', 'RULE_END_DATE']
    for col in date_columns:
        if col in mapped_df.columns:
            mapped_df[col] = pd.to_datetime(mapped_df[col], errors='coerce').dt.strftime('%Y-%m-%d')
    
    # Numeric formatting
    numeric_columns = ['AMOUNT', 'QUANTITY_INVOICED', 'UNIT_SELLING_PRICE', 'CONVERSION_RATE']
    for col in numeric_columns:
        if col in mapped_df.columns:
            mapped_df[col] = pd.to_numeric(mapped_df[col], errors='coerce')
    
    # Set default values for required fields if empty
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
    mapped_df['LINE_NUMBER'] = range(1, len(mapped_df) + 1)
    
    # Remove rows with critical missing data
    critical_fields = ['BATCH_SOURCE_NAME', 'CURRENCY_CODE', 'AMOUNT']
    for field in critical_fields:
        if field in mapped_df.columns:
            mapped_df = mapped_df.dropna(subset=[field])
    
    print(f"Mapped data: {len(mapped_df)} records")
    
    # Step 5: Generate CSV file
    print("\nStep 5: Generating CSV file...")
    csv_filename = 'RA_INTERFACE_LINES_ALL_Data.csv'
    
    # Ensure we only include columns that exist in the template
    final_columns = [col for col in template_headers if col in mapped_df.columns]
    final_df = mapped_df[final_columns].copy()
    
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
    print("\nSample of processed data (first 3 rows):")
    print(final_df.head(3).to_string())
    
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
                validation_results.append(f"⚠️  WARNING: {field} has {null_count} null values")
            else:
                validation_results.append(f"✅ OK: {field} - no null values")
        else:
            validation_results.append(f"❌ ERROR: Required field {field} not found")
    
    # Check for duplicate transaction numbers
    if 'TRX_NUMBER' in df.columns:
        duplicates = df['TRX_NUMBER'].duplicated().sum()
        if duplicates > 0:
            validation_results.append(f"  WARNING: {duplicates} duplicate transaction numbers")
        else:
            validation_results.append(" OK: No duplicate transaction numbers")
    
    # Check amount values
    if 'AMOUNT' in df.columns:
        zero_amounts = (df['AMOUNT'] == 0).sum()
        negative_amounts = (df['AMOUNT'] < 0).sum()
        if zero_amounts > 0:
            validation_results.append(f"  WARNING: {zero_amounts} records with zero amount")
        if negative_amounts > 0:
            validation_results.append(f" INFO: {negative_amounts} records with negative amount (credit memos)")
    
    # Check date formats
    date_fields = ['TRX_DATE', 'GL_DATE']
    for field in date_fields:
        if field in df.columns:
            invalid_dates = df[field].isnull().sum()
            if invalid_dates > 0:
                validation_results.append(f" WARNING: {field} has {invalid_dates} invalid dates")
            else:
                validation_results.append(f" OK: {field} - all dates valid")
    
    # Print validation results
    for result in validation_results:
        print(result)
    
    # Summary statistics
    print(f"\n📊 SUMMARY STATISTICS:")
    print(f"Total records: {len(df)}")
    if 'AMOUNT' in df.columns:
        print(f"Total amount: {df['AMOUNT'].sum():,.2f}")
        print(f"Average amount: {df['AMOUNT'].mean():,.2f}")
    if 'CURRENCY_CODE' in df.columns:
        print(f"Currencies: {df['CURRENCY_CODE'].nunique()} unique")
        print(f"Currency breakdown:")
        print(df['CURRENCY_CODE'].value_counts().to_string())

def create_control_file():
    """Create a control file with processing instructions"""
    control_content = f"""
# Oracle Fusion Receivables FBDI Control File
# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

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
□ All required fields populated
□ Customer references valid
□ Amounts and quantities correct
□ Dates in proper format
□ Currency codes valid
□ No duplicate transaction numbers
"""
    
    with open('FBDI_Control_Instructions.txt', 'w') as f:
        f.write(control_content)
    
    print("📋 Control file created: FBDI_Control_Instructions.txt")

# Main execution
if __name__ == "__main__":
    try:
        print("🚀 Starting Oracle Fusion Receivables FBDI Processing...")
        
        # Process the data
        zip_file, csv_file = process_fbdi_receivables()
        
        # Create control file
        create_control_file()
        
        if zip_file and csv_file:
            print(f"\n🎉 FBDI processing completed successfully!")
            print(f"📁 Upload this file to Oracle Fusion: {zip_file}")
            print(f"📋 Review instructions in: FBDI_Control_Instructions.txt")
        else:
            print("❌ FBDI processing failed!")
            
    except Exception as e:
        print(f"❌ Error during FBDI processing: {str(e)}")
        import traceback
        traceback.print_exc()
