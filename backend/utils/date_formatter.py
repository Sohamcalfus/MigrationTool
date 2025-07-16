import pandas as pd
from datetime import datetime

class DateFormatter:
    """Utility class for formatting dates in FBDI files"""
    
    DATE_FORMATS = [
        '%Y-%m-%d',
        '%Y/%m/%d', 
        '%m/%d/%Y',
        '%d/%m/%Y',
        '%m-%d-%Y',
        '%d-%m-%Y',
        '%Y-%m-%d %H:%M:%S',
        '%m/%d/%Y %H:%M:%S'
    ]
    
    DATE_KEYWORDS = ['date', 'Date', 'DATE', 'time', 'Time', 'TIME']
    
    @staticmethod
    def format_date_for_column(data_series, column_name):
        """Format a pandas series containing dates to YYYY/MM/DD format"""
        def format_single_date(date_value):
            if pd.isna(date_value) or date_value == "" or date_value is None:
                return date_value
            
            try:
                parsed_date = None
                
                # Handle different input types
                if isinstance(date_value, str):
                    # Try different string formats
                    for fmt in DateFormatter.DATE_FORMATS:
                        try:
                            parsed_date = datetime.strptime(date_value, fmt)
                            break
                        except ValueError:
                            continue
                    
                    # If no format matches, try pandas to_datetime
                    if parsed_date is None:
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
    
    @staticmethod
    def is_date_column(column_name):
        """Check if a column name suggests it contains date data"""
        return any(keyword in str(column_name) for keyword in DateFormatter.DATE_KEYWORDS)
