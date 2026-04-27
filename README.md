# GRC Incident Management System - Backend API

A comprehensive FastAPI backend for the GRC (Governance, Risk, Compliance) Incident Management System with AI-powered features.

## Features

- **Authentication & Authorization**: JWT-based auth with role-based access
- **Incident Management**: Full CRUD operations with AI classification
- **Risk Management**: Automated risk scoring and mitigation suggestions
- **Compliance Tracking**: Policy management and compliance scoring
- **AI Intelligence**:
  - Incident severity prediction
  - Smart incident classification
  - Automated action suggestions
  - Risk prediction analytics
- **Audit Logging**: Complete audit trail for compliance
- **Reporting**: Generate and export reports
- **Notifications**: Real-time notification system

## Tech Stack

- **Framework**: FastAPI
- **Database**: SQLite (easily switchable to PostgreSQL)
- **ORM**: SQLAlchemy
- **Authentication**: JWT tokens with bcrypt
- **AI/ML**: Scikit-learn, spaCy for NLP
- **Documentation**: Auto-generated Swagger UI

## Installation

1. **Create virtual environment**:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Download spaCy model** (for NLP):
```bash
python -m spacy download en_core_web_sm
```

## Running the API

Start the development server:
```bash
uvicorn main:app --reload
```

The API will be available at: `http://127.0.0.1:8000`

## API Documentation

Visit `http://127.0.0.1:8000/docs` for interactive Swagger UI documentation.

## Key Endpoints

### Authentication
- `POST /register` - User registration
- `POST /token` - Login and get access token

### Incidents
- `GET /incidents` - List all incidents
- `POST /incidents` - Create new incident (AI-enhanced)
- `PUT /incidents/{id}` - Update incident
- `DELETE /incidents/{id}` - Delete incident

### Risks
- `GET /risks` - List all risks
- `POST /risks` - Create new risk (AI-scored)

### Compliance
- `GET /compliance` - List compliance policies
- `POST /compliance` - Create compliance policy

### AI Features
- `POST /ai/predict-severity` - Predict incident severity
- `POST /ai/classify-incident` - Classify incident category
- `POST /ai/suggest-actions` - Get action recommendations

### Dashboard
- `GET /dashboard/stats` - Get dashboard statistics

## Database Schema

The system uses the following main tables:
- `users` - User accounts and roles
- `incidents` - Security incidents
- `risks` - Risk assessments
- `compliance_policies` - Compliance requirements
- `reports` - Generated reports
- `notifications` - User notifications
- `audit_logs` - Audit trail

## AI Features

### Incident Intelligence
- **Severity Prediction**: Analyzes incident description to predict severity level
- **Smart Classification**: Automatically categorizes incidents (Phishing, Malware, Breach, etc.)
- **Action Suggestions**: Provides contextual mitigation steps based on incident type

### Risk Analytics
- **Automated Scoring**: Calculates risk scores using probability × impact
- **Mitigation Suggestions**: Recommends specific mitigation strategies
- **Predictive Analysis**: Identifies high-risk departments based on historical data

## Security Features

- **JWT Authentication**: Secure token-based authentication
- **Password Hashing**: Bcrypt password encryption
- **Role-Based Access**: Admin, Risk Manager, Compliance Officer, Employee roles
- **Audit Logging**: Complete activity tracking for compliance

## Integration with Flutter App

The Flutter app can connect to this API using the `http` package:

```dart
final response = await http.get(
  Uri.parse('http://127.0.0.1:8000/incidents'),
  headers: {'Authorization': 'Bearer $token'},
);
```

## Development

### Adding New AI Features
1. Extend the `AIService` class in `ai_service.py`
2. Add new endpoints in `main.py`
3. Update Pydantic schemas in `schemas.py`

### Database Migrations
For production, consider using Alembic for database migrations.

### Testing
```bash
pytest
```

## Production Deployment

1. Change `SECRET_KEY` in `auth.py`
2. Use PostgreSQL instead of SQLite
3. Set up proper CORS for Flutter app
4. Configure HTTPS
5. Set up monitoring and logging

## License

This project is part of the GRC Incident Management System major project.