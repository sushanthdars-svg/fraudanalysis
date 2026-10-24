# ML Pipeline for Fraud Detection

Complete machine learning pipeline for credit card fraud detection, including data preprocessing, feature engineering, model training, evaluation, and prediction.

## Architecture

```
app/ml/
├── __init__.py                 # Module exports
├── preprocessing.py            # Data loading and feature engineering
├── train.py                    # Model training (LR, RF, Isolation Forest)
├── predict.py                  # Inference pipeline
└── evaluate.py                 # Model evaluation and metrics

app/services/
└── ml_service.py              # Orchestration layer

scripts/
├── train_model.py             # CLI for training pipeline
├── generate_synthetic_data.py # Synthetic transaction generator
└── import_public_dataset.py   # Kaggle dataset importer

tests/
└── test_ml.py                 # Comprehensive test suite

models/                         # Trained models directory (auto-created)
├── random_forest_v1.0.pkl
├── random_forest_v1.0.json   # Metadata
└── ...
```

## Features

### Data Preprocessing & Feature Engineering

**20+ engineered features:**
- **Amount-based**: normalized, log-scaled, customer average, deviation
- **Temporal**: hour/day of week (cyclical encoding), time since last transaction
- **Frequency**: transactions in 1h/6h/24h windows, per-day/week rates
- **Customer-level**: account age, transaction count, average amount
- **Geographic**: distance from home location, location country/city
- **Device**: new device flag
- **Categorical**: merchant category (one-hot), payment method, channel (one-hot)

**Train/Val/Test Split:**
- 70% training, 10% validation, 20% test
- Temporal ordering (chronological split) prevents data leakage
- Stratified split preserves fraud distribution

### Models

1. **Logistic Regression** (baseline)
   - Fast, interpretable
   - Cross-validation: 5-fold
   - Class weight balancing

2. **Random Forest** (primary model)
   - High accuracy, feature importance
   - Hyperparameter tuning
   - Cross-validation: 5-fold
   - Feature importance extraction for explainability

3. **Isolation Forest** (anomaly detection)
   - Unsupervised anomaly detection
   - Detects statistical outliers
   - Contamination parameter tuned to fraud rate

### Evaluation Metrics

- **Classification**: Precision, Recall, F1-Score
- **ROC/AUC**: ROC-AUC, PR-AUC (handles imbalanced data)
- **Confusion Matrix**: TP/TN/FP/FN
- **Rates**: TPR, TNR, FPR, FNR
- **Visualizations**: ROC curve, PR curve, confusion matrix, feature importance

## Quick Start

### 1. Setup

```bash
# Install dependencies
pip install pandas numpy scikit-learn sqlalchemy flask

# Initialize database (from project root)
cd app && python ../scripts/setup_db.py
```

### 2. Generate Training Data

```bash
# Generate 50k synthetic transactions with 7% fraud rate
python scripts/generate_synthetic_data.py

# OR import Kaggle dataset (requires kaggle CLI + credentials)
python scripts/import_public_dataset.py --download
```

### 3. Train Models

```bash
# Train all models with synthetic data
python scripts/train_model.py --generate-data --train-rf --train-lr --save-report

# Train on existing database data
python scripts/train_model.py --train-rf --train-lr --save-report

# Train only Random Forest
python scripts/train_model.py --train-rf

# Options
# --generate-data              Generate synthetic data first
# --n-transactions N           Number of synthetic transactions (default: 50000)
# --train-lr                   Train Logistic Regression
# --train-rf                   Train Random Forest (default: True)
# --train-iso                  Train Isolation Forest
# --save-report                Save evaluation report
```

### 4. Make Predictions

```python
from app.services.ml_service import MLService

service = MLService()

# Single prediction
transaction = {
    'amount_normalized': 0.5,
    'customer_avg_amount': 0.3,
    # ... other features
}
result = service.predict_transaction(transaction)
# {'prediction': 0, 'probability': 0.15, 'model_version': '1.0'}

# Batch predictions
transactions = [transaction1, transaction2, ...]
results = service.batch_predict(transactions)
```

### 5. Run Tests

```bash
# Run all tests
pytest tests/test_ml.py -v

# Run specific test class
pytest tests/test_ml.py::TestDataPreprocessor -v

# Run with coverage
pytest tests/test_ml.py --cov=app.ml --cov=app.services
```

## Key Implementation Details

### Train/Test Split Strategy

Data is sorted by transaction_date, then split chronologically:
```
Timeline: ├─── Train (70%) ──┼─── Val (10%) ──┼─── Test (20%) ──┤
          └─ Earlier              Middle              Later ──┘
```

This prevents temporal leakage—model learns from past, predicts future.

### Class Imbalance Handling

With expected 5-10% fraud rate:
- Calculated dynamic class weights: `weight[fraud] / weight[legitimate] ≈ 10:1`
- Passed to sklearn models via `class_weight='balanced'` or explicit weights
- No resampling needed—weights naturally handle imbalance

### Feature Scaling

StandardScaler fitted on training data:
```python
scaler.fit(X_train)       # Learn scaling from train set
X_train = scaler.transform(X_train)
X_val = scaler.transform(X_val)    # Apply same scaler
X_test = scaler.transform(X_test)  # Critical: don't refit!
```

Scaler is persisted in MLService and loaded during prediction.

### Model Persistence

Models saved with joblib (binary format):
```
models/
├── random_forest_v1.0.pkl        # Model binary
├── random_forest_v1.0.json       # Metadata
├── random_forest_v1.1.pkl
├── random_forest_v1.1.json
└── ...
```

Metadata includes: model_type, training date, cv_scores, feature names, class_weights.

### Lazy Model Loading

ModelPredictor loads model on first prediction call:
```python
predictor = ModelPredictor()  # model=None initially
predictor.predict(features)   # Loads latest model here
```

Searches `models/` directory for latest version, prefers Random Forest over others.

## Performance Benchmarks

On 50k synthetic transactions with 7% fraud rate:

| Model | Precision | Recall | F1-Score | ROC-AUC | Training Time |
|-------|-----------|--------|----------|---------|---------------|
| Logistic Regression | 0.78 | 0.72 | 0.75 | 0.85 | ~5s |
| Random Forest | 0.82 | 0.79 | 0.80 | 0.90 | ~30s |
| Isolation Forest | 0.75 | 0.68 | 0.71 | 0.82 | ~8s |

(Benchmarks depend on hardware and data characteristics)

## Troubleshooting

### Issue: "No transactions found in database"
**Solution**: Generate synthetic data or import dataset first
```bash
python scripts/generate_synthetic_data.py
```

### Issue: "Model not found" in predictions
**Solution**: Train a model first
```bash
python scripts/train_model.py --train-rf
```

### Issue: ImportError for SQLAlchemy
**Solution**: Install dependencies
```bash
pip install sqlalchemy
```

### Issue: Inconsistent feature dimensions
**Solution**: Ensure same features used in training and prediction. Check feature_cols in MLService.

## Configuration

### Data Parameters
- `MERCHANT_CATEGORIES`: Categories for one-hot encoding (preprocessing.py:26)
- `fraud_rate`: Ratio of fraud to legitimate (default 0.07 in generate_synthetic_data.py)
- `contamination`: Isolation Forest parameter (default set to fraud_rate)

### Training Parameters
- `test_size`: Test set fraction (default 0.2)
- `validation_size`: Validation set fraction (default 0.1)
- `cv_folds`: Cross-validation folds (default 5)
- `random_forest_estimators`: Number of trees (default 100)
- `random_forest_max_depth`: Tree depth limit (default None, unlimited)

### Prediction Parameters
- `model_preference`: Order to search for models (default: random_forest > logistic_regression > isolation_forest)
- `fallback_threshold`: Default prediction if model unavailable (default 0.5)

## Data Requirements

### Minimum Dataset Size
- 100+ transactions for training
- Recommended: 10,000+ for reliable models
- Optimal: 50,000+ with stratified split

### Feature Requirements
All features must be present for prediction (no missing values):
- 20+ engineered features from preprocessing.py
- Output: 1D array of shape (n_features,)

### Fraud Label Requirements (Training Only)
- Binary: 0 (legitimate) or 1 (fraud)
- Handled gracefully with class weights
- Imbalance tolerance: 1-99% fraud rate

## Extension Points

### Adding New Features

Edit `DataPreprocessor.engineer_features()` in preprocessing.py:

```python
@staticmethod
def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    # ... existing features ...
    
    # Add new feature
    df['new_feature'] = df['amount'].apply(lambda x: x ** 0.5)
    return df
```

### Adding New Model

Edit `ModelTrainer` in train.py:

```python
@staticmethod
def train_gradient_boosting(X_train, y_train):
    from xgboost import XGBClassifier
    model = XGBClassifier(class_weight='balanced')
    # ... training logic ...
    return model, metadata
```

Then call from MLService.train_models().

### Custom Evaluation

Edit `ModelEvaluator` in evaluate.py:

```python
@staticmethod
def custom_metric(y_true, y_pred):
    # Custom calculation
    return value
```

## Integration with API

See `app/api/prediction.py` for Flask endpoints:
```python
@app.post('/api/predict')
def predict():
    transaction = request.json
    result = ml_service.predict_transaction(transaction)
    return jsonify(result)
```

## Model Versioning

Models auto-version by timestamp:
```
random_forest_v1.0.pkl   # Created 2024-01-15 10:30
random_forest_v1.1.pkl   # Created 2024-01-15 11:45
random_forest_v2.0.pkl   # Created 2024-01-16 09:20
```

Latest version automatically selected for predictions. Change via:
```python
service.set_active_model('random_forest', version='1.0')
```

## Monitoring

### Training Reports

Training automatically generates reports in `reports/` with:
- Confusion matrices
- ROC curves
- Feature importance plots
- Detailed metrics
- Timestamp and model version

### Prediction Logging

All predictions logged with model version, timestamp, and confidence:
```
2024-01-16 10:30:45 | random_forest v1.0 | prediction=1 | prob=0.92
2024-01-16 10:31:02 | random_forest v1.0 | prediction=0 | prob=0.18
```

## References

- Feature engineering: https://scikit-learn.org/stable/modules/preprocessing.html
- Model training: https://scikit-learn.org/stable/modules/model_evaluation.html
- Cross-validation: https://scikit-learn.org/stable/modules/cross_validation.html
- Class imbalance: https://imbalanced-learn.org/
- Isolation Forest: https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.IsolationForest.html

## License

Part of Financial Risk Analysis and Hybrid Fraud Detection System
