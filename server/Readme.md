# Setup & Run

## Step 1 — Create virtual environment
```bash
python3.11 -m venv venv
source venv/bin/activate
```
(Windows: `venv\Scripts\activate`)

## Step 2 — Install dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

## Step 3 — Make sure model files are in place
- sizePredictionEngine/Y26sizeEnginev6.0.pt
- backend/models/final_model.keras
- backend/models/label_classes.npy
- backend/models/cvd_generator_weights.npz
- backend/models/preprocessing_config.json
- backend/models/pattern_model_weights.npz
- backend/models/pattern_config.json

## Step 4 — Run the server
```bash
uvicorn server:app --host 0.0.0.0 --port 8000 --reload
```

## Step 5 — Open it
```
http://localhost:8000/docs
```

Done. Size prediction: /predict. Color/CVD/pattern: /coloranalyzer/...