from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename
import os
from datetime import datetime
import bcrypt
from config import Config
from database import db, Patient, MRIScan, Prediction, MemoryVaultItem, Alert
from ml_model import predict_image, load_model
from sqlalchemy import func

app = Flask(__name__)

# Load configuration
app.config.from_object(Config)
app.config['SQLALCHEMY_DATABASE_URI'] = Config.SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = Config.SECRET_KEY

# Initialize database
db.init_app(app)

# Create upload directories
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'mri_scans'), exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'memory_vault', 'photos'), exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'memory_vault', 'voice'), exist_ok=True)

# Load ML model
print("Loading ML model...")
load_model()
print("ML model loaded successfully!")

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

def get_current_patient():
    """Get current patient from session"""
    if 'user' not in session:
        return None
    
    user_id = session['user'].get('id')
    patient = Patient.query.get(user_id)
    
    # Create patient if doesn't exist
    if not patient:
        patient = Patient(
            id=user_id,
            name=session['user'].get('name', 'Unknown'),
            email=f"user{user_id}@example.com"
        )
        db.session.add(patient)
        db.session.commit()
    
    return patient

@app.route('/')
def index():
    if 'user' not in session:
        return render_template('login.html')
    return render_template('dashboard.html')

@app.route('/register', methods=['GET'])
def register_page():
    return render_template('register.html')

@app.route('/register', methods=['POST'])
def register():
    try:
        data = request.json
        name = data.get('name')
        email = data.get('email')
        password = data.get('password')
        role = data.get('role', 'patient')
        age = data.get('age')
        gender = data.get('gender')
        
        # Validate required fields
        if not name or not email or not password:
            return jsonify({'error': 'Name, email, and password are required'}), 400
        
        # Check if email already exists
        existing_patient = Patient.query.filter_by(email=email).first()
        if existing_patient:
            return jsonify({'error': 'Email already registered'}), 400
        
        # Hash password
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Create new patient
        new_patient = Patient(
            name=name,
            email=email,
            password_hash=password_hash,
            role=role,
            age=age,
            gender=gender
        )
        
        db.session.add(new_patient)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Registration successful'})
        
    except Exception as e:
        print(f"Registration error: {e}")
        db.session.rollback()
        return jsonify({'error': 'Registration failed. Please try again.'}), 500

@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.json
        email = data.get('email')
        password = data.get('password')
        
        # Validate input
        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400
        
        # Find patient by email
        patient = Patient.query.filter_by(email=email).first()
        
        if not patient:
            return jsonify({'error': 'Invalid email or password'}), 401
        
        # Check if password_hash exists (for backward compatibility)
        if not patient.password_hash:
            return jsonify({'error': 'Please register with a password first'}), 401
        
        # Verify password
        if not bcrypt.checkpw(password.encode('utf-8'), patient.password_hash.encode('utf-8')):
            return jsonify({'error': 'Invalid email or password'}), 401
        
        # Create session
        session['user'] = {
            'role': patient.role or 'patient',
            'name': patient.name,
            'id': patient.id,
            'email': patient.email
        }
        
        return jsonify({'success': True})
        
    except Exception as e:
        print(f"Login error: {e}")
        return jsonify({'error': 'Login failed. Please try again.'}), 500

@app.route('/logout', methods=['POST'])
def logout():
    session.pop('user', None)
    return jsonify({'success': True})

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'user' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file and allowed_file(file.filename):
        try:
            # Get current patient
            patient = get_current_patient()
            if not patient:
                return jsonify({'error': 'Patient not found'}), 404
            
            # Save file
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{timestamp}_{filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'mri_scans', filename)
            file.save(filepath)
            
            # Save scan to database
            mri_scan = MRIScan(
                patient_id=patient.id,
                file_path=filepath,
                file_name=filename,
                file_size=os.path.getsize(filepath),
                file_type=filename.rsplit('.', 1)[1].lower()
            )
            db.session.add(mri_scan)
            db.session.commit()
            
            # Make prediction using ML model
            print(f"Making prediction for {filepath}...")
            prediction_result = predict_image(filepath)
            
            if prediction_result is None:
                return jsonify({'error': 'Prediction failed'}), 500
            
            # Save prediction to database
            prediction = Prediction(
                scan_id=mri_scan.id,
                patient_id=patient.id,
                risk_level=prediction_result['risk_level'],
                risk_score=prediction_result['risk_score'],
                predicted_class=prediction_result['label'],
                confidence=prediction_result['confidence'],
                model_version='v1.0',
                features_json={'features': prediction_result['features']}
            )
            db.session.add(prediction)
            db.session.commit()
            
            # Auto-create a risk alert based on the prediction (non-critical)
            try:
                alert_priority = 'low'
                if prediction_result['risk_level'] == 'High':
                    alert_priority = 'critical'
                elif prediction_result['risk_level'] == 'Medium':
                    alert_priority = 'high'
                
                risk_alert = Alert(
                    patient_id=patient.id,
                    alert_type='risk_alert',
                    priority=alert_priority,
                    title=f"{prediction_result['risk_level']} Risk Assessment Alert",
                    message=f"Your latest MRI scan shows {prediction_result['risk_level'].lower()} risk indicators "
                            f"(Score: {prediction_result['risk_score']}%, Class: {prediction_result['label']}). "
                            f"{'Immediate consultation with a specialist is recommended.' if prediction_result['risk_level'] == 'High' else 'Consider scheduling a follow-up consultation.' if prediction_result['risk_level'] == 'Medium' else 'Continue routine check-ups.'}"
                )
                db.session.add(risk_alert)
                db.session.commit()
            except Exception as alert_err:
                print(f"Warning: Could not create risk alert: {alert_err}")
                db.session.rollback()
            
            # Format response
            response_data = {
                'id': prediction.id,
                'date': prediction.prediction_date.isoformat(),
                'riskLevel': prediction.risk_level,
                'score': prediction.risk_score,
                'class': prediction.predicted_class,
                'confidence': prediction.confidence,
                'fileName': filename
            }
            
            return jsonify({'success': True, 'prediction': response_data})
            
        except Exception as e:
            print(f"Error processing upload: {e}")
            db.session.rollback()
            return jsonify({'error': str(e)}), 500
    
    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/api/predictions')
def get_predictions():
    if 'user' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        patient = get_current_patient()
        if not patient:
            return jsonify({'predictions': []})
        
        # Get predictions from database
        predictions = Prediction.query.filter_by(patient_id=patient.id)\
            .order_by(Prediction.prediction_date.desc())\
            .limit(50)\
            .all()
        
        predictions_data = [pred.to_dict() for pred in predictions]
        
        return jsonify({'predictions': predictions_data})
        
    except Exception as e:
        print(f"Error fetching predictions: {e}")
        return jsonify({'predictions': []})

@app.route('/api/trends')
def get_trends():
    if 'user' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        patient = get_current_patient()
        if not patient:
            return jsonify({'trendData': [], 'classDistribution': []})
        
        # Get trend data from database (last 6 months)
        predictions = Prediction.query.filter_by(patient_id=patient.id)\
            .order_by(Prediction.prediction_date.asc())\
            .all()
        
        # Calculate monthly averages
        monthly_data = {}
        for pred in predictions:
            month = pred.prediction_date.strftime('%b')
            if month not in monthly_data:
                monthly_data[month] = []
            monthly_data[month].append(pred.risk_score)
        
        trend_data = [
            {'month': month, 'score': sum(scores) / len(scores)}
            for month, scores in monthly_data.items()
        ]
        
        # Get class distribution
        class_counts = db.session.query(
            Prediction.predicted_class,
            func.count(Prediction.id)
        ).filter_by(patient_id=patient.id)\
         .group_by(Prediction.predicted_class)\
         .all()
        
        class_colors = {
            'Normal': '#10b981',
            'MCI': '#f59e0b',
            'Alzheimer': '#ef4444'
        }
        
        class_distribution = [
            {
                'name': class_name,
                'value': count,
                'color': class_colors.get(class_name, '#6b7280')
            }
            for class_name, count in class_counts
        ]
        
        return jsonify({
            'trendData': trend_data,
            'classDistribution': class_distribution
        })
        
    except Exception as e:
        print(f"Error fetching trends: {e}")
        return jsonify({'trendData': [], 'classDistribution': []})

# Memory Vault APIs
@app.route('/api/memory-vault', methods=['GET', 'POST'])
def memory_vault():
    if 'user' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    patient = get_current_patient()
    if not patient:
        return jsonify({'error': 'Patient not found'}), 404
    
    if request.method == 'GET':
        # Get all memory vault items
        items = MemoryVaultItem.query.filter_by(patient_id=patient.id)\
            .order_by(MemoryVaultItem.created_at.desc())\
            .all()
        return jsonify({'items': [item.to_dict() for item in items]})
    
    elif request.method == 'POST':
        # Create new memory vault item
        data = request.json
        
        item = MemoryVaultItem(
            patient_id=patient.id,
            item_type=data.get('type'),
            title=data.get('title'),
            content=data.get('content'),
            reminder_date=datetime.fromisoformat(data['reminder_date']) if data.get('reminder_date') else None
        )
        
        db.session.add(item)
        db.session.commit()
        
        return jsonify({'success': True, 'item': item.to_dict()})

@app.route('/api/memory-vault/<int:item_id>', methods=['GET', 'PUT', 'DELETE'])
def memory_vault_item(item_id):
    if 'user' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    patient = get_current_patient()
    if not patient:
        return jsonify({'error': 'Patient not found'}), 404
    item = MemoryVaultItem.query.filter_by(id=item_id, patient_id=patient.id).first()
    
    if not item:
        return jsonify({'error': 'Item not found'}), 404
    
    if request.method == 'GET':
        return jsonify({'item': item.to_dict()})
    
    elif request.method == 'PUT':
        data = request.json
        item.title = data.get('title', item.title)
        item.content = data.get('content', item.content)
        if data.get('reminder_date'):
            item.reminder_date = datetime.fromisoformat(data['reminder_date'])
        
        db.session.commit()
        return jsonify({'success': True, 'item': item.to_dict()})
    
    elif request.method == 'DELETE':
        db.session.delete(item)
        db.session.commit()
        return jsonify({'success': True})

@app.route('/api/memory-vault/upload', methods=['POST'])
def upload_memory_file():
    if 'user' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    item_type = request.form.get('type', 'photo')
    title = request.form.get('title', 'Untitled')
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    patient = get_current_patient()
    if not patient:
        return jsonify({'error': 'Patient not found'}), 404
    
    # Save file
    filename = secure_filename(file.filename)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{timestamp}_{filename}"
    
    subfolder = 'photos' if item_type == 'photo' else 'voice'
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'memory_vault', subfolder, filename)
    file.save(filepath)
    
    # Create memory vault item
    item = MemoryVaultItem(
        patient_id=patient.id,
        item_type=item_type,
        title=title,
        file_path=filepath
    )
    
    db.session.add(item)
    db.session.commit()
    
    return jsonify({'success': True, 'item': item.to_dict()})

# Delete vault items by type
@app.route('/api/memory-vault/clear-type/<item_type>', methods=['DELETE'])
def clear_vault_by_type(item_type):
    if 'user' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        patient = get_current_patient()
        if not patient:
            return jsonify({'error': 'Patient not found'}), 404
        
        # Map frontend type names to database types
        type_map = {'note': ['note', 'reminder'], 'photo': ['photo'], 'voice': ['voice']}
        db_types = type_map.get(item_type, [item_type])
        
        items = MemoryVaultItem.query.filter(
            MemoryVaultItem.patient_id == patient.id,
            MemoryVaultItem.item_type.in_(db_types)
        ).all()
        
        # Delete files from disk
        for item in items:
            if item.file_path and os.path.exists(item.file_path):
                try:
                    os.remove(item.file_path)
                except Exception:
                    pass
            db.session.delete(item)
        
        db.session.commit()
        return jsonify({'success': True, 'deleted': len(items)})
    except Exception as e:
        print(f"Error clearing vault items: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to clear items'}), 500

# Delete all vault items
@app.route('/api/memory-vault/clear-all', methods=['DELETE'])
def clear_all_vault():
    if 'user' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        patient = get_current_patient()
        if not patient:
            return jsonify({'error': 'Patient not found'}), 404
        
        items = MemoryVaultItem.query.filter_by(patient_id=patient.id).all()
        
        # Delete files from disk
        for item in items:
            if item.file_path and os.path.exists(item.file_path):
                try:
                    os.remove(item.file_path)
                except Exception:
                    pass
            db.session.delete(item)
        
        db.session.commit()
        return jsonify({'success': True, 'deleted': len(items)})
    except Exception as e:
        print(f"Error clearing all vault items: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to clear vault'}), 500

# Serve uploaded files (vault photos, voice recordings, MRI scans)
@app.route('/uploads/<path:filename>')
def serve_upload(filename):
    if 'user' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Dashboard stats API
@app.route('/api/dashboard')
def get_dashboard_stats():
    if 'user' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        patient = get_current_patient()
        if not patient:
            return jsonify({'totalScans': 0, 'latestScore': 0, 'riskLevel': 'N/A'})
        
        total_scans = Prediction.query.filter_by(patient_id=patient.id).count()
        latest = Prediction.query.filter_by(patient_id=patient.id)\
            .order_by(Prediction.prediction_date.desc()).first()
        
        return jsonify({
            'totalScans': total_scans,
            'latestScore': latest.risk_score if latest else 0,
            'riskLevel': latest.risk_level if latest else 'N/A'
        })
    except Exception as e:
        print(f"Error fetching dashboard stats: {e}")
        return jsonify({'totalScans': 0, 'latestScore': 0, 'riskLevel': 'N/A'})

# ═══════════════ ALERTS API ═══════════════

@app.route('/api/alerts', methods=['GET'])
def get_alerts():
    if 'user' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        patient = get_current_patient()
        if not patient:
            return jsonify({'alerts': [], 'unread_count': 0})
        
        show_dismissed = request.args.get('show_dismissed', 'false') == 'true'
        
        query = Alert.query.filter_by(patient_id=patient.id)
        if not show_dismissed:
            query = query.filter_by(is_dismissed=False)
        
        alerts = query.order_by(Alert.created_at.desc()).limit(50).all()
        unread_count = Alert.query.filter_by(patient_id=patient.id, is_read=False, is_dismissed=False).count()
        
        return jsonify({
            'alerts': [a.to_dict() for a in alerts],
            'unread_count': unread_count
        })
    except Exception as e:
        print(f"Error fetching alerts: {e}")
        return jsonify({'alerts': [], 'unread_count': 0})


@app.route('/api/alerts', methods=['POST'])
def create_alert():
    if 'user' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        patient = get_current_patient()
        if not patient:
            return jsonify({'error': 'Patient not found'}), 404
        
        data = request.json
        title = data.get('title', '').strip()
        message = data.get('message', '').strip()
        alert_type = data.get('alert_type', 'custom')
        priority = data.get('priority', 'medium')
        scheduled_time = data.get('scheduled_time')
        
        if not title or not message:
            return jsonify({'error': 'Title and message are required'}), 400
        
        alert = Alert(
            patient_id=patient.id,
            alert_type=alert_type,
            priority=priority,
            title=title,
            message=message,
            scheduled_time=datetime.fromisoformat(scheduled_time) if scheduled_time else None
        )
        
        db.session.add(alert)
        db.session.commit()
        
        return jsonify({'success': True, 'alert': alert.to_dict()})
    except Exception as e:
        print(f"Error creating alert: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to create alert'}), 500


@app.route('/api/alerts/<int:alert_id>', methods=['PUT'])
def update_alert(alert_id):
    if 'user' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        patient = get_current_patient()
        if not patient:
            return jsonify({'error': 'Patient not found'}), 404
        
        alert = Alert.query.filter_by(id=alert_id, patient_id=patient.id).first()
        if not alert:
            return jsonify({'error': 'Alert not found'}), 404
        
        data = request.json
        if 'is_read' in data:
            alert.is_read = data['is_read']
        if 'is_dismissed' in data:
            alert.is_dismissed = data['is_dismissed']
        
        db.session.commit()
        return jsonify({'success': True, 'alert': alert.to_dict()})
    except Exception as e:
        print(f"Error updating alert: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to update alert'}), 500


@app.route('/api/alerts/<int:alert_id>', methods=['DELETE'])
def delete_alert(alert_id):
    if 'user' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        patient = get_current_patient()
        if not patient:
            return jsonify({'error': 'Patient not found'}), 404
        
        alert = Alert.query.filter_by(id=alert_id, patient_id=patient.id).first()
        if not alert:
            return jsonify({'error': 'Alert not found'}), 404
        
        db.session.delete(alert)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        print(f"Error deleting alert: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to delete alert'}), 500


@app.route('/api/alerts/mark-all-read', methods=['POST'])
def mark_all_alerts_read():
    if 'user' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        patient = get_current_patient()
        if not patient:
            return jsonify({'error': 'Patient not found'}), 404
        
        Alert.query.filter_by(patient_id=patient.id, is_read=False).update({'is_read': True})
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        print(f"Error marking alerts read: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to mark alerts as read'}), 500


# Current user info API
@app.route('/api/user')
def get_user_info():
    if 'user' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    return jsonify(session['user'])

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
