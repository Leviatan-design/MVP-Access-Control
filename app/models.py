import enum
from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class AccessType(str, enum.Enum):
    PEATONAL = "peatonal"
    VEHICULAR = "vehicular"


class VisitStatus(str, enum.Enum):
    SCHEDULED = "scheduled"
    INSIDE = "inside"
    EXITED = "exited"
    CANCELLED = "cancelled"


class Property(Base):
    __tablename__ = "properties"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    unit = Column(String(40), nullable=False)
    owner_name = Column(String(120), nullable=False)

    visits = relationship("Visit", back_populates="property")


class Visit(Base):
    __tablename__ = "visits"

    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(Integer, ForeignKey("properties.id"), nullable=False)
    visitor_name = Column(String(120), nullable=False)
    visitor_id = Column(String(40), nullable=False)
    access_type = Column(Enum(AccessType), nullable=False)
    scheduled_at = Column(DateTime, nullable=False)
    code = Column(String(10), unique=True, nullable=False, index=True)
    status = Column(Enum(VisitStatus), default=VisitStatus.SCHEDULED, nullable=False)
    entry_at = Column(DateTime, nullable=True)
    exit_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    property = relationship("Property", back_populates="visits")
