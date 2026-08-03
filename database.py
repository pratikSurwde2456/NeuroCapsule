from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy import JSON

db = SQLAlchemy()

class Patient(db.Model):
    """Patient model"""
    __tablename__ = 'patients'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=True)  # For authentication
    age = db.Column(db.Integer, nullable=True)
    gender = db.Column(db.Enum('M', 'F', 'Other'), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    role = db.Column(db.Enum('patient', 'doctor'), default='patient')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    scans = db.relationship('MRIScan', backref='patient', lazy=True, cascade='all, delete-orphan')
    predictions = db.relationship('Prediction', backref='patient', lazy=True, cascade='all, delete-orphan')
    memory_items = db.relationship('MemoryVaultItem', backref='patient', lazy=True, cascade='all, delete-orphan')
    alerts = db.relationship('Alert', backref='patient', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'age': self.age,
            'gender': self.gender,
            'phone': self.phone,
            'role': self.role,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class MRIScan(db.Model):
    """MRI Scan model"""
    __tablename__ = 'mri_scans'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_name = db.Column(db.String(255), nullable=False)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    file_size = db.Column(db.BigInteger, nullable=True)
    file_type = db.Column(db.String(50), nullable=True)
    
    # Relationships
    predictions = db.relationship('Prediction', backref='scan', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'patient_id': self.patient_id,
            'file_path': self.file_path,
            'file_name': self.file_name,
            'upload_date': self.upload_date.isoformat() if self.upload_date else None,
            'file_size': self.file_size,
            'file_type': self.file_type
        }


class Prediction(db.Model):
    """Prediction model"""
    __tablename__ = 'predictions'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    scan_id = db.Column(db.Integer, db.ForeignKey('mri_scans.id'), nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    risk_level = db.Column(db.Enum('Low', 'Medium', 'High'), nullable=False)
    risk_score = db.Column(db.Float, nullable=False)
    predicted_class = db.Column(db.Enum('Normal', 'MCI', 'Alzheimer'), nullable=False)
    confidence = db.Column(db.Float, nullable=False)
    model_version = db.Column(db.String(50), default='v1.0')
    prediction_date = db.Column(db.DateTime, default=datetime.utcnow)
    features_json = db.Column(JSON, nullable=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'scan_id': self.scan_id,
            'patient_id': self.patient_id,
            'riskLevel': self.risk_level,
            'score': self.risk_score,
            'class': self.predicted_class,
            'confidence': self.confidence,
            'model_version': self.model_version,
            'date': self.prediction_date.isoformat() if self.prediction_date else None,
            'features': self.features_json
        }


class MemoryVaultItem(db.Model):
    """Memory Vault Item model"""
    __tablename__ = 'memory_vault_items'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    item_type = db.Column(db.Enum('reminder', 'note', 'photo', 'voice'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=True)
    file_path = db.Column(db.String(500), nullable=True)
    reminder_date = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'patient_id': self.patient_id,
            'type': self.item_type,
            'title': self.title,
            'content': self.content,
            'file_path': self.file_path,
            'reminder_date': self.reminder_date.isoformat() if self.reminder_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }



class Alert(db.Model):
    """Alert / Notification model"""
    __tablename__ = 'alerts'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    alert_type = db.Column(db.String(50), nullable=False, default='custom')  # risk_alert, medication, appointment, custom
    priority = db.Column(db.String(20), nullable=False, default='medium')  # low, medium, high, critical
    title = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    is_dismissed = db.Column(db.Boolean, default=False)
    scheduled_time = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'patient_id': self.patient_id,
            'alert_type': self.alert_type,
            'priority': self.priority,
            'title': self.title,
            'message': self.message,
            'is_read': self.is_read,
            'is_dismissed': self.is_dismissed,
            'scheduled_time': self.scheduled_time.isoformat() if self.scheduled_time else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


def init_db(app):
    """Initialize database"""
    db.init_app(app)
    with app.app_context():
        db.create_all()
        print("Database tables created successfully!")


def test_connection():
    """Test database connection"""
    try:
        db.session.execute(db.text('SELECT 1'))
        print("Database connection successful!")
        return True
    except Exception as e:
        print(f"Database connection failed: {e}")
        return False
