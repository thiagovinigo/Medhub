import os
from dotenv import load_dotenv
load_dotenv(dotenv_path="../.env")

from PIL import Image as PILImage
from agno.agent import Agent
from agno.models.groq import Groq
from agno.media import Image as AgnoImage
from agno.tools.tavily import TavilyTools
from textwrap import dedent

# Modelos LLaMA do Groq (Visão e Texto)
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

def preprocess_img(img_path):
    """Redimensiona a imagem e salva em formato temporário."""
    image = PILImage.open(img_path)
    width, height = image.size
    aspect_ratio = width / height
    img_width = 600
    img_height = int(img_width / aspect_ratio)
    resized_img = image.resize((img_width, img_height))

    temp_path = img_path + "_resized.png"
    resized_img.save(temp_path)

    return temp_path, resized_img

def format_res(res, return_thinking=False):
    res = res.strip()
    if return_thinking:
        res = res.replace("<think>", "[pensando...] ")
        res = res.replace("</think>", "\n---\n")
    else:
        if "</think>" in res:
            res = res.split("</think>")[-1].strip()
    res = res.replace("```","")
    return res

def process_image(file_path: str):
    """Executa o pipeline completo: processamento, análise e pesquisa usando Groq."""
    
    # Valida as chaves de API
    groq_key = os.environ.get("GROQ_API_KEY")
    tavily_key = os.environ.get("TAVILY_API_KEY")
    
    if not groq_key:
        raise Exception("Chaves de API do Groq ausentes. O sistema precisa do Llama para rodar.")
        
    med_agent = Agent(
        name="Medical Image Agent",
        role="Especialista em imagens médicas",
        model=Groq(id=ID_MODEL_VISION),
        markdown=True
    )

    tools = []
    if tavily_key:
        tools.append(TavilyTools())

    research_agent = Agent(
        name="Researcher Agent",
        role="Pesquisador médico",
        instructions=dedent(
            """Você é um pesquisador médico responsável por buscar informações complementares sobre os achados identificados na imagem médica.
            Utilize ferramentas de busca (se ativas) para encontrar literatura médica recente, protocolos de tratamento padrão e avanços tecnológicos relevantes."""
        ),
        model=Groq(id=ID_MODEL_TEXT),
        tools=tools
    )

    temp_path, _ = preprocess_img(file_path)
    agno_img = AgnoImage(filepath=temp_path)

    # 1. Análise Médica
    res_med = med_agent.run(prompt_analysis, images=[agno_img])
    analysis_text = format_res(res_med.content)

    # 2. Pesquisa Complementar
    prompt_search = prompt_search_template.format(analysis_text)
    res_search = research_agent.run(prompt_search)
    research_text = format_res(res_search.content)
    
    # Limpeza
    if os.path.exists(temp_path):
        os.remove(temp_path)

    return {
        "analysis": analysis_text,
        "research": research_text
    }
