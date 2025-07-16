import pandas as pd
import tempfile
import shutil
import zipfile
import os
from datetime import datetime

class FileProcessor:
    """Utility class for processing Excel and CSV files"""
    
    @staticmethod
    def save_uploaded_file(uploaded_file, suffix=".xlsx"):
        """Save uploaded file to temporary location"""
        tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        shutil.copyfileobj(uploaded_file.stream, tmp_file)
        tmp_file.close()
        return tmp_file.name
    
    @staticmethod
    def read_template_file(template_path, sheet_name="RA_INTERFACE_LINES_ALL"):
        """Read FBDI template file"""
        if not os.path.exists(template_path):
            raise FileNotFoundError(f"Template file not found: {template_path}")
        
        return pd.read_excel(template_path, sheet_name=sheet_name, header=None)
    
    @staticmethod
    def read_raw_file(file_path, sheet_index=0):
        """Read raw data file"""
        return pd.read_excel(file_path, sheet_name=sheet_index, header=None)
    
    @staticmethod
    def create_zip_file(csv_file_path, zip_filename="fbdi_output.zip"):
        """Create ZIP file containing CSV"""
        zip_path = tempfile.NamedTemporaryFile(delete=False, suffix=".zip").name
        
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(csv_file_path, arcname="fbdi_output.csv")
        
        return zip_path
    
    @staticmethod
    def cleanup_temp_files(*file_paths):
        """Clean up temporary files"""
        for file_path in file_paths:
            try:
                if file_path and os.path.exists(file_path):
                    os.remove(file_path)
            except Exception as e:
                print(f"Error cleaning up file {file_path}: {e}")
    
    @staticmethod
    def generate_filename(project_name, fbdi_type, extension="zip"):
        """Generate standardized filename"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"{project_name}_{fbdi_type}_FBDI_{timestamp}.{extension}"
