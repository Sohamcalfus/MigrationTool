import pandas as pd
from backend.models1 import ColumnMapping

class MappingManager:
    """Utility class for managing column mappings"""
    
    @staticmethod
    def get_latest_mappings():
        """Get the latest active column mappings from database"""
        try:
            mappings = ColumnMapping.query.filter(ColumnMapping.status == 'Y')\
                .order_by(ColumnMapping.created_at.desc()).all()
            return {m.template_column: m.raw_column for m in mappings}
        except Exception as e:
            print(f"Error getting mappings: {e}")
            return {}
    
    @staticmethod
    def create_mapping_preview(template_columns, raw_columns, stored_mappings):
        """Create mapping preview for frontend display"""
        mappings = []
        
        for template_col in template_columns:
            if pd.isna(template_col) or template_col == "":
                continue
            if template_col == "*Buisness Unit Name":
                continue
                
            mapped_raw_col = None
            
            # Special handling for Comments column
            if template_col == "Comments" and "*Buisness Unit Name" in raw_columns:
                mapped_raw_col = "*Buisness Unit Name"
            elif template_col in stored_mappings:
                mapped_raw_col = stored_mappings[template_col]
            
            mappings.append({
                "template_column": template_col,
                "raw_column": mapped_raw_col or "Not Mapped"
            })
        
        return mappings
    
    @staticmethod
    def apply_mappings(template_df, raw_data, template_columns, raw_columns, stored_mappings, start_row=4):
        """Apply column mappings to template dataframe"""
        from utils.date_formatter import DateFormatter
        
        has_bu_col = "*Buisness Unit Name" in raw_columns
        num_rows = raw_data.shape[0]
        
        for col_idx, template_col in enumerate(template_columns):
            if pd.isna(template_col) or template_col == "" or template_col == "*Buisness Unit Name":
                continue
            
            # Special handling for Comments column
            if template_col == "Comments" and has_bu_col:
                raw_idx = raw_columns.index("*Buisness Unit Name")
                template_df.iloc[start_row:start_row + num_rows, col_idx] = raw_data.iloc[:, raw_idx].values
                continue
            
            # Apply stored mappings
            if template_col in stored_mappings:
                raw_col_name = stored_mappings[template_col]
                if raw_col_name in raw_columns:
                    raw_idx = raw_columns.index(raw_col_name)
                    data = raw_data.iloc[:, raw_idx]
                    
                    # Apply date formatting if needed
                    if DateFormatter.is_date_column(template_col) or DateFormatter.is_date_column(raw_col_name):
                        print(f"Formatting dates for column: {template_col}")
                        data = DateFormatter.format_date_for_column(data, template_col)
                    
                    template_df.iloc[start_row:start_row + num_rows, col_idx] = data.values
        
        return template_df
