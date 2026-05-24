from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, Float, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime

DATABASE_URL = "sqlite:///./medhub.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    exams = relationship("ExamRecord", back_populates="user", cascade="all, delete")
    patients = relationship("Patient", back_populates="user", cascade="all, delete")
    cases = relationship("ClinicalCase", back_populates="user", cascade="all, delete")


class ExamRecord(Base):
    __tablename__ = "exam_records"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    filename = Column(String, default="")
    modality = Column(String, default="")
    analysis = Column(Text, nullable=False)
    research = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    user = relationship("User", back_populates="exams")


class Patient(Base):
    __tablename__ = "patients"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    birth_date = Column(String, default="")   # ISO date string YYYY-MM-DD
    sex = Column(String, default="")           # M, F, O
    height_cm = Column(Float)
    blood_type = Column(String, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    user = relationship("User", back_populates="patients")
    metrics = relationship("PatientMetric", back_populates="patient", cascade="all, delete", order_by="PatientMetric.date.desc()")
    conditions = relationship("PatientCondition", back_populates="patient", cascade="all, delete")
    cases = relationship("ClinicalCase", back_populates="patient", cascade="all, delete")


class PatientMetric(Base):
    """Dated weight/height entries for a patient — tracks evolution over time."""
    __tablename__ = "patient_metrics"
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    date = Column(String, nullable=False)    # YYYY-MM-DD
    weight_kg = Column(Float)
    height_cm = Column(Float)
    notes = Column(String, default="")
    patient = relationship("Patient", back_populates="metrics")


class PatientCondition(Base):
    """Pre-existing medical conditions for a patient."""
    __tablename__ = "patient_conditions"
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    condition = Column(String, nullable=False)
    active = Column(Boolean, default=True)
    patient = relationship("Patient", back_populates="conditions")


class ClinicalCase(Base):
    """A clinical case: contains patient context, multiple exams, and the consolidated AI analysis."""
    __tablename__ = "clinical_cases"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=True)
    title = Column(String, nullable=False)
    chief_complaint = Column(Text, default="")
    clinical_history = Column(Text, default="")
    exams_summary = Column(Text, default="[]")  # JSON array of {name, modality, image_count}
    analysis = Column(Text)
    research = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    analyzed_at = Column(DateTime)
    user = relationship("User", back_populates="cases")
    patient = relationship("Patient", back_populates="cases")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    Base.metadata.create_all(bind=engine)
