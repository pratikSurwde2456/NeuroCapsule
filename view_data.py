from flask import Flask
from database import db, Patient, MRIScan, Prediction, MemoryVaultItem
from config import Config
from tabulate import tabulate

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = Config.SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

def view_all_data():
    """View all data in the database"""
    with app.app_context():
        print("\n" + "="*80)
        print("ALZHEIMER'S PREDICTION SYSTEM - DATABASE VIEWER")
        print("="*80)
        
        # View Patients
        print("\n📋 PATIENTS")
        print("-" * 80)
        patients = Patient.query.all()
        if patients:
            patient_data = [[p.id, p.name, p.email, p.age, p.gender, p.phone] 
                           for p in patients]
            print(tabulate(patient_data, 
                          headers=['ID', 'Name', 'Email', 'Age', 'Gender', 'Phone'],
                          tablefmt='grid'))
        else:
            print("No patients found.")
        
        # View MRI Scans
        print("\n🔬 MRI SCANS")
        print("-" * 80)
        scans = MRIScan.query.all()
        if scans:
            scan_data = [[s.id, s.patient_id, s.file_name, s.file_type, 
                         s.upload_date.strftime('%Y-%m-%d %H:%M')] 
                        for s in scans]
            print(tabulate(scan_data, 
                          headers=['ID', 'Patient ID', 'File Name', 'Type', 'Upload Date'],
                          tablefmt='grid'))
        else:
            print("No MRI scans found.")
        
        # View Predictions
        print("\n🧠 PREDICTIONS")
        print("-" * 80)
        predictions = Prediction.query.all()
        if predictions:
            pred_data = [[pr.id, pr.patient_id, pr.risk_level, pr.risk_score, 
                         pr.predicted_class, f"{pr.confidence}%",
                         pr.prediction_date.strftime('%Y-%m-%d %H:%M')] 
                        for pr in predictions]
            print(tabulate(pred_data, 
                          headers=['ID', 'Patient', 'Risk Level', 'Score', 'Class', 'Confidence', 'Date'],
                          tablefmt='grid'))
        else:
            print("No predictions found.")
        
        # View Memory Vault Items
        print("\n💾 MEMORY VAULT ITEMS")
        print("-" * 80)
        items = MemoryVaultItem.query.all()
        if items:
            item_data = [[i.id, i.patient_id, i.item_type, i.title, 
                         i.created_at.strftime('%Y-%m-%d %H:%M')] 
                        for i in items]
            print(tabulate(item_data, 
                          headers=['ID', 'Patient', 'Type', 'Title', 'Created'],
                          tablefmt='grid'))
        else:
            print("No memory vault items found.")
        
        # Summary Statistics
        print("\n📊 SUMMARY STATISTICS")
        print("-" * 80)
        stats = [
            ['Total Patients', Patient.query.count()],
            ['Total MRI Scans', MRIScan.query.count()],
            ['Total Predictions', Prediction.query.count()],
            ['Total Memory Items', MemoryVaultItem.query.count()],
        ]
        print(tabulate(stats, headers=['Metric', 'Count'], tablefmt='grid'))
        
        print("\n" + "="*80)

if __name__ == '__main__':
    view_all_data()
