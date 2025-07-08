import streamlit as st
import pandas as pd
import zipfile
import os
from datetime import datetime
import numpy as np
import tempfile
import shutil
from io import BytesIO

def process_fbdi_with_uploads(template_file, raw_file):
    """Process FBDI with uploaded files - no computer paths needed"""
    
    # Create temporary directory for processing
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Save uploaded files to temporary location
        template_path = os.path.join(temp_dir, "template.xlsm")
        raw_data_path = os.path.join(temp_dir, "raw_data.xlsx")
        
        # Write uploaded files to temp directory
        with open(template_path, "wb") as f:
            f.write(template_file.getbuffer())
        with open(raw_data_path, "wb") as f:
            f.write(raw_file.getbuffer())
        
        # Process the files
        zip_file, csv_file = process_fbdi_receivables_uploaded(template_path, raw_data_path, temp_dir)
        
        return zip_file, csv_file, temp_dir
        
    except Exception as e:
        # Clean up on error
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise e

def process_fbdi_receivables_uploaded(template_path, raw_data_path, output_dir):
    """Complete FBDI processing for uploaded files"""
    
    print("="*60)
    print("ORACLE FUSION RECEIVABLES FBDI PROCESSOR")
    print("="*60)
    
    # Step 1: Load the RA_INTERFACE_LINES_ALL template
    print("\nStep 1: Loading uploaded template...")
    
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
    print("\nStep 2: Loading uploaded raw data...")
    
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
        
    except Exception as e:
        print(f"Error loading raw data: {e}")
        return None, None
    
    # Step 3: Create comprehensive column equivalence mapping
    print("\nStep 3: Creating comprehensive column equivalence mapping...")
    
    def clean_column_name(col_name):
        """Remove asterisks and extra spaces from column names"""
        cleaned = str(col_name).strip()
        # Remove leading and trailing asterisks
        cleaned = cleaned.strip('*').strip()
        return cleaned
    
    # Column equivalence mapping with asterisk handling
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
        
        # LINE TYPE variations - Handle asterisk variations
        'LINE_TYPE': 'Transaction Line Type',
        'Line Type': 'Transaction Line Type',
        'LINETYPE': 'Transaction Line Type',
        'Transaction Line Type': 'Transaction Line Type',
        '*Transaction Line Type*': 'Transaction Line Type',
        '*Transaction Line Type': 'Transaction Line Type',
        'Transaction Line Type*': 'Transaction Line Type',
        
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
        
        # Line Number variations
        'LINE_NUMBER': 'LINE_NUMBER',
        'Line Number': 'LINE_NUMBER',
        'LINENUMBER': 'LINE_NUMBER',
    }
    
    def normalize_columns_with_asterisk_handling(columns, equivalence_map):
        """Normalize column names, handle asterisks, and remove ALL duplicates"""
        normalized = []
        seen = set()
        duplicates_found = []
        
        for col in columns:
            # First clean the column name (remove asterisks)
            cleaned_col = clean_column_name(col)
            
            # Then get normalized column name (try both original and cleaned)
            norm_col = equivalence_map.get(col, equivalence_map.get(cleaned_col, cleaned_col))
            
            if norm_col not in seen:
                normalized.append(norm_col)
                seen.add(norm_col)
            else:
                duplicates_found.append((col, norm_col))
        
        return normalized
    
    # Normalize template columns with asterisk handling
    normalized_template_headers = normalize_columns_with_asterisk_handling(template_headers, column_equivalence)
    
    # Additional duplicate check
    final_unique_headers = []
    seen_final = set()
    
    for col in normalized_template_headers:
        if col not in seen_final:
            final_unique_headers.append(col)
            seen_final.add(col)
    
    # Step 4: Create final dataframe with unique normalized columns
    if len(raw_df) > 0:
        # Create dataframe with final unique columns
        final_df = pd.DataFrame(index=range(len(raw_df)), columns=final_unique_headers)
        # Initialize all columns with None/NaN
        for col in final_unique_headers:
            final_df[col] = None
    else:
        final_df = pd.DataFrame(columns=final_unique_headers)
    
    # Step 5: Apply hard-coded values from template
    hard_coded_count = 0
    if hard_coded_values:
        for original_col, hard_value in hard_coded_values.items():
            # Clean and normalize the column name
            cleaned_col = clean_column_name(original_col)
            normalized_col = column_equivalence.get(original_col, column_equivalence.get(cleaned_col, cleaned_col))
            
            if normalized_col in final_df.columns:
                final_df[normalized_col] = hard_value
                hard_coded_count += 1
    
    # Step 6: Map raw data to normalized template columns
    mapped_count = 0
    for raw_col in raw_df.columns:
        # Clean and normalize the raw column name
        cleaned_raw_col = clean_column_name(raw_col)
        normalized_col = column_equivalence.get(raw_col, column_equivalence.get(cleaned_raw_col, cleaned_raw_col))
        
        if normalized_col in final_df.columns:
            # Only map if not already set by hard-coded values
            if final_df[normalized_col].isnull().all():
                final_df[normalized_col] = raw_df[raw_col].values
                mapped_count += 1
    
    # Step 7: Apply default values for Oracle required fields
    default_values = {
        'Transaction Line Type': 'LINE',
        'CONVERSION_TYPE': 'Corporate',
        'QUANTITY_INVOICED': 1,
        'TAX_EXEMPT_FLAG': 'N',
    }
    
    for col, default_val in default_values.items():
        if col in final_df.columns:
            final_df[col] = final_df[col].fillna(default_val)
    
    # Step 8: Add any unmapped raw data columns
    additional_columns = []
    for raw_col in raw_df.columns:
        cleaned_raw_col = clean_column_name(raw_col)
        normalized_col = column_equivalence.get(raw_col, column_equivalence.get(cleaned_raw_col, cleaned_raw_col))
        # Add if it's not already in our final dataframe
        if normalized_col not in final_df.columns:
            final_df[normalized_col] = raw_df[raw_col].values
            additional_columns.append(raw_col)
    
    # Step 9: Generate line numbers
    if len(final_df) > 0:
        if 'LINE_NUMBER' not in final_df.columns:
            final_df['LINE_NUMBER'] = range(1, len(final_df) + 1)
        else:
            final_df['LINE_NUMBER'] = range(1, len(final_df) + 1)
    
    # Step 10: Generate CSV file in output directory
    csv_filename = os.path.join(output_dir, 'RA_INTERFACE_LINES_ALL_Data.csv')
    final_df.to_csv(csv_filename, index=False, encoding='utf-8')
    
    # Step 11: Create ZIP file in output directory
    zip_filename = os.path.join(output_dir, f'RA_INTERFACE_LINES_ALL_{datetime.now().strftime("%Y%m%d_%H%M%S")}.zip')
    
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        zipf.write(csv_filename, os.path.basename(csv_filename))
    
    print(f"\n✅ Processing completed!")
    print(f"Records processed: {len(final_df)}")
    print(f"Final columns: {len(final_df.columns)}")
    print(f"Hard-coded values: {hard_coded_count}")
    print(f"Mapped columns: {mapped_count}")
    
    return zip_filename, csv_filename

def main():
    st.set_page_config(
        page_title="Oracle Fusion FBDI Processor",
        page_icon="📊",
        layout="wide"
    )
    
    st.title("🚀 Oracle Fusion Receivables FBDI Processor")
    st.markdown("Transform your raw invoice data into Oracle Fusion ready format!")
    st.markdown("---")
    
    # Instructions
    with st.expander("📖 How to use this tool", expanded=False):
        st.markdown("""
        ### Step-by-step guide:
        1. **Upload FBDI Template** - Your Oracle Fusion RA_INTERFACE_LINES_ALL template (.xlsm)
        2. **Upload Raw Data** - Your customer invoice data (.xlsx)
        3. **Click Process** - The tool will map raw data to template format
        4. **Download ZIP** - Upload the ZIP file to Oracle Fusion
        
        ### What this tool does:
        - ✅ Maps raw data columns to Oracle template columns
        - ✅ Applies hard-coded values from template
        - ✅ Removes duplicate columns
        - ✅ Handles asterisk variations (*Column Name*)
        - ✅ Generates LINE_NUMBER automatically
        - ✅ Creates Oracle-ready ZIP file
        """)
    
    # File upload section
    st.header("📁 Upload Files")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📄 FBDI Template")
        template_file = st.file_uploader(
            "Upload Oracle FBDI Template",
            type=['xlsm', 'xlsx'],
            key="template",
            help="Upload your RA_INTERFACE_LINES_ALL template file from Oracle Fusion"
        )
        
        if template_file:
            st.success(f"✅ Template uploaded: {template_file.name}")
            st.info(f"📊 File size: {len(template_file.getbuffer()):,} bytes")
        
    with col2:
        st.subheader("📊 Raw Invoice Data")
        raw_file = st.file_uploader(
            "Upload Raw Invoice Data",
            type=['xlsx'],
            key="raw_data",
            help="Upload your customer invoice conversion data file"
        )
        
        if raw_file:
            st.success(f"✅ Raw data uploaded: {raw_file.name}")
            st.info(f"📊 File size: {len(raw_file.getbuffer()):,} bytes")
    
    # Processing section
    if template_file and raw_file:
        st.markdown("---")
        st.header("⚙️ Process Files")
        
        # Process button
        if st.button("🔄 Process FBDI Files", type="primary", use_container_width=True):
            
            # Create progress indicators
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            try:
                status_text.text("📁 Processing uploaded files...")
                progress_bar.progress(20)
                
                status_text.text("🔄 Mapping raw data to template...")
                progress_bar.progress(50)
                
                # Process the files
                zip_file, csv_file, temp_dir = process_fbdi_with_uploads(template_file, raw_file)
                progress_bar.progress(90)
                
                if zip_file and csv_file and os.path.exists(zip_file):
                    status_text.text("✅ Processing completed successfully!")
                    progress_bar.progress(100)
                    
                    st.success("🎉 FBDI Processing Completed Successfully!")
                    
                    # Display results
                    st.markdown("---")
                    st.header("📊 Processing Results")
                    
                    # Load and show CSV preview
                    df = pd.read_csv(csv_file)
                    
                    # Statistics
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("📊 Records Processed", len(df))
                    with col2:
                        st.metric("📋 Total Columns", len(df.columns))
                    with col3:
                        st.metric("✅ Columns with Data", sum(df.count() > 0))
                    with col4:
                        file_size = os.path.getsize(zip_file)
                        st.metric("📦 ZIP File Size", f"{file_size:,} bytes")
                    
                    # Show data preview
                    st.subheader("📋 Data Preview (First 10 rows)")
                    st.dataframe(df.head(10), use_container_width=True)
                    
                    # Column mapping summary
                    with st.expander("🔍 View Column Mapping Details"):
                        st.write("**Columns in final output:**")
                        for i, col in enumerate(df.columns, 1):
                            has_data = "✅" if df[col].notna().any() else "❌"
                            st.write(f"{i:3d}. {has_data} {col}")
                    
                    # Download section
                    st.markdown("---")
                    st.header("📥 Download Processed Files")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Download ZIP file
                        with open(zip_file, "rb") as f:
                            st.download_button(
                                label="📦 Download ZIP for Oracle Upload",
                                data=f.read(),
                                file_name=os.path.basename(zip_file),
                                mime="application/zip",
                                use_container_width=True,
                                type="primary"
                            )
                        st.caption("⬆️ Upload this ZIP file to Oracle Fusion")
                    
                    with col2:
                        # Download CSV file
                        csv_data = df.to_csv(index=False).encode('utf-8')
                        st.download_button(
                            label="📄 Download CSV File",
                            data=csv_data,
                            file_name=os.path.basename(csv_file),
                            mime="text/csv",
                            use_container_width=True
                        )
                        st.caption("📊 For review and validation")
                    
                    # Oracle upload instructions
                    st.markdown("---")
                    st.header("📋 Oracle Fusion Upload Instructions")
                    
                    st.info("""
                    **Ready to upload to Oracle Fusion!** Follow these steps:
                    
                    1. **Log into Oracle Fusion Cloud**
                    2. **Navigate to:** Receivables → Billing → Import AutoInvoice
                    3. **Click:** "Import Transactions"
                    4. **Upload** the ZIP file you downloaded above
                    5. **Select** appropriate batch source and run the import
                    6. **Monitor** the import process in Scheduled Processes
                    """)
                    
                    # Clean up temp directory after a delay
                    if temp_dir and os.path.exists(temp_dir):
                        shutil.rmtree(temp_dir, ignore_errors=True)
                    
                else:
                    st.error("❌ Processing failed! Please check your files and try again.")
                    status_text.text("❌ Processing failed!")
                    progress_bar.progress(0)
                    
            except Exception as e:
                st.error(f"❌ Error during processing: {str(e)}")
                status_text.text(f"❌ Error: {str(e)}")
                progress_bar.progress(0)
                
                # Show detailed error in expander
                with st.expander("🔍 View Error Details"):
                    st.code(str(e))
    
    else:
        st.info("👆 Please upload both FBDI template and raw data files to begin processing.")
        
        # Show file requirements
        st.markdown("---")
        st.header("📋 File Requirements")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            **FBDI Template File:**
            - ✅ Oracle Fusion RA_INTERFACE_LINES_ALL template
            - ✅ File format: .xlsm or .xlsx
            - ✅ Contains column headers and hard-coded values
            - ✅ Downloaded from Oracle Fusion
            """)
        
        with col2:
            st.markdown("""
            **Raw Invoice Data File:**
            - ✅ Customer invoice conversion data
            - ✅ File format: .xlsx
            - ✅ Contains actual transaction data
            - ✅ Column headers in first few rows
            """)

if __name__ == "__main__":
    main()
