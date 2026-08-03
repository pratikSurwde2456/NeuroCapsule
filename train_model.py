import os
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
import joblib
from ml_model import AlzheimerPredictor
from config import Config
import json

def load_dataset():
    """Load dataset from directory structure"""
    config = Config()
    dataset_path = config.DATASET_PATH
    
    X_features = []
    y_labels = []
    
    predictor = AlzheimerPredictor()
    predictor.build_feature_extractor()
    
    print("Loading dataset and extracting features...")
    
    for class_idx, class_name in enumerate(config.CLASS_NAMES):
        class_dir = os.path.join(dataset_path, class_name)
        
        if not os.path.exists(class_dir):
            print(f"Warning: Directory {class_dir} not found!")
            continue
        
        image_files = [f for f in os.listdir(class_dir) if f.endswith(('.jpg', '.jpeg', '.png'))]
        
        print(f"Processing {len(image_files)} images from {class_name}...")
        
        for img_file in image_files[:100]:  # Limit to 100 images per class for faster training
            img_path = os.path.join(class_dir, img_file)
            
            try:
                features = predictor.extract_features(img_path)
                if features is not None:
                    X_features.append(features)
                    y_labels.append(class_idx)
            except Exception as e:
                print(f"Error processing {img_file}: {e}")
                continue
    
    X = np.array(X_features)
    y = np.array(y_labels)
    
    print(f"\nDataset loaded: {len(X)} samples")
    print(f"Feature shape: {X.shape}")
    print(f"Class distribution: {np.bincount(y)}")
    
    return X, y


def train_model():
    """Train the ensemble classifier"""
    config = Config()
    
    # Load dataset
    print("=" * 60)
    print("TRAINING ALZHEIMER'S PREDICTION MODEL")
    print("=" * 60)
    
    X, y = load_dataset()
    
    if len(X) == 0:
        print("Error: No data loaded!")
        return False
    
    # Split dataset
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    print(f"\nTrain set: {len(X_train)} samples")
    print(f"Test set: {len(X_test)} samples")
    
    # Scale features
    print("\nScaling features...")
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Train Random Forest classifier
    print("\nTraining Random Forest classifier...")
    classifier = RandomForestClassifier(
        n_estimators=100,
        max_depth=20,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1,
        verbose=1
    )
    
    classifier.fit(X_train_scaled, y_train)
    
    # Evaluate
    print("\nEvaluating model...")
    y_pred = classifier.predict(X_test_scaled)
    
    accuracy = accuracy_score(y_test, y_pred)
    print(f"\nAccuracy: {accuracy * 100:.2f}%")
    
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, target_names=config.CLASS_NAMES))
    
    print("\nConfusion Matrix:")
    print(confusion_matrix(y_test, y_pred))
    
    # Save model
    print("\nSaving model...")
    predictor = AlzheimerPredictor()
    predictor.save_model(classifier, scaler)
    
    # Save training metrics
    metrics = {
        'accuracy': float(accuracy),
        'train_samples': len(X_train),
        'test_samples': len(X_test),
        'classes': config.CLASS_NAMES,
        'model_type': 'RandomForest + MobileNetV2'
    }
    
    metrics_path = os.path.join(config.MODEL_PATH, 'training_metrics.json')
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    print("\n" + "=" * 60)
    print("TRAINING COMPLETED SUCCESSFULLY!")
    print("=" * 60)
    
    return True


if __name__ == '__main__':
    # Create models directory
    os.makedirs('models', exist_ok=True)
    
    # Train model
    train_model()
