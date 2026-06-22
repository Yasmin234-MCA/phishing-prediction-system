# phishing-prediction-system
Deep Learning based phishing prediction system 

A machine learning-based system to detect and classify phishing emails as **legitimate or phishing**.

##  Overview
This project analyzes email content using ML algorithms to predict whether an email is a phishing attempt or a legitimate one — helping users stay safe from cyber threats.

##  Features
- 📧 Detects phishing emails with high accuracy
- 🤖 Machine learning-powered classification
- 📊 Visual results and prediction output
- ⚡ Fast and easy to use

##  Tech Stack
- **Language:** Python
- **Libraries:** scikit-learn, pandas, numpy, matplotlib, seaborn
- **Model:** Deep Learning (COnvolutional Neural Network)
- **Frontend:** Flask 

## Project Structure
phishing-prediction-system/

├── dataset/              # Email dataset (CSV)
├── model/                # Saved trained model (.pkl)
├── static/               # CSS, images, screenshots
│   └── screenshots/      # 📸 App screenshots
├── templates/            # HTML templates (if Flask)
├── app.py                # Main application
├── train.py              # Model training script
├── requirements.txt      # Dependencies
└── README.md

## ▶️ How to Run
1. Clone the repo
2. Install dependencies → `pip install -r requirements.txt`
3. Run the app → `python app.py`
4. Open browser → `http://localhost:5000`
