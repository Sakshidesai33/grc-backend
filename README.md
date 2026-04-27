# 🚀 GRC Incident Management System - Backend API

A comprehensive **FastAPI backend system** for the GRC (Governance, Risk, Compliance) Incident Management System with AI-powered features.

---

## 🌍 Live System

- **Backend API**:  
  https://grc-backend-dzop.onrender.com

- **Swagger Documentation**:  
  https://grc-backend-dzop.onrender.com/docs

- **Base API URL**:  
  https://grc-backend-dzop.onrender.com/api/v1

---

## ✨ Features

### 🔐 Authentication & Authorization
- JWT-based secure authentication
- Role-based access control (Admin / Analyst / Auditor)
- Password hashing using bcrypt

### 📊 Incident Management
- Full CRUD operations for incidents
- AI-powered incident classification
- Severity prediction system

### ⚠️ Risk Management
- Automated risk scoring
- Risk level classification
- Mitigation suggestions

### 📜 Compliance Tracking
- Policy management system
- Compliance scoring engine
- Audit-ready tracking system

### 🤖 AI Intelligence Engine
- Incident severity prediction
- Smart incident classification (Phishing / Malware / Breach)
- Automated action recommendations
- Risk analytics engine

### 📁 Audit System
- Complete system audit logging
- User activity tracking
- Compliance history

### 📢 Notifications
- Real-time notification system
- System alerts and updates

---

## 🛠 Tech Stack

- **Backend Framework**: FastAPI
- **Database**: SQLite (production-ready for PostgreSQL upgrade)
- **ORM**: SQLAlchemy
- **Authentication**: JWT + bcrypt
- **AI/ML**: Scikit-learn, spaCy (NLP)
- **Documentation**: Swagger UI (auto-generated)

---

## ⚙️ Installation (Local Setup)

### 1️⃣ Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
