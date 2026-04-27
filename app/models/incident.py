from sqlalchemy import Column, Integer, String, Text, DateTime
from db.database import Base

class Incident(Base):
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    description = Column(Text)
    severity = Column(String)
    status = Column(String)
    department = Column(String)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
