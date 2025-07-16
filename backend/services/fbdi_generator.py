import pandas as pd
import tempfile
import os
from utils.file_processor import FileProcessor
from utils.mapping_manager import MappingManager

class FBDIGeneratorService:
    """Service class for FBDI generation operations"""
    
    def __init__(self, config):
        self.config = config
        self.file_processor = FileProcessor()
        self.mapping_manager = MappingManager()
    
    def generate_fbdi(self, raw_file, fbdi_type, project_name, env_type):
        """
        Generate FBDI file from raw data
        
        Args:
            raw_file: Uploaded raw file
            fbdi_type: Type of FBDI template to use
            project_name: Project name for file naming
            env_type: Environment type
            
        Returns:
            dict: Generation result with file path and metadata
        """
        temp_files = []
        
        try:
            # Validate template exists
            template_path = f"{self.config.TEMPLATES_PATH}/{fbdi_type}_template.xlsm"
            if not os.path.exists(template_path):
                return {"success": False, "error": f"Template for type '{fbdi_type}' not found"}
            
            # Save uploaded file temporarily
            tmp_raw = self.file_processor.save_uploaded_file(raw_file, ".xlsx")
            temp_files.append(tmp_raw)
            
            # Read template and raw files
            template_df = self.file_processor.read_template_file(template_path)
            raw_df = self.file_processor.read_raw_file(tmp_raw)
            
            # Extract columns and data
            template_columns = template_df.iloc[3].tolist()
            raw_columns = raw_df.iloc[1].tolist()
            raw_data = raw_df.iloc[2:].reset_index(drop=True)
            
            # Prepare template dataframe
            start_row = 4
            num_rows = raw_data.shape[0]
            
            if template_df.shape[0] < start_row + num_rows:
                empty_rows = pd.DataFrame([[""] * template_df.shape[1]] * (start_row + num_rows - template_df.shape[0]))
                template_df = pd.concat([template_df, empty_rows], ignore_index=True)
            
            # Get stored mappings and apply them
            stored_mappings = self.mapping_manager.get_latest_mappings()
            template_df = self.mapping_manager.apply_mappings(
                template_df, raw_data, template_columns, raw_columns, stored_mappings, start_row
            )
            
            # Remove Business Unit Name column if exists
            if "*Buisness Unit Name" in template_columns:
                col_idx = template_columns.index("*Buisness Unit Name")
                template_df = template_df.drop(columns=col_idx, axis=1)
            
            # Extract final data
            final_df = template_df.iloc[start_row:start_row + num_rows]
            
            # Save to CSV
            csv_path = tempfile.NamedTemporaryFile(delete=False, suffix=".csv").name
            temp_files.append(csv_path)
            final_df.to_csv(csv_path, index=False, header=False, date_format='%Y/%m/%d')
            
            # Create ZIP file
            zip_filename = self.file_processor.generate_filename(project_name, fbdi_type)
            zip_path = self.file_processor.create_zip_file(csv_path, zip_filename)
            temp_files.append(zip_path)
            
            return {
                "success": True,
                "zip_path": zip_path,
                "filename": zip_filename,
                "temp_files": temp_files,
                "metadata": {
                    "project_name": project_name,
                    "fbdi_type": fbdi_type,
                    "env_type": env_type,
                    "rows_processed": num_rows
                }
            }
            
        except Exception as e:
            # Cleanup temp files on error
            self.file_processor.cleanup_temp_files(*temp_files)
            return {"success": False, "error": str(e)}
