from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class ColumnMapping(db.Model):
    __tablename__ = 'column_mapping'
    
    id = db.Column(db.Integer, primary_key=True)
    fbdi_module = db.Column(db.String(100), nullable=False)
    fbdi_subset = db.Column(db.String(100), nullable=False)
    template_column = db.Column(db.String(100), nullable=False)
    raw_column = db.Column(db.String(100), nullable=True)  # Allow null for unmapped columns
    status = db.Column(db.String(1), nullable=False)  # 'Y' or 'N'
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())  # Track when mapping was created
    
    def __repr__(self):
        return f'<ColumnMapping {self.template_column} -> {self.raw_column}>'




