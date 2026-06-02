from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, JSONResponse
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy.orm import Session
from dotenv import load_dotenv
from datetime import datetime
import os
import tempfile
import json
import uuid
import traceback
from supabase import create_client, Client
load_dotenv(dotenv_path="../.env")

from agents import process_image, classify_uploaded_files
from case_agents import process_case, generate_suggestion
from doc_parser import extract_text
from database import (
    get_db, create_tables,
    User, ExamRecord,
    Patient, PatientMetric, PatientCondition, ClinicalCase,
)
from auth import hash_password, verify_password, create_token, get_optional_user, get_required_user
from pdf_generator import generate_report_pdf

app = FastAPI(title="MedAI API", version="2.0.0")

# Inicializa cliente Supabase se as chaves estiverem configuradas
supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_KEY")
supabase: Client = None
if supabase_url and supabase_key:
    supabase = create_client(supabase_url, supabase_key)

# Permite acesso do front-end
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc), "type": type(exc).__name__},
    )


@app.on_event("startup")
def startup():
    try:
        create_tables()
    except Exception as e:
        print(f"[startup] create_tables failed (non-fatal): {e}")


@app.get("/api/dbcheck")
def dbcheck():
    db_url = os.environ.get("DATABASE_URL", "NOT_SET")
    masked = db_url[:30] + "..." if len(db_url) > 30 else db_url
    try:
        from database import engine
        with engine.connect() as conn:
            conn.execute(__import__("sqlalchemy").text("SELECT 1"))
        return {"db": "connected", "url_preview": masked}
    except Exception as e:
        return {"db": "error", "url_preview": masked, "error": str(e)}


# ── Pydantic models ────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str

class PDFRequest(BaseModel):
    analysis: str
    research: str
    metadata: Optional[dict] = None

class PatientCreate(BaseModel):
    name: str
    birth_date: Optional[str] = ""
    sex: Optional[str] = ""
    height_cm: Optional[float] = None
    blood_type: Optional[str] = ""

class MetricCreate(BaseModel):
    date: str
    weight_kg: Optional[float] = None
    height_cm: Optional[float] = None
    notes: Optional[str] = ""

class ConditionCreate(BaseModel):
    condition: str

class PatientUpdate(BaseModel):
    name: Optional[str] = None
    birth_date: Optional[str] = None
    sex: Optional[str] = None
    blood_type: Optional[str] = None
    height_cm: Optional[float] = None

class SuggestRequest(BaseModel):
    specialty: str
    analysis: str
    suggestion_type: str
    patient_context: Optional[str] = ""

class FileInfoItem(BaseModel):
    index: int
    filename: str
    is_document: bool

class ClassifyRequest(BaseModel):
    files: List[FileInfoItem]


# ── Auth ───────────────────────────────────────────────────────────────────────

@app.post("/api/auth/register")
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == req.email).first():
        raise HTTPException(status_code=400, detail="Email já cadastrado.")
    user = User(name=req.name, email=req.email, hashed_password=hash_password(req.password))
    db.add(user); db.commit(); db.refresh(user)
    return {"token": create_token(user.id), "user": {"id": user.id, "name": user.name, "email": user.email}}

@app.post("/api/auth/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.email).first()
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Email ou senha incorretos.")
    return {"token": create_token(user.id), "user": {"id": user.id, "name": user.name, "email": user.email}}

@app.get("/api/auth/me")
def me(user: User = Depends(get_required_user)):
    return {"id": user.id, "name": user.name, "email": user.email}


# ── Quick history (Sprint 1) ───────────────────────────────────────────────────

@app.get("/api/history")
def get_history(user: User = Depends(get_required_user), db: Session = Depends(get_db)):
    exams = (
        db.query(ExamRecord)
        .filter(ExamRecord.user_id == user.id)
        .order_by(ExamRecord.created_at.desc())
        .limit(50).all()
    )
    return [
        {"id": e.id, "filename": e.filename, "modality": e.modality,
         "analysis": e.analysis, "research": e.research,
         "created_at": e.created_at.isoformat()}
        for e in exams
    ]


# ── PDF ────────────────────────────────────────────────────────────────────────

@app.post("/api/pdf")
def create_pdf(req: PDFRequest):
    pdf_bytes = generate_report_pdf(req.analysis, req.research, req.metadata)
    return Response(content=pdf_bytes, media_type="application/pdf",
                    headers={"Content-Disposition": "attachment; filename=laudo-medhub.pdf"})


# ── Quick analyze (Sprint 1) ───────────────────────────────────────────────────

@app.get("/")
def root():
    return {"status": "MedAI API v2 rodando."}

@app.post("/api/analyze")
async def analyze(
    file: UploadFile = File(...),
    user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    if not os.environ.get("GROQ_API_KEY"):
        raise HTTPException(status_code=500, detail="GROQ_API_KEY não configurada.")
    allowed = ["jpg", "jpeg", "png", "bmp", "gif", "dcm"]
    ext = file.filename.split(".")[-1].lower()
    if ext not in allowed:
        raise HTTPException(status_code=400, detail="Formato inválido. Use JPG, PNG, BMP, GIF ou DCM.")
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}") as tmp:
            tmp.write(await file.read()); tmp_path = tmp.name
        results = process_image(tmp_path)
        
        # Se Supabase estiver configurado, salva a imagem no Storage
        if supabase:
            try:
                import uuid
                file_name = f"{uuid.uuid4()}.{ext}"
                content_type = file.content_type or "image/jpeg"
                with open(tmp_path, "rb") as f:
                    file_bytes = f.read()
                
                supabase.storage.from_("medical-images").upload(
                    file_name,
                    file_bytes,
                    {"content-type": content_type}
                )
                
                public_url = supabase.storage.from_("medical-images").get_public_url(file_name)
                
                db_response = supabase.table("analyses").insert({
                    "image_url": public_url,
                    "analysis_text": results.get("analysis", ""),
                    "research_text": results.get("research", "")
                }).execute()
                
                if db_response.data:
                    results["db_id"] = db_response.data[0]["id"]
                    results["image_url"] = public_url
            except Exception as supabase_error:
                print(f"Erro ao salvar no Supabase: {supabase_error}")
                results["supabase_error"] = str(supabase_error)

        os.remove(tmp_path)
        if user:
            modality = (results.get("metadata") or {}).get("modality", "")
            db.add(ExamRecord(user_id=user.id, filename=file.filename,
                              modality=modality, analysis=results["analysis"],
                              research=results["research"]))
            db.commit()
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



# ── File Classification ────────────────────────────────────────────────────────

@app.post("/api/classify-files")
def classify_files(req: ClassifyRequest):
    file_infos = [{"index": f.index, "filename": f.filename, "is_document": f.is_document} for f in req.files]
    return classify_uploaded_files(file_infos)


# ── Suggest ───────────────────────────────────────────────────────────────────

@app.post("/api/suggest")
def suggest(req: SuggestRequest):
    if not os.environ.get("GROQ_API_KEY"):
        raise HTTPException(status_code=500, detail="GROQ_API_KEY não configurada.")
    try:
        result = generate_suggestion(
            specialty=req.specialty,
            analysis=req.analysis,
            suggestion_type=req.suggestion_type,
            patient_context=req.patient_context or "",
        )
        return {"suggestion": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Patients ───────────────────────────────────────────────────────────────────

def _patient_dict(p: Patient) -> dict:
    latest_metric = p.metrics[0] if p.metrics else None
    return {
        "id": p.id,
        "name": p.name,
        "birth_date": p.birth_date,
        "sex": p.sex,
        "height_cm": p.height_cm,
        "blood_type": p.blood_type,
        "weight_kg": latest_metric.weight_kg if latest_metric else None,
        "conditions": [{"id": c.id, "condition": c.condition} for c in p.conditions if c.active],
        "metrics": [{"id": m.id, "date": m.date, "weight_kg": m.weight_kg,
                     "height_cm": m.height_cm, "notes": m.notes} for m in p.metrics],
        "created_at": p.created_at.isoformat(),
    }

@app.get("/api/patients")
def list_patients(user: User = Depends(get_required_user), db: Session = Depends(get_db)):
    patients = db.query(Patient).filter(Patient.user_id == user.id).order_by(Patient.name).all()
    return [_patient_dict(p) for p in patients]

@app.post("/api/patients")
def create_patient(req: PatientCreate, user: User = Depends(get_required_user), db: Session = Depends(get_db)):
    p = Patient(user_id=user.id, name=req.name, birth_date=req.birth_date or "",
                sex=req.sex or "", height_cm=req.height_cm, blood_type=req.blood_type or "")
    db.add(p); db.commit(); db.refresh(p)
    return _patient_dict(p)

@app.get("/api/patients/{patient_id}")
def get_patient(patient_id: int, user: User = Depends(get_required_user), db: Session = Depends(get_db)):
    p = db.query(Patient).filter(Patient.id == patient_id, Patient.user_id == user.id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Paciente não encontrado.")
    return _patient_dict(p)

@app.post("/api/patients/{patient_id}/metrics")
def add_metric(patient_id: int, req: MetricCreate,
               user: User = Depends(get_required_user), db: Session = Depends(get_db)):
    p = db.query(Patient).filter(Patient.id == patient_id, Patient.user_id == user.id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Paciente não encontrado.")
    m = PatientMetric(patient_id=p.id, date=req.date, weight_kg=req.weight_kg,
                      height_cm=req.height_cm, notes=req.notes or "")
    db.add(m); db.commit()
    return {"ok": True}

@app.post("/api/patients/{patient_id}/conditions")
def add_condition(patient_id: int, req: ConditionCreate,
                  user: User = Depends(get_required_user), db: Session = Depends(get_db)):
    p = db.query(Patient).filter(Patient.id == patient_id, Patient.user_id == user.id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Paciente não encontrado.")
    c = PatientCondition(patient_id=p.id, condition=req.condition)
    db.add(c); db.commit()
    return {"ok": True}

@app.put("/api/patients/{patient_id}")
def update_patient(patient_id: int, req: PatientUpdate,
                   user: User = Depends(get_required_user), db: Session = Depends(get_db)):
    p = db.query(Patient).filter(Patient.id == patient_id, Patient.user_id == user.id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Paciente não encontrado.")
    if req.name is not None: p.name = req.name
    if req.birth_date is not None: p.birth_date = req.birth_date
    if req.sex is not None: p.sex = req.sex
    if req.blood_type is not None: p.blood_type = req.blood_type
    if req.height_cm is not None: p.height_cm = req.height_cm
    db.commit(); db.refresh(p)
    return _patient_dict(p)

@app.delete("/api/patients/{patient_id}/conditions/{condition_id}")
def delete_condition(patient_id: int, condition_id: int,
                     user: User = Depends(get_required_user), db: Session = Depends(get_db)):
    cond = (db.query(PatientCondition)
            .join(Patient)
            .filter(PatientCondition.id == condition_id,
                    PatientCondition.patient_id == patient_id,
                    Patient.user_id == user.id)
            .first())
    if not cond:
        raise HTTPException(status_code=404, detail="Condição não encontrada.")
    db.delete(cond); db.commit()
    return {"ok": True}

@app.get("/api/patients/{patient_id}/cases")
def get_patient_cases(patient_id: int,
                      user: User = Depends(get_required_user), db: Session = Depends(get_db)):
    p = db.query(Patient).filter(Patient.id == patient_id, Patient.user_id == user.id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Paciente não encontrado.")
    cases = (db.query(ClinicalCase)
             .filter(ClinicalCase.patient_id == patient_id, ClinicalCase.user_id == user.id)
             .order_by(ClinicalCase.created_at.desc()).all())
    return [_case_dict(c) for c in cases]


# ── Clinical Cases ─────────────────────────────────────────────────────────────

def _case_dict(c: ClinicalCase) -> dict:
    exams = json.loads(c.exams_summary or "[]")
    return {
        "id": c.id,
        "title": c.title,
        "patient_name": c.patient.name if c.patient else None,
        "chief_complaint": c.chief_complaint,
        "exams": exams,
        "analysis": c.analysis,
        "research": c.research,
        "created_at": c.created_at.isoformat(),
        "analyzed_at": c.analyzed_at.isoformat() if c.analyzed_at else None,
    }

@app.get("/api/cases")
def list_cases(user: User = Depends(get_required_user), db: Session = Depends(get_db)):
    cases = (db.query(ClinicalCase)
             .filter(ClinicalCase.user_id == user.id)
             .order_by(ClinicalCase.created_at.desc()).limit(50).all())
    return [_case_dict(c) for c in cases]

@app.post("/api/cases/analyze")
async def analyze_case(
    patient_json: str = Form(...),
    exams_json: str = Form(...),
    files: Optional[List[UploadFile]] = File(default=None),
    doc_files: Optional[List[UploadFile]] = File(default=None),
    user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    """
    Analyzes a complete clinical case.
    - patient_json: JSON with patient profile
    - exams_json: JSON array of {name, modality, exam_date, file_count}
    - files: all images flattened in order (exam0_files, exam1_files, ...)
    """
    if not os.environ.get("GROQ_API_KEY"):
        raise HTTPException(status_code=500, detail="GROQ_API_KEY não configurada.")

    try:
        patient_data = json.loads(patient_json)
        exams_meta = json.loads(exams_json)
    except Exception:
        raise HTTPException(status_code=400, detail="JSON inválido em patient_json ou exams_json.")

    tmp_paths: List[str] = []
    try:
        # Write all files to temp
        all_paths: List[str] = []
        for f in (files or []):
            ext = f.filename.split(".")[-1].lower()
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}") as tmp:
                tmp.write(await f.read())
                all_paths.append(tmp.name)
                tmp_paths.append(tmp.name)

        # Distribute paths to exams according to file_count
        exams_payload = []
        idx = 0
        for em in exams_meta:
            count = em.get("file_count", 0)
            exam_paths = all_paths[idx: idx + count]
            idx += count
            if exam_paths:
                exams_payload.append({
                    "name": em.get("name", ""),
                    "modality": em.get("modality", ""),
                    "exam_date": em.get("exam_date", ""),
                    "image_paths": exam_paths,
                })

        # Extract text from uploaded documents (PDF/DOCX)
        documents = []
        for df in (doc_files or []):
            ext = df.filename.split(".")[-1].lower()
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}") as tmp:
                tmp.write(await df.read())
                tmp_paths.append(tmp.name)
                text = extract_text(tmp.name)
                if text:
                    documents.append({"name": df.filename, "text": text})

        case_payload = {"patient": patient_data, "exams": exams_payload, "documents": documents}
        results = process_case(case_payload)

        # Persist to DB if user is authenticated
        if user:
            # Create or reuse patient record
            patient_record = None
            if patient_data.get("name"):
                patient_record = db.query(Patient).filter(
                    Patient.user_id == user.id,
                    Patient.name == patient_data["name"]
                ).first()
                if not patient_record:
                    patient_record = Patient(
                        user_id=user.id,
                        name=patient_data["name"],
                        birth_date=patient_data.get("birth_date", ""),
                        sex=patient_data.get("sex", ""),
                        height_cm=patient_data.get("height_cm"),
                    )
                    db.add(patient_record)
                    db.flush()

                    # Add conditions
                    for cond in patient_data.get("conditions", []):
                        if cond:
                            db.add(PatientCondition(patient_id=patient_record.id, condition=cond))

                # Add weight metric
                if patient_data.get("weight_kg"):
                    db.add(PatientMetric(
                        patient_id=patient_record.id,
                        date=datetime.utcnow().date().isoformat(),
                        weight_kg=patient_data["weight_kg"],
                        height_cm=patient_data.get("height_cm"),
                    ))

            exams_summary = json.dumps([
                {"name": e.get("name", ""), "modality": e.get("modality", ""),
                 "image_count": len(e.get("image_paths", []))}
                for e in exams_payload
            ], ensure_ascii=False)

            title = patient_data.get("name") or "Caso Clínico"
            if exams_payload:
                title += f" — {exams_payload[0].get('name', '')}"

            case_record = ClinicalCase(
                user_id=user.id,
                patient_id=patient_record.id if patient_record else None,
                title=title,
                chief_complaint=patient_data.get("chief_complaint", ""),
                clinical_history=patient_data.get("clinical_history", ""),
                exams_summary=exams_summary,
                analysis=results["analysis"],
                research=results["research"],
                analyzed_at=datetime.utcnow(),
            )
            db.add(case_record)
            db.commit()
            results["case_id"] = case_record.id

        return results

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        for p in tmp_paths:
            try:
                if os.path.exists(p):
                    os.remove(p)
            except Exception:
                pass
