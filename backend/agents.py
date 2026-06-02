import os
import re
import json
from dotenv import load_dotenv
load_dotenv(dotenv_path="../.env")

from PIL import Image as PILImage
from agno.agent import Agent
from agno.models.groq import Groq
from agno.media import Image as AgnoImage
from agno.tools.tavily import TavilyTools
from textwrap import dedent

ID_MODEL_VISION = "meta-llama/llama-4-scout-17b-16e-instruct"
ID_MODEL_TEXT = "llama-3.3-70b-versatile"

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
    """Executa o pipeline completo: análise + pesquisa usando Groq."""
    groq_key = os.environ.get("GROQ_API_KEY")
    tavily_key = os.environ.get("TAVILY_API_KEY")

    if not groq_key:
        raise Exception("Chaves de API do Groq ausentes. O sistema precisa do Llama para rodar.")

    med_agent = Agent(
        name="Medical Image Agent",
        role="Especialista em imagens médicas",
        model=Groq(id=ID_MODEL_VISION),
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
        model=Groq(id=ID_MODEL_TEXT),
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

def classify_uploaded_files(file_infos: list) -> dict:
    """
    Classifies a list of uploaded files into exam groups using LLM.
    file_infos: [{"index": int, "filename": str, "is_document": bool}]
    Returns: {"exams": [{"name": str, "modality": str, "indices": [int]}], "document_indices": [int]}
    """
    groq_key = os.environ.get("GROQ_API_KEY")
    if not groq_key:
        return _heuristic_classify(file_infos)

    files_text = "\n".join(
        f'  {f["index"]}: "{f["filename"]}" ({"documento" if f["is_document"] else "imagem médica"})'
        for f in file_infos
    )

    prompt = f"""Você é um classificador de arquivos médicos. Analise os nomes dos arquivos e agrupe-os em exames separados.

Arquivos recebidos:
{files_text}

Regras:
- PDF, DOC, DOCX são SEMPRE documentos (laudos, receitas, pedidos). Nunca os coloque em exames.
- Imagens do mesmo exame têm nomes parecidos (mesmo prefixo ou mesma modalidade e região).
- Detecte modalidade pelo nome: RM/MRI/ressonancia→MR, RX/raio/radio/xray→XR, TC/tomografia/CT→CT, US/eco/ultrassom→US, PET→PET.
- Se um arquivo DICOM sem nome descritivo estiver sozinho, crie um exame genérico para ele.
- Se não houver padrão claro, prefira criar grupos menores a colocar tudo junto.

Retorne SOMENTE JSON válido, sem markdown, sem texto extra:
{{"exams":[{{"name":"Nome do Exame","modality":"MR","indices":[0,1]}},{{"name":"Outro Exame","modality":"XR","indices":[2]}}],"document_indices":[3]}}"""

    try:
        from groq import Groq as GroqClient
        client = GroqClient(api_key=groq_key)
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=512,
        )
        text = response.choices[0].message.content.strip()
        match = re.search(r'\{[\s\S]*\}', text)
        if match:
            result = json.loads(match.group())
            # Ensure all indices are accounted for — anything missing → documents
            accounted = set(result.get("document_indices", []))
            for exam in result.get("exams", []):
                accounted.update(exam.get("indices", []))
            missing = [f["index"] for f in file_infos if f["index"] not in accounted]
            if missing:
                result["document_indices"] = result.get("document_indices", []) + missing
            return result
    except Exception as e:
        print(f"[classify_uploaded_files] LLM error: {e}")

    return _heuristic_classify(file_infos)


def _heuristic_classify(file_infos: list) -> dict:
    """Fallback: groups by filename prefix when LLM is unavailable."""
    doc_indices = [f["index"] for f in file_infos if f["is_document"]]
    image_infos = [f for f in file_infos if not f["is_document"]]

    if not image_infos:
        return {"exams": [], "document_indices": doc_indices}

    groups: dict = {}
    for f in image_infos:
        base = re.split(r'[-_\s\d\.]+', f["filename"])[0].lower() or "exame"
        groups.setdefault(base, []).append(f["index"])

    exams = [
        {"name": prefix.capitalize(), "modality": "", "indices": indices}
        for prefix, indices in groups.items()
    ]
    return {"exams": exams, "document_indices": doc_indices}
