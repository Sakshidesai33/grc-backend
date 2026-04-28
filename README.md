# 🚀 GRC Incident Management System (AI-Powered Backend)

![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-green)
![Python](https://img.shields.io/badge/Python-3.10+-blue)
![Status](https://img.shields.io/badge/Status-Deployed-brightgreen)
![License](https://img.shields.io/badge/License-Academic-lightgrey)

A production-style AI-powered backend system built using **FastAPI** for Governance, Risk, and Compliance (GRC) Incident Management.

This system integrates:

- Machine Learning (AI predictions)
- Role-Based Access Control (RBAC)
- Cloud deployment (Render)
- Secure authentication system

to simulate a real-world enterprise-grade GRC platform.

---

# 🌍 Live Deployment

| Service | URL |
|--------|-----|
| 🚀 Backend API | https://grc-backend-dzop.onrender.com |
| 📘 Swagger Docs | https://grc-backend-dzop.onrender.com/docs |
| 🔗 Base API | https://grc-backend-dzop.onrender.com/api/v1 |

---

# 🏗 System Architecture

```text
Flutter Frontend
      ↓
Dio HTTP Client (JWT Authentication)
      ↓
FastAPI Backend (Render Cloud)
      ↓
Service Layer (Auth / Incident / Risk / AI)
      ↓
SQLAlchemy ORM Layer
      ↓
SQLite / PostgreSQL Database
      ↓
Machine Learning Models (Scikit-learn + NLP)
```

---

# ✨ Features

## 🔐 Authentication System
- JWT-based authentication
- Role-based access control (Admin / Analyst / Auditor)
- Secure password hashing using bcrypt

## 📊 Incident Management
- Create / Read / Update / Delete incidents
- AI-based incident classification
- Severity prediction system

## ⚠️ Risk Management
- Automated risk scoring (Probability × Impact)
- Risk mitigation suggestions
- Smart risk categorization

## 🤖 AI Intelligence Layer
- NLP-based incident classification (Phishing / Malware / Breach)
- Machine learning severity prediction
- Smart recommendation engine

## 📜 Compliance & Audit
- Audit logging system
- Compliance tracking module
- Activity traceability for all users

---

# 🛠 Tech Stack

- **Backend:** FastAPI  
- **Database:** SQLite (PostgreSQL ready)  
- **ORM:** SQLAlchemy  
- **Authentication:** JWT + bcrypt  
- **AI/ML:** Scikit-learn, spaCy  
- **Deployment:** Render Cloud  
- **API Docs:** Swagger UI  

---

# ⚙️ Setup Instructions

## 1️⃣ Install Dependencies
```bash
pip install -r requirements.txt
```

---

## 2️⃣ Run Backend Locally
```bash
uvicorn app.main:app --reload
```

---

## 3️⃣ Install NLP Model (Required for AI features)
```bash
python -m spacy download en_core_web_sm
```

---

# 📡 API Endpoints

## 🔐 Authentication
```
POST /register
POST /token
```

## 📊 Incidents
```
GET /incidents
POST /incidents
PUT /incidents/{id}
DELETE /incidents/{id}
```

## ⚠️ Risk Management
```
GET /risks
POST /risks
```

## 🤖 AI Services
```
POST /ai/predict-severity
POST /ai/classify-incident
POST /ai/suggest-actions
```

## 📊 Dashboard
```
GET /dashboard/stats
```

---

# 📱 Flutter Integration

## ❌ Wrong (Localhost)
```text
http://127.0.0.1:8000/incidents
```

## ✅ Correct (Production API)
```dart
final response = await http.get(
  Uri.parse('https://grc-backend-dzop.onrender.com/api/v1/incidents'),
  headers: {
    'Authorization': 'Bearer $token',
    'Content-Type': 'application/json',
  },
);
```

---

# 🔐 Security Features

- JWT authentication system  
- bcrypt password encryption  
- Role-Based Access Control (RBAC)  
- Full audit logging system  

---

# ☁️ Deployment

- Hosted on Render Cloud  
- Auto deployment from GitHub  
- Environment-based configuration  
- Production-ready FastAPI setup  

---

# 🧪 Testing

```bash
pytest
```

---

# 📈 Future Enhancements

- PostgreSQL migration for scalability  
- Docker containerization  
- CI/CD pipeline (GitHub Actions)  
- Real-time notifications (WebSockets)  
- Advanced AI models (Deep Learning upgrade)  
- Monitoring dashboard (Grafana integration)  

---

# 🏁 Project Summary

This project is a **full-stack AI-powered GRC system** that demonstrates:

✔ Backend engineering (FastAPI)  
✔ AI/ML integration (NLP + prediction models)  
✔ Secure authentication system  
✔ Cloud deployment (Render)  
✔ Flutter mobile integration  
```
