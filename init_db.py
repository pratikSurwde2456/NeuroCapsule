from flask import Flask
from database import db, init_db, Patient, MRIScan, Prediction, MemoryVaultItem
from config import Config
import os

def create_database():
    """Create database and tables"""
    app = Flask(__name__)
    
    # Configure app
    app.config['SQLALCHEMY_DATABASE_URI'] = Config.SQLALCHEMY_DATABASE_URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize database
    db.init_app(app)
    
    with app.app_context():
        # Create all tables
        print("Creating database tables...")
        db.create_all()
        print("✓ Tables created successfully!")
        
        # Create sample patient for testing
        existing_patient = Patient.query.filter_by(email='john.doe@example.com').first()
        if not existing_patient:
            sample_patient = Patient(
                name='John Doe',
                email='john.doe@example.com',
                age=65,
                gender='M',
                phone='+1234567890'
            )
            db.session.add(sample_patient)
            
            # Create sample doctor patient
            sample_doctor = Patient(
                name='Dr. Smith',
                email='dr.smith@hospital.com',
                age=45,
                gender='M',
                phone='+0987654321'
            )
            db.session.add(sample_doctor)
            
            db.session.commit()
            print("✓ Sample patients created!")
        else:
            print("✓ Sample data already exists!")
        
        # Verify tables
        print("\nVerifying database structure...")
        tables = db.metadata.tables.keys()
        print(f"Tables created: {', '.join(tables)}")
        
        # Test query
        patient_count = Patient.query.count()
        print(f"Total patients: {patient_count}")
        
        print("\n" + "=" * 60)
        print("DATABASE INITIALIZATION COMPLETED SUCCESSFULLY!")
        print("=" * 60)


if __name__ == '__main__':
    # Create uploads directories
    os.makedirs('uploads/mri_scans', exist_ok=True)
    os.makedirs('uploads/memory_vault/photos', exist_ok=True)
    os.makedirs('uploads/memory_vault/voice', exist_ok=True)
    os.makedirs('models', exist_ok=True)
    
    # Create database
    create_database()
