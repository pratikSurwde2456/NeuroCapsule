# Neurocapsule - Alzheimer's Prediction System

🧠 **AI-Powered MRI-Based Alzheimer's Risk Prediction System**

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install Flask Flask-SQLAlchemy python-dotenv PyMySQL cryptography tensorflow scikit-learn xgboost numpy pandas Pillow
```

### 2. Initialize Database
```bash
python init_db.py
```

### 3. Train Model (Optional - already trained)
```bash
python train_model.py
```

### 4. Run Application
```bash
python app.py
```

### 5. Access Application
Open browser: `http://localhost:5000`

## 📊 System Overview

- **ML Model**: MobileNetV2 + Random Forest (75.34% accuracy)
- **Database**: MySQL with 4 tables (patients, mri_scans, predictions, memory_vault_items)
- **Backend**: Flask REST API with 10+ endpoints
- **Frontend**: Beautiful Tailwind CSS UI
- **Features**: MRI analysis, Memory vault, Trend analysis

## 🎯 Features

✅ Real-time MRI scan analysis  
✅ 4-class classification (NonDemented, VeryMildDemented, MildDemented, ModerateDemented)  
✅ Risk level assessment (Low, Medium, High)  
✅ Historical prediction tracking  
✅ Trend visualization  
✅ Digital memory vault (reminders, notes, photos, voice)  
✅ Patient management system  

## 📁 Project Structure

```
Neurocapsule/
├── app.py              # Main Flask application
├── config.py           # Configuration
├── database.py         # Database models
├── ml_model.py         # ML model
├── train_model.py      # Training script
├── init_db.py          # DB initialization
├── requirements.txt    # Dependencies
├── .env                # Environment variables
├── models/             # Trained models
├── dataset/            # Training data
├── uploads/            # User uploads
└── templates/          # HTML templates
```

## 🔧 Configuration

Edit `.env` file:
```env
DB_HOST=localhost
DB_PORT=3306
DB_NAME=alzheimer_ai
DB_USER=root
DB_PASSWORD=your_password
```

## 📈 Model Performance

- **Accuracy**: 75.34%
- **Classes**: 4 (NonDemented, VeryMildDemented, MildDemented, ModerateDemented)
- **Architecture**: MobileNetV2 (feature extraction) + Random Forest (classification)

## 🎓 Usage

1. **Login** as Patient or Doctor
2. **Upload** MRI scan (DICOM, PNG, JPG)
3. **View** prediction results with risk level and confidence
4. **Track** trends over time
5. **Use** memory vault for reminders and notes

## 🛠️ Tech Stack

- **Backend**: Flask, SQLAlchemy
- **Database**: MySQL
- **ML**: TensorFlow, scikit-learn, XGBoost
- **Frontend**: HTML, Tailwind CSS, JavaScript

## 📝 API Endpoints

- `POST /login` - Authentication
- `POST /upload` - Upload MRI and get prediction
- `GET /api/predictions` - Get all predictions
- `GET /api/trends` - Get trend analysis
- `GET/POST /api/memory-vault` - Memory vault CRUD
- `GET/POST /api/alerts` - Alerts & notifications CRUD
- `PUT/DELETE /api/alerts/<id>` - Update/delete alert
- `POST /api/alerts/mark-all-read` - Mark all read

## ⚡ Performance

- Model training: ~5 minutes (364 samples)
- Prediction time: ~2 seconds per image
- Database queries: <100ms

## 🔮 Future Enhancements

- Train on full dataset (6400 images) for better accuracy
- Add PDF report generation
- Implement data augmentation
- Deploy to production with Gunicorn/Nginx

## 📄 License

MIT License

## 👨‍💻 Author

Built with ❤️ using AI-powered development

---

**Status**: ✅ Fully Operational  
**Version**: 1.0.0  
**Last Updated**: January 22, 2026
