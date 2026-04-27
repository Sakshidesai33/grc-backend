from sqlalchemy.orm import Session
from .database import Base, engine, SessionLocal
from models.user import User
from models.incident import Incident
from core.security import hash_password

def create_tables():
    """Create all database tables"""
    # Drop all tables to force recreation with new schema
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables recreated with new schema")

def seed_data():
    """Seed initial data for testing"""
    db = SessionLocal()
    try:
        # Check if admin user exists
        admin_user = db.query(User).filter(User.email == "admin@demo.com").first()
        if not admin_user:
            # Create admin user
            admin_user = User(
                name="Admin User",
                first_name="Admin",
                last_name="User",
                email="admin@demo.com",
                role="admin",
                department="IT Security",
                hashed_password=hash_password("admin123")
            )
            db.add(admin_user)
            
            # Create sample users
            users = [
                User(
                    name="Security Manager",
                    first_name="Security",
                    last_name="Manager",
                    email="manager@demo.com",
                    role="manager",
                    department="Security",
                    hashed_password=hash_password("manager123")
                ),
                User(
                    name="Security Analyst",
                    first_name="Security",
                    last_name="Analyst",
                    email="analyst@demo.com",
                    role="analyst",
                    department="Security",
                    hashed_password=hash_password("analyst123")
                ),
                User(
                    name="Auditor",
                    first_name="Audit",
                    last_name="Specialist",
                    email="auditor@demo.com",
                    role="auditor",
                    department="Audit",
                    hashed_password=hash_password("auditor123")
                ),
                User(
                    name="Regular User",
                    first_name="Regular",
                    last_name="User",
                    email="user@demo.com",
                    role="user",
                    department="General",
                    hashed_password=hash_password("user123")
                )
            ]
            
            for user in users:
                db.add(user)
            
            # Create sample incidents
            incidents = [
                Incident(
                    title="Security Breach Detected",
                    description="Unauthorized access attempt detected on main database server",
                    severity="critical",
                    department="IT Security",
                    status="open"
                ),
                Incident(
                    title="Network Performance Issue",
                    description="High latency detected on primary network switch",
                    severity="medium",
                    department="Network Operations",
                    status="investigating"
                ),
                Incident(
                    title="Data Access Anomaly",
                    description="Unusual data access patterns detected in customer database",
                    severity="high",
                    department="Data Management",
                    status="open"
                )
            ]
            
            for incident in incidents:
                db.add(incident)
            
            db.commit()
            print("✅ Sample data seeded successfully")
        else:
            print("✅ Database already contains data")
            
    except Exception as e:
        import traceback
        print(f"❌ Error seeding data: {e}")
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

def init_database():
    """Initialize database with tables and sample data"""
    create_tables()
    seed_data()

if __name__ == "__main__":
    init_database()
