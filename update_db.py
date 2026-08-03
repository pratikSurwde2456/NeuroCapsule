from flask import Flask
from database import db
from config import Config
import bcrypt

def update_database():
    """Update database schema to add password_hash and role columns"""
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = Config.SQLALCHEMY_DATABASE_URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    
    with app.app_context():
        # Add columns using raw SQL
        try:
            # Add password_hash column if it doesn't exist
            db.session.execute(db.text(
                "ALTER TABLE patients ADD COLUMN password_hash VARCHAR(255) NULL"
            ))
            print("✓ Added password_hash column")
        except Exception as e:
            if "Duplicate column name" in str(e):
                print("✓ password_hash column already exists")
            else:
                print(f"Error adding password_hash: {e}")
        
        try:
            # Add role column if it doesn't exist
            db.session.execute(db.text(
                "ALTER TABLE patients ADD COLUMN role ENUM('patient', 'doctor') DEFAULT 'patient'"
            ))
            print("✓ Added role column")
        except Exception as e:
            if "Duplicate column name" in str(e):
                print("✓ role column already exists")
            else:
                print(f"Error adding role: {e}")
        
        try:
            # Make email NOT NULL if needed
            db.session.execute(db.text(
                "ALTER TABLE patients MODIFY COLUMN email VARCHAR(255) NOT NULL"
            ))
            print("✓ Updated email column to NOT NULL")
        except Exception as e:
            print(f"Email column update: {e}")
        
        db.session.commit()
        print("\n" + "="*60)
        print("DATABASE SCHEMA UPDATE COMPLETED!")
        print("="*60)

if __name__ == '__main__':
    update_database()
