# GRC AI Backend - Deployment Guide

## 🚀 Quick Start

### Local Development
```bash
# Install dependencies
pip install -r app/requirements.txt

# Run server
cd app
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

### Docker Development
```bash
# Build and run
docker-compose up --build

# Stop
docker-compose down
```

## 🌍 Cloud Deployment Options

### 1. Render (Recommended for Students)
**Steps:**
1. Push code to GitHub
2. Connect Render account
3. Create new Web Service
4. Configure:
   - **Build Command**: `pip install -r app/requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Health Check Path**: `/`

### 2. Railway (Easiest)
**Steps:**
1. Push code to GitHub
2. Connect Railway
3. Railway auto-detects FastAPI
4. Set environment variables in Railway dashboard

### 3. AWS (Advanced)
**Options:**
- **EC2 + Docker**: Manual setup
- **ECS + Fargate**: Container orchestration
- **Lambda + API Gateway**: Serverless

## 🔧 Environment Variables

Required for production:
```env
DATABASE_URL=sqlite:///./grc.db
SECRET_KEY=CHANGE_THIS_IN_PRODUCTION_USE_RANDOM_STRING
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
ENVIRONMENT=production
ALLOWED_ORIGINS=https://yourdomain.com,https://yourapp.com
LOG_LEVEL=INFO
```

## 📱 Flutter Integration

Update your Flutter app's API URL:
```dart
// Development
String baseUrl = "http://127.0.0.1:8000";

// Production (after deployment)
String baseUrl = "https://your-backend.onrender.com";
```

## 🔐 Security Notes

- **SECRET_KEY**: Must be changed in production
- **CORS**: Restrict to your Flutter app domain
- **Database**: Use PostgreSQL for production
- **HTTPS**: Always use HTTPS in production

## 🐳 Docker Commands

```bash
# Build image
docker build -t grc-backend .

# Run container
docker run -p 8000:8000 grc-backend

# View logs
docker logs grc-backend
```

## 📊 Monitoring

### Health Check
- **Endpoint**: `GET /`
- **Response**: System status

### Logs
- **Location**: `/app/logs/`
- **Format**: JSON structured

## 🚨 Troubleshooting

### Common Issues:
1. **Port conflicts**: Change port in docker-compose.yml
2. **Database errors**: Check DATABASE_URL
3. **CORS issues**: Update ALLOWED_ORIGINS
4. **Import errors**: Verify requirements.txt

### Debug Commands:
```bash
# Check container status
docker ps

# View container logs
docker logs grc_backend

# Access container shell
docker exec -it grc_backend bash
```

## 📈 Production Checklist

- [ ] Change SECRET_KEY
- [ ] Set ALLOWED_ORIGINS
- [ ] Use PostgreSQL
- [ ] Enable HTTPS
- [ ] Set up monitoring
- [ ] Configure backups
- [ ] Test all endpoints
- [ ] Update Flutter API URL
