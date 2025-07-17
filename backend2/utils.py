import pandas as pd
from datetime import datetime
from models import ColumnMapping

def format_date_for_column(data_series, column_name):
    def format_single_date(date_value):
        if pd.isna(date_value) or date_value == "" or date_value is None:
            return date_value
        try:
            # Handle different input types
            if isinstance(date_value, str):
                # Try different string formats
                for fmt in ['%Y-%m-%d', '%Y/%m/%d', '%m/%d/%Y', '%d/%m/%Y', '%m-%d-%Y', '%d-%m-%Y', '%Y-%m-%d %H:%M:%S']:
                    try:
                        parsed_date = datetime.strptime(date_value, fmt)
                        break
                    except ValueError:
                        continue
                else:
                    # If no format matches, try pandas to_datetime
                    try:
                        parsed_date = pd.to_datetime(date_value)
                    except:
                        return date_value
            elif isinstance(date_value, (datetime, pd.Timestamp)):
                parsed_date = date_value
            else:
                # Try to convert using pandas
                try:
                    parsed_date = pd.to_datetime(date_value)
                except:
                    return date_value
            
            # Always format as YYYY/MM/DD (date only, no time)
            return parsed_date.strftime('%Y/%m/%d')
            
        except Exception as e:
            print(f"Error formatting date {date_value}: {e}")
            return date_value
    
    return data_series.apply(format_single_date)

def is_date_column(column_name):
    """Check if a column name suggests it contains date data"""
    date_keywords = ['date', 'Date', 'DATE', 'time', 'Time', 'TIME']
    return any(keyword in str(column_name) for keyword in date_keywords)

def get_latest_mappings():
    try:
        mappings = ColumnMapping.query.filter(ColumnMapping.status == 'Y')\
            .order_by(ColumnMapping.created_at.desc()).all()
        mapping_dict = {m.template_column: m.raw_column for m in mappings}
        return mapping_dict
    except Exception as e:
        print(f"Error getting mappings: {e}")
        return {}
