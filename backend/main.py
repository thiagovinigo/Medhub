from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
import tempfile

# Carrega variáveis de ambiente na raiz ANTES de importar agents
load_dotenv(dotenv_path="../.env")

from agents import process_image

app = FastAPI(title="MedAI API", version="1.0.0")

# Permite acesso do front-end
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Mude para a porta do frontend em produção
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"status": "Backend rodando. Bem-vindo à API MedAI."}

@app.post("/api/analyze")
async def analyze_medical_image(file: UploadFile = File(...)):
    if not os.environ.get("GROQ_API_KEY"):
        raise HTTPException(status_code=500, detail="Chaves de API do Groq não configuradas no ambiente.")
    
    # Valida formato da imagem
    allowed_extensions = ["jpg", "jpeg", "png", "bmp", "gif"]
    file_ext = file.filename.split(".")[-1].lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail="Formato de arquivo inválido.")
    
    # Salva temporariamente
    try:
        # Usa um arquivo temporário
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_ext}") as temp_file:
            contents = await file.read()
            temp_file.write(contents)
            temp_file_path = temp_file.name

        # Processa através da pipeline de Agentes
        results = process_image(temp_file_path)

        # Remove arquivo original salvo temporariamente
        os.remove(temp_file_path)

        return results

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
