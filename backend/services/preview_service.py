import os
from utils.file_processor import FileProcessor
from utils.mapping_manager import MappingManager

class PreviewService:
    """Service class for mapping preview operations"""
    
    def __init__(self, config):
        self.config = config
        self.file_processor = FileProcessor()
        self.mapping_manager = MappingManager()
    
    def generate_preview(self, raw_file, fbdi_type):
        """
        Generate mapping preview for uploaded file
        
        Args:
            raw_file: Uploaded raw file
            fbdi_type: Type of FBDI template
            
        Returns:
            dict: Preview result with mappings
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
            
            # Extract columns
            template_columns = template_df.iloc[3].tolist()
            raw_columns = raw_df.iloc[1].tolist()
            
            # Get stored mappings
            stored_mappings = self.mapping_manager.get_latest_mappings()
            
            # Create mapping preview
            mappings = self.mapping_manager.create_mapping_preview(
                template_columns, raw_columns, stored_mappings
            )
            
            # Cleanup temp files
            self.file_processor.cleanup_temp_files(*temp_files)
            
            return {
                "success": True,
                "mappings": mappings,
                "stats": {
                    "template_columns": len([col for col in template_columns if col and col != "*Buisness Unit Name"]),
                    "raw_columns": len(raw_columns),
                    "mapped_columns": len([m for m in mappings if m["raw_column"] != "Not Mapped"])
                }
            }
            
        except Exception as e:
            # Cleanup temp files on error
            self.file_processor.cleanup_temp_files(*temp_files)
            return {"success": False, "error": str(e)}
