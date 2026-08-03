"""Quick diagnostic to check database state"""
from app import app, db
from database import Patient, MRIScan, Prediction, MemoryVaultItem

with app.app_context():
    # Check patients
    patients = Patient.query.all()
    print(f"\n{'='*50}")
    print(f"PATIENTS ({len(patients)}):")
    for p in patients:
        print(f"  ID={p.id}, Name={p.name}, Email={p.email}, Role={p.role}")
    
    # Check predictions per patient
    print(f"\n{'='*50}")
    print("PREDICTIONS:")
    for p in patients:
        preds = Prediction.query.filter_by(patient_id=p.id).count()
        print(f"  Patient {p.id} ({p.name}): {preds} predictions")
    
    # Check vault items per patient
    print(f"\n{'='*50}")
    print("VAULT ITEMS:")
    for p in patients:
        items = MemoryVaultItem.query.filter_by(patient_id=p.id).count()
        print(f"  Patient {p.id} ({p.name}): {items} vault items")
    
    # Check alerts per patient
    print(f"\n{'='*50}")
    try:
        from database import Alert
        print("ALERTS:")
        for p in patients:
            alerts = Alert.query.filter_by(patient_id=p.id).count()
            print(f"  Patient {p.id} ({p.name}): {alerts} alerts")
    except Exception as e:
        print(f"Alerts table error: {e}")
    
    print(f"\n{'='*50}")
