@echo off
title Setup Proyecto Data Science

echo Creando estructura optimizada...

mkdir backend
mkdir frontend
mkdir backend\app
mkdir backend\app\routes
mkdir backend\app\services
mkdir backend\app\models
mkdir backend\data
mkdir backend\data\raw
mkdir backend\data\processed
mkdir backend\scripts
mkdir backend\notebooks

mkdir frontend\js
mkdir frontend\css

echo Creando archivos base...

type nul > backend\app\main.py
type nul > backend\app\routes\predict.py
type nul > backend\app\services\predict_service.py
type nul > backend\scripts\train_classification.py
type nul > backend\scripts\train_regression.py

type nul > frontend\index.html
type nul > frontend\js\main.js
type nul > frontend\js\charts.js

cd backend
python -m venv venv

echo fastapi >> requirements.txt
echo uvicorn >> requirements.txt
echo pandas >> requirements.txt
echo scikit-learn >> requirements.txt
echo xgboost >> requirements.txt
echo lightgbm >> requirements.txt
echo joblib >> requirements.txt

echo Setup completo.
pause