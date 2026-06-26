import os
import re
import json
from dotenv import load_dotenv
load_dotenv(dotenv_path="../.env")

from PIL import Image as PILImage
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.media import Image as AgnoImage
from agno.tools.tavily import TavilyTools
from textwrap import dedent

ID_MODEL_VISION = "gpt-4o"
ID_MODEL_TEXT = "gpt-4o-mini"

prompt_analysis = """
Você é um especialista altamente qualificado em imagens médicas, com profundo conhecimento em diagnóstico por imagem.
Forneça o resultado direto, sem nenhuma frase ou apresentação sua antes ou ao final do resultado.
Analise a imagem médica e estruture sua resposta (em português) da seguinte forma:

### 1. Tipo de imagem e região
 - Identifique o tipo de exame (raio-X, ressonância magnética, tomografia, ultrassom, etc.).
 - Especifique a região anatômica e o posicionamento do paciente.
 - Avalie a qualidade técnica da imagem (resolução, cortes, artefatos, etc.).

### 2. Achados relevantes
 - Aponte observações clínicas relevantes de forma sistemática.
 - Descreva possíveis anomalias, com detalhes visuais.

### 3. Avaliação diagnóstica
 - Proponha um diagnóstico principal com nível de confiança (ex: alto, moderado).
 - Liste diagnósticos diferenciais por ordem de probabilidade.
 - Seja sempre sincero quanto à certeza que você possui sobre o diagnóstico.
 - Justifique com base nas evidências visuais encontradas.
 - Destaque qualquer detalhe crítico ou urgente.

### 4. Explicação em linguagem leiga
 - Reescreva os achados de forma compreensível para o paciente.
 - Evite jargões médicos ou explique-os brevemente.
 - Use analogias visuais ou comparações comuns quando útil.
 - Aborde preocupações frequentes que pacientes possuem, relacionado a esse tipo de exame.
"""

prompt_search_template = """Com base na seguinte análise de imagem médica, realize uma pesquisa complementar.
 - Forneça o resultado direto, sem nenhuma frase ou apresentação sua antes ou ao final do resultado.
 - Traga protocolos clínicos ou avanços tecnológicos relevantes.
 - Forneça 2 a 3 links ou referências confiáveis.
 - Organize sua resposta de forma clara, estruturada e precisa, usando marcação (markdown) quando possível para facilitar a leitura.

Resultado da análise médica: "{}"
"""


def preprocess_img(img_path: str):
    """Prepara imagem para análise. Suporta DICOM (.dcm) e formatos comuns."""
    metadata: dict = {}

    if img_path.lower().endswith('.dcm'):
        import pydicom
        import numpy as np

        ds = pydicom.dcmread(img_path)

        metadata['modality'] = str(getattr(ds, 'Modality', ''))
        raw_name = getattr(ds, 'PatientName', '')
        metadata['patient_name'] = str(raw_name) if raw_name else ''
        raw_date = str(getattr(ds, 'StudyDate', ''))
        if len(raw_date) == 8:
            metadata['study_date'] = f"{raw_date[6:]}/{raw_date[4:6]}/{raw_date[:4]}"

        pixel_array = ds.pixel_array.astype(np.float64)

        # Apply Hounsfield rescale if present (CT scans)
        slope = float(getattr(ds, 'RescaleSlope', 1))
        intercept = float(getattr(ds, 'RescaleIntercept', 0))
        pixel_array = pixel_array * slope + intercept

        # Multi-frame DICOM: take the middle frame
        if pixel_array.ndim == 3 and pixel_array.shape[0] < pixel_array.shape[1]:
            pixel_array = pixel_array[pixel_array.shape[0] // 2]

        # Normalize to 0-255
        pmin, pmax = pixel_array.min(), pixel_array.max()
        if pmax > pmin:
            pixel_array = (pixel_array - pmin) / (pmax - pmin) * 255
        pixel_array = pixel_array.astype('uint8')

        image = PILImage.fromarray(pixel_array)
        if image.mode not in ('L', 'RGB'):
            image = image.convert('RGB')
    else:
        image = PILImage.open(img_path)

    width, height = image.size
    img_width = 600
    img_height = int(img_width / (width / height))
    resized = image.resize((img_width, img_height))

    temp_path = img_path + "_resized.png"
    resized.save(temp_path)
    return temp_path, resized, metadata


def format_res(res: str, return_thinking: bool = False) -> str:
    res = res.strip()
    if return_thinking:
        res = res.replace("<think>", "[pensando...] ")
        res = res.replace("</think>", "\n---\n")
    else:
        if "</think>" in res:
            res = res.split("</think>")[-1].strip()
    res = res.replace("```", "")
    return res


def process_image(file_path: str) -> dict:
    """Executa o pipeline completo: análise + pesquisa usando OpenAI."""
    openai_key = os.environ.get("OPENAI_API_KEY")
    tavily_key = os.environ.get("TAVILY_API_KEY")

    if not openai_key:
        raise Exception("Chaves de API da OpenAI ausentes. O sistema precisa do GPT para rodar.")

    med_agent = Agent(
        name="Medical Image Agent",
        role="Especialista em imagens médicas",
        model=OpenAIChat(id=ID_MODEL_VISION),
        markdown=True,
    )

    tools = [TavilyTools()] if tavily_key else []
    research_agent = Agent(
        name="Researcher Agent",
        role="Pesquisador médico",
        instructions=dedent(
            """Você é um pesquisador médico responsável por buscar informações complementares sobre os achados identificados na imagem médica.
            Utilize ferramentas de busca (se ativas) para encontrar literatura médica recente, protocolos de tratamento padrão e avanços tecnológicos relevantes."""
        ),
        model=OpenAIChat(id=ID_MODEL_TEXT),
        tools=tools,
    )

    temp_path, _, metadata = preprocess_img(file_path)
    agno_img = AgnoImage(filepath=temp_path)

    res_med = med_agent.run(prompt_analysis, images=[agno_img])
    analysis_text = format_res(res_med.content)

    prompt_search = prompt_search_template.format(analysis_text)
    res_search = research_agent.run(prompt_search)
    research_text = format_res(res_search.content)

    if os.path.exists(temp_path):
        os.remove(temp_path)

    return {
        "analysis": analysis_text,
        "research": research_text,
        "metadata": metadata,
    }


# ── File Classification Agent ──────────────────────────────────────────────────

_VISION_CLASSIFY_PROMPT = """Você é um especialista em imagens médicas. Olhe esta imagem e responda APENAS com um JSON válido, sem texto extra, sem markdown.

Identifique:
- modality: XR (raio-x), MR (ressonância), CT (tomografia), US (ultrassom), ou outro
- region: região anatômica em português (ex: joelho, tórax, coluna, abdômen)
- exam_name: nome curto do exame (ex: "Raio-X Joelho", "RM Coluna")

Formato obrigatório:
{"modality":"XR","region":"joelho","exam_name":"Raio-X Joelho"}"""


def _vision_classify_single(image_path: str, filename: str) -> dict:
    """Calls vision model to identify modality and region of one image."""
    openai_key = os.environ.get("OPENAI_API_KEY")
    fallback = {"modality": "", "region": "", "exam_name": _clean_filename(filename)}
    if not openai_key:
        return fallback
    temp_path = None
    try:
        temp_path, _, _ = preprocess_img(image_path)
        agno_img = AgnoImage(filepath=temp_path)
        agent = Agent(
            name="Image Classifier",
            model=OpenAIChat(id=ID_MODEL_VISION),
            markdown=False,
        )
        result = agent.run(_VISION_CLASSIFY_PROMPT, images=[agno_img])
        text = format_res(result.content)
        match = re.search(r'\{[^}]+\}', text)
        if match:
            data = json.loads(match.group())
            # Ensure exam_name is never empty
            if not data.get("exam_name"):
                mod = data.get("modality", "")
                region = data.get("region", "")
                data["exam_name"] = f"{mod} {region}".strip() or _clean_filename(filename)
            return data
    except Exception as e:
        print(f"[vision_classify] {e}")
    finally:
        if temp_path:
            try:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            except Exception:
                pass
    return fallback


def _clean_filename(filename: str) -> str:
    return filename.rsplit(".", 1)[0].replace("_", " ").replace("-", " ").strip().capitalize() or "Exame"


_LAB_KEYWORDS = {
    "hemograma", "sangue", "laborat", "bioquim", "lipidio", "lipídio",
    "colesterol", "glicemia", "trigliceride", "triglicéride", "urina",
    "urinalise", "hematol", "sorolog", "creatinina", "ureia",
    "hormônio", "hormonio", "tsh", "insulina", "hba1c", "vitamina",
    "ferritina", "plaqueta", "leucocito", "leucócito", "resultado",
    "exame lab", "analise", "painel", "pcr", "eletroforese",
}


def _is_lab_document(filename: str) -> bool:
    name = filename.lower().replace("_", " ").replace("-", " ")
    return any(kw in name for kw in _LAB_KEYWORDS)


def classify_files_with_vision(file_entries: list) -> dict:
    """
    Classifies uploaded files using the vision model for images.
    file_entries: [{"index": int, "filename": str, "path": str, "is_document": bool}]
    Returns:
      {
        "exams": [{"name", "modality", "indices"}],
        "document_indices": [int],        # background docs (laudos, receitas)
        "document_exam_indices": [int],   # lab-result PDFs → analyzed as exams
      }
    """
    doc_indices = []
    doc_exam_indices = []
    for e in file_entries:
        if e["is_document"]:
            if _is_lab_document(e["filename"]):
                doc_exam_indices.append(e["index"])
            else:
                doc_indices.append(e["index"])

    image_entries = [e for e in file_entries if not e["is_document"]]

    if not image_entries:
        return {"exams": [], "document_indices": doc_indices, "document_exam_indices": doc_exam_indices}

    # Classify each image with vision model
    classified = []
    for entry in image_entries:
        info = _vision_classify_single(entry["path"], entry["filename"])
        info["index"] = entry["index"]
        classified.append(info)

    # Group by (modality, region).
    # If either is empty the model couldn't classify → treat as its own exam.
    groups: dict = {}
    for c in classified:
        mod = (c.get("modality") or "").upper().strip()
        reg = (c.get("region") or "").lower().strip()
        key = f"{mod}_{reg}" if (mod and reg) else f"_unclassified_{c['index']}"
        if key not in groups:
            groups[key] = {
                "name": c.get("exam_name") or f"{mod} {reg}".strip() or _clean_filename(c.get("filename", "")),
                "modality": mod,
                "indices": [],
            }
        groups[key]["indices"].append(c["index"])

    exams = list(groups.values())
    return {"exams": exams, "document_indices": doc_indices, "document_exam_indices": doc_exam_indices}
