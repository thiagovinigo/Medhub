import os
import math
import tempfile
from typing import List
from datetime import date as date_type
from textwrap import dedent
from PIL import Image as PILImage
from agno.agent import Agent
from agno.models.groq import Groq
from agno.media import Image as AgnoImage
from agno.tools.tavily import TavilyTools

ID_MODEL_VISION = "meta-llama/llama-4-scout-17b-16e-instruct"
ID_MODEL_TEXT = "llama-3.3-70b-versatile"

SPECIALTY_LABELS = {
    "spine":     "neurorradiologista especializado em coluna vertebral",
    "neuro":     "neurorradiologista especializado em neuroimagem craniana",
    "thorax":    "radiologista especializado em tórax e sistema respiratório",
    "abdomen":   "radiologista especializado em abdome e pelve",
    "msk":       "radiologista musculoesquelético e ortopédico",
    "cardio":    "cardiologista e radiologista cardiovascular",
    "endocrino": "endocrinologista especializado em glândulas endócrinas e metabolismo",
    "onco":      "oncologista especializado em diagnóstico por imagem e estadiamento tumoral",
    "breast":    "radiologista especializado em mamografia e diagnóstico de mama (BI-RADS)",
    "nutri":     "nutricionista clínico especializado em metabolismo e saúde alimentar",
    "default":   "radiologista diagnóstico generalista",
}

# Extra instructions injected per specialty after the base prompt
SPECIALTY_INSTRUCTIONS = {
    "spine": dedent("""\
        Avalie sistematicamente: alinhamento vertebral (lordose/cifose), altura dos discos intervertebrais,
        sinais de hérnia discal (protrusão/extrusão/sequestro), estenose de canal e foraminal,
        compressão radicular ou medular, sinais de mielopatia, alterações degenerativas (espondilartrose,
        osteófitos), fraturas ou instabilidades. Informe o nível vertebral afetado (ex: C5-C6, L4-L5)."""),

    "neuro": dedent("""\
        Avalie sistematicamente: parênquima cerebral (sinal, volume, sulcos), ventrículos (tamanho, simetria),
        estruturas da linha média (desvio?), fossa posterior (cerebelo, tronco encefálico),
        substância branca (hiperintensidades, leucoaraiose), estruturas vasculares (aneurismas, malformações),
        sinais de AVC isquêmico/hemorrágico, tumores (primários ou metastáticos), hidrocefalia, edema."""),

    "thorax": dedent("""\
        Avalie sistematicamente: campos pulmonares (consolidações, nódulos, massas, derrame, pneumotórax),
        padrão intersticial (reticular, em vidro fosco, crazy paving), hilos pulmonares, mediastino
        (alargamento, linfonodomegalias, timo), coração (área cardíaca, contornos), pleura, parede torácica.
        Para TC: classifique nódulos pelo Lung-RADS quando aplicável."""),

    "abdomen": dedent("""\
        Avalie sistematicamente: fígado (parênquima, lesões focais, ductos biliares), vesícula biliar,
        pâncreas (cabeça/corpo/cauda, ducto de Wirsung), baço, rins (parênquima, pelves, cálculos),
        adrenais, aorta e vasos, alças intestinais, linfonodos, ascite, pelve (bexiga, útero/ovários,
        próstata se visível). Classifique lesões hepáticas pelo LI-RADS quando aplicável."""),

    "msk": dedent("""\
        Avalie sistematicamente: alinhamento e integridade óssea (fraturas, luxações, deformidades),
        espaços articulares (estreitamento, derrame), cartilagem (espessura, irregularidades),
        tendões e ligamentos (rupturas parciais/totais, entesofitose), meniscos (quando joelho),
        manguito rotador (quando ombro), tecidos moles periarticulares (edema, bursite, cistos).
        Informe grau de artrose (Kellgren-Lawrence se aplicável)."""),

    "cardio": dedent("""\
        Avalie sistematicamente: câmaras cardíacas (tamanho, hipertrofia), valvas (calcificações, morfologia),
        pericárdio (espessamento, derrame), aorta ascendente/arco/descendente (dilatação, dissecção),
        coronárias (se CT coronária: escore de cálcio, estenoses), perfusão miocárdica (se cintilografia),
        fração de ejeção estimada, sinais de disfunção sistólica/diastólica."""),

    "endocrino": dedent("""\
        TIREOIDE: avalie volume global, ecotextura (homogênea/heterogênea), nódulos (número, tamanho,
        composição, ecogenicidade, margens, calcificações — classifique por TIRADS 1-5),
        vascularização ao Doppler, linfonodos cervicais.
        ADRENAIS: tamanho, morfologia, density em TC (< 10 HU = adenoma lipídico rico),
        massas (feocromocitoma, carcinoma, metástase).
        HIPÓFISE: volume, sinal, microadenomas (< 10 mm), macroadenomas, compressão quiasmática.
        PÂNCREAS ENDÓCRINO: insulinomas, gastrinomas — lesões hipervascularizadas.
        Correlacione sempre com perfil hormonal e metabólico disponível."""),

    "onco": dedent("""\
        Para cada lesão suspeita avalie: localização anatômica precisa, dimensões (3 eixos),
        características morfológicas (margens espiculadas/lobuladas/lisas, densidade/sinal,
        componente necrótico, calcificações), invasão de estruturas adjacentes,
        linfonodomegalias (tamanho, localização, morfologia suspeita > 10 mm / razão córtex/hilo),
        lesões à distância (metástases hepáticas, pulmonares, ósseas, adrenais).
        Aplique critérios RECIST 1.1 quando disponível medida prévia.
        Estadie conforme TNM da lesão primária identificada.
        Diferencie critérios de malignidade vs. benignidade. Destaque achados urgentes."""),

    "breast": dedent("""\
        Avalie densidade mamária (BI-RADS A/B/C/D). Para cada achado: localização (quadrante + distância
        do mamilo), tamanho, forma (oval/redondo/irregular), margens (circunscritas/obscurecidas/
        microlobuladas/indistintas/espiculadas), densidade (gordurosa/iso/hiperDensa), calcificações
        (morfologia: tipicamente benignas vs. suspeitas vs. altamente suspeitas; distribuição).
        Distorções arquiteturais, assimetrias. Classifique cada achado com categoria BI-RADS 0-6
        e recomende conduta correspondente."""),

    "nutri": dedent("""\
        Avalie o estado nutricional a partir dos exames fornecidos.
        Perfil lipídico: colesterol total, LDL, HDL, triglicerídeos (valores de referência e risco cardiovascular).
        Glicemia: glicemia jejum, HbA1c, curva glicêmica — rastreio de DM2 e resistência insulínica.
        Hemograma: anemia (hemoglobina, ferritina, VCM), leucograma.
        Função renal: creatinina, ureia, TFG estimada.
        Função hepática: TGO, TGP, GGT — hepatite gordurosa (DHGNA) associada à obesidade.
        Vitaminas e minerais: vitamina D, B12, ferro, zinco, magnésio se disponíveis.
        Correlacione IMC, peso e histórico clínico com os achados laboratoriais.
        Classifique o risco metabólico geral (baixo / moderado / alto)."""),

    "default": "Realize uma análise sistemática e abrangente de todos os achados visíveis na imagem.",
}


SPECIALTY_SUGGESTION_INSTRUCTIONS = {
    "spine": dedent("""\
        Fisioterapia: protocolo indicado (McKenzie / estabilização segmentar / RPG / tração), frequência e duração estimada.
        Medicamentos: AINEs, relaxantes musculares, corticoides (oral ou epidural) com posologia e prazo.
        Cirurgia: critérios objetivos para indicação (déficit neurológico progressivo, falha em 6 sem. de conservador, síndrome da cauda equina).
        Orientações posturais e de atividade física: restrições imediatas, exercícios liberados.
        Encaminhamento urgente: indique quando e para qual especialidade (ortopedia, neurocirurgia).
        Prazo de reavaliação e critérios para escalonamento do tratamento."""),

    "msk": dedent("""\
        Fisioterapia / reabilitação: protocolo específico por articulação e lesão (ex: fortalecimento quadríceps pós-LCA, protocolo RICE).
        Imobilização/órtese: tipo, duração e carga permitida.
        Medicamentos: AINEs, infiltração corticoide intra-articular (critérios e técnica).
        Cirurgia: critérios objetivos (ruptura completa, instabilidade grau III, falha conservadora em X semanas).
        Retorno esportivo/laboral: critérios funcionais e cronograma estimado.
        Prazo de reavaliação e controle de imagem sugerido."""),

    "thorax": dedent("""\
        Nódulo pulmonar: conduta por tamanho e risco (Fleischner Society / Lung-RADS) — seguimento com TC, PET-CT ou biópsia.
        Pneumonia: antibioticoterapia empírica (esquema, via, duração) com base no contexto clínico e gravidade (CURB-65).
        Derrame pleural: toracocentese diagnóstica/terapêutica, critérios (Light).
        Investigação oncológica: indicação de biópsia (broncoscopia, EBUS, CT-guiada), estadiamento.
        Internação vs. ambulatório: critérios de hospitalização urgente.
        Prazo de controle radiológico e seguimento ambulatorial."""),

    "neuro": dedent("""\
        AVC isquêmico: janela terapêutica para trombolise IV (≤4,5h) e trombectomia mecânica (≤24h), contraindicações absolutas.
        Tumor cerebral: indicação de biópsia estereotáxica ou ressecção, radioterapia/quimioterapia adjuvante.
        Epilepsia: ajuste ou início de anticonvulsivante (droga, dose, titulação).
        Cefaleia: tratamento abortivo vs. profilático, critérios de neuroimagem urgente (red flags).
        Encaminhamento urgente: herniação transtentorial, HSAE, hidrocefalia aguda, meningite.
        Prazo de reavaliação neurológica e critérios de internação."""),

    "abdomen": dedent("""\
        Colelitíase/colecistite: colecistectomia eletiva vs. urgente (critérios de Tokyo Guidelines).
        Lesão hepática: conduta por LI-RADS (seguimento, biópsia, ablação, ressecção).
        Nefrolitíase: tratamento expectante (≤4mm), LECO, ureteroscopia ou nefrolitotripsia (critérios).
        Apendicite aguda: escore de Alvarado, cirurgia vs. antibioticoterapia.
        Internação imediata: peritonite, obstrução intestinal, isquemia mesentérica.
        Prazo de retorno, controle de imagem e exames complementares sugeridos."""),

    "cardio": dedent("""\
        Risco cardiovascular: escore de Framingham/ESC, escore de cálcio coronário (Agatston) — meta de LDL e indicação de estatina.
        Doença arterial coronariana: terapia médica otimizada (DAPT, BB, IECA/BRA, estatina) vs. ICP vs. CABG (critérios SYNTAX/HEART).
        Insuficiência cardíaca: IECA/BRA/ARNI, BB, MRA, SGLT2i — doses-alvo e titulação.
        Valvopatia: periodicidade do ecocardiograma de controle, timing de intervenção (critérios AHA/ESC).
        Urgência: IAMCSST → ativação de hemodinâmica; arritmia instável → cardioversão; tromboembolismo → anticoagulação.
        Metas de controle: PA, FC, LDL, HbA1c — prazos de reavaliação."""),

    "endocrino": dedent("""\
        Nódulo tireoidiano: conduta por TIRADS (1-2: rotina, 3: US em 1-2 anos, 4-5: PAAF, critérios de punção por tamanho).
        Hipotireoidismo: levotiroxina — dose inicial por peso (1,6 µg/kg/dia), titulação pelo TSH.
        Diabetes mellitus: escalonamento terapêutico (metformina → GLP-1/SGLT2 → insulina), metas de HbA1c por perfil de risco.
        Síndrome metabólica: intervenção em estilo de vida + farmacoterapia (estatina, anti-hipertensivo, metformina).
        Nódulo adrenal: investigação funcional (cortisol, aldosterona, metanefrinas), critérios cirúrgicos (>4cm ou crescimento >1cm/ano).
        Prazo de retorno e exames de controle hormonal."""),

    "nutri": dedent("""\
        Plano alimentar: calorias-alvo por IMC/objetivo, distribuição de macronutrientes (PTN g/kg, CHO %, LIP %).
        Dislipidemia: redução de gordura saturada (<7% VET), aumento de fibras solúveis (≥25g/dia), ômega-3.
        Resistência insulínica / DM2: índice glicêmico baixo, fracionamento de refeições (5-6x/dia), controle de carga glicêmica.
        Suplementação indicada: vitamina D (dose terapêutica se deficiente), B12, ferro quelato, magnésio (doses e duração).
        Atividade física complementar: tipo (aeróbico + resistência), frequência mínima, progressão.
        Prazo de retorno e exames de controle (colesterol, glicemia, vitaminas)."""),

    "breast": dedent("""\
        Conduta por categoria BI-RADS:
          0 → complementar (US ou mamografia adicional);
          1-2 → rastreamento anual de rotina;
          3 → US de controle em 6 meses (2 anos de seguimento para reclassificação);
          4A/4B/4C/5 → core biopsy guiada por US ou estereotaxia;
          6 → encaminhamento oncologia para planejamento terapêutico.
        Biópsia: tipo (core needle vs. VABB), guia de imagem preferencial, laboratório de anatomopatologia.
        Rastreamento genético: indicação de BRCA1/2 (critérios de risco familiar).
        Prazo de resultado e próximo passo conforme laudo AP."""),

    "onco": dedent("""\
        Estadiamento TNM completo com implicações prognósticas e sobrevida estimada.
        Protocolo de tratamento: intenção (curativa vs. paliativa), modalidades (cirurgia, QT, RT, imunoterapia, terapia-alvo).
        Biópsia / rebiópsia: indicação (progressão, resistência), local ideal, análise molecular (IHQ, FISH, NGS/painéis).
        Avaliação de resposta: critérios RECIST 1.1 (tumores sólidos) ou iRECIST (imunoterapia) — timing de reavaliação.
        Discussão multidisciplinar: tumor board, quais especialidades acionar (oncologia clínica, radioterapia, cirurgia oncológica).
        Cuidados de suporte: antieméticos, G-CSF, analgesia, suporte nutricional oncológico."""),

    "default": dedent("""\
        Exames complementares imediatos: indique os 2-3 mais relevantes para confirmar o diagnóstico.
        Tratamento empírico: se indicado, droga, dose e via de administração.
        Internação vs. ambulatório: critérios objetivos para hospitalização urgente.
        Encaminhamento especializado: qual especialidade, caráter (urgente em 24-48h / eletivo em X semanas).
        Prazo de retorno e critérios de reavaliação ou escalonamento."""),
}


def detect_specialty(modality: str, exam_name: str) -> str:
    n = (exam_name or "").lower()
    m = (modality or "").lower()

    # Nutrition — explicit dietary/lab terms
    if any(x in n for x in ["nutri", "nutrição", "nutricion", "dietétic",
                              "perfil lipídico", "colesterol", "triglicéride", "trigliceride",
                              "glicemia jejum", "curva glicêmica", "hemograma completo",
                              "exames de sangue", "hba1c", "vitamina d", "vitamina b12"]):
        return "nutri"

    # Breast — before msk to avoid confusion
    if any(x in n for x in ["mama", "mamografia", "mastografia", "mamária", "breast"]):
        return "breast"

    # Oncology — explicit keywords
    if any(x in n for x in ["tumor", "neoplasia", "carcinoma", "metástase", "metastase",
                              "sarcoma", "linfoma", "câncer", "cancer", "oncolog",
                              "estadiam", "pet", "cintilografia oncológica"]):
        return "onco"
    if m == "pet":
        return "onco"

    # Endocrinology
    if any(x in n for x in ["tireoide", "tireóide", "paratireoide", "paratireóide",
                              "adrenal", "suprarrenal", "hipófise", "hipofise",
                              "glândula", "glandula", "endócrin", "endocrin",
                              "hashimoto", "graves", "insulinom"]):
        return "endocrino"

    # Spine
    if any(x in n for x in ["coluna", "cervical", "lombar", "torácica", "vertebr",
                              "disco", "sacro", "cóccix", "coccix", "espondilose"]):
        return "spine"

    # Neuro / cranial
    if any(x in n for x in ["crânio", "cranio", "cerebro", "cérebro", "encéfalo",
                              "encefalo", "neuro", "brain", "hipocampo", "seio",
                              "órbita", "orbita", "sela"]):
        return "neuro"

    # Thorax
    if any(x in n for x in ["tórax", "torax", "pulmão", "pulmao", "pulmonar",
                              "chest", "pleural", "brônquio", "bronquio", "mediastino"]):
        return "thorax"

    # Cardio
    if any(x in n for x in ["coração", "coracao", "cardíaco", "cardiaco",
                              "aorta", "coronária", "coronaria", "ecocardiograma",
                              "angiografia"]):
        return "cardio"

    # Abdomen / pelvis
    if any(x in n for x in ["abdome", "abdomen", "fígado", "figado", "hepático",
                              "hepatico", "renal", "rim", "pélvis", "pelve",
                              "vesícula", "vesicula", "pâncreas", "pancreas",
                              "bexiga", "prostata", "próstata", "útero", "utero",
                              "ovário", "ovario", "retroperitôni"]):
        return "abdomen"

    # Musculoskeletal / orthopedic
    if any(x in n for x in ["joelho", "ombro", "quadril", "tornozelo", "punho",
                              "osso", "articulação", "articulacao", "membro",
                              "fêmur", "femur", "tíbia", "tibia", "fíbula",
                              "fibula", "úmero", "umero", "cotovelo", "pé ",
                              "mão ", "dedo", "escápula", "escapula", "clavícula",
                              "manguito", "menisco"]):
        return "msk"

    return "default"


def _calculate_age(birth_date_str: str) -> int:
    if not birth_date_str:
        return 0
    try:
        birth = date_type.fromisoformat(birth_date_str)
        return (date_type.today() - birth).days // 365
    except Exception:
        return 0


def _bmi(weight_kg, height_cm) -> str:
    try:
        bmi = float(weight_kg) / ((float(height_cm) / 100) ** 2)
        return f"{bmi:.1f}"
    except Exception:
        return "N/A"


def build_patient_context(p: dict, documents: list = None) -> str:
    lines = []
    name = p.get("name", "")
    age = _calculate_age(p.get("birth_date", ""))
    sex_map = {"M": "Masculino", "F": "Feminino", "O": "Outro"}
    sex = sex_map.get(p.get("sex", ""), "")

    header = f"Paciente: {name}" if name else "Paciente: não informado"
    if age:
        header += f", {age} anos"
    if sex:
        header += f", {sex}"
    lines.append(header)

    w, h = p.get("weight_kg"), p.get("height_cm")
    metrics = []
    if w:
        metrics.append(f"Peso: {w} kg")
    if h:
        metrics.append(f"Altura: {h} cm")
    if w and h:
        metrics.append(f"IMC: {_bmi(w, h)}")
    if metrics:
        lines.append(" | ".join(metrics))

    raw_conds = p.get("conditions", [])
    conditions = [c if isinstance(c, str) else c.get("condition", "") for c in raw_conds if c]
    conditions = [c for c in conditions if c]
    lines.append("Condições pré-existentes: " + (", ".join(conditions) if conditions else "Nenhuma informada"))

    complaint = (p.get("chief_complaint") or "").strip()
    if complaint:
        lines.append(f"Queixa principal: {complaint}")

    history = (p.get("clinical_history") or "").strip()
    if history:
        lines.append(f"Histórico clínico: {history}")

    if documents:
        lines.append("\n--- DOCUMENTOS CLÍNICOS ANEXADOS ---")
        for doc in documents:
            lines.append(f"\n[{doc['name']}]\n{doc['text']}")

    return "\n".join(lines)


def _convert_to_viewable(filepath: str) -> str:
    if not filepath.lower().endswith(".dcm"):
        return filepath
    import pydicom
    import numpy as np
    ds = pydicom.dcmread(filepath)
    arr = ds.pixel_array.astype(np.float64)
    slope = float(getattr(ds, "RescaleSlope", 1))
    intercept = float(getattr(ds, "RescaleIntercept", 0))
    arr = arr * slope + intercept
    if arr.ndim == 3 and arr.shape[0] < arr.shape[1]:
        arr = arr[arr.shape[0] // 2]
    pmin, pmax = arr.min(), arr.max()
    if pmax > pmin:
        arr = (arr - pmin) / (pmax - pmin) * 255
    arr = arr.astype("uint8")
    img = PILImage.fromarray(arr)
    if img.mode not in ("L", "RGB"):
        img = img.convert("RGB")
    out = filepath + "_view.png"
    img.save(out)
    return out


def select_frames(paths: List[str], max_n: int = 9) -> List[str]:
    if len(paths) <= max_n:
        return paths
    return [paths[int(i * len(paths) / max_n)] for i in range(max_n)]


def build_grid(image_paths: List[str], cols: int = 3, thumb: int = 280) -> str:
    images = []
    for p in image_paths:
        try:
            img = PILImage.open(p).convert("RGB").resize((thumb, thumb))
            images.append(img)
        except Exception:
            pass
    if not images:
        raise ValueError("Nenhuma imagem válida para montar o grid.")
    rows = math.ceil(len(images) / cols)
    grid = PILImage.new("RGB", (cols * thumb, rows * thumb), color=20)
    for i, img in enumerate(images):
        grid.paste(img, ((i % cols) * thumb, (i // cols) * thumb))
    out = tempfile.mktemp(suffix="_grid.jpg")
    grid.save(out, "JPEG", quality=85)
    return out


EXAM_PROMPT = """\
Você é um {specialty_label}.
Analise as imagens do exame abaixo e responda em português.
Forneça o resultado direto, sem texto de apresentação ou encerramento.
Use EXATAMENTE as seções com headers ## conforme mostrado abaixo.

CONTEXTO DO PACIENTE:
{patient_context}

{doc_summary_section}
EXAME:
Nome: {exam_name} | Modalidade: {modality} | Data: {exam_date}
Total de imagens na série: {total_images} | Cortes apresentados neste grid: {shown_frames}

DIRETRIZES ESPECÍFICAS PARA ESTE ESPECIALISTA:
{specialty_instructions}

## Análise Técnica
 - Tipo de exame, modalidade, região anatômica e posicionamento.
 - Qualidade técnica (resolução, artefatos, cobertura da série).
 - Achados visuais sistemáticos e detalhados seguindo as diretrizes específicas acima.

## Correlação Clínica
 - Relacione cada achado com a queixa e o histórico clínico do paciente.
 - Identifique quais achados explicam ou contradizem os sintomas relatados.
 - Correlacione com documentos clínicos anexos, se houver.

## Diagnóstico Profissional
 - **Diagnóstico principal** com nível de confiança (alto / moderado / baixo) e justificativa clínica.
 - **Diagnósticos diferenciais** em ordem de probabilidade com critérios de exclusão de cada um.
 - **Achados críticos**: destaque qualquer achado urgente com grau de urgência (IMEDIATA / ALTA / MODERADA / ELETIVA).
 - **Raciocínio diagnóstico**: por que este diagnóstico prevalece sobre os diferenciais.
 - **Decisão sugerida pela IA**: se fosse o médico responsável, qual seria a próxima ação concreta (ex: solicitar RM com gadolínio em 48h, iniciar fisioterapia 3x/semana, encaminhar cirurgia eletiva em 30 dias).
 - CID-10 sugerido quando aplicável.

## Sugestão Médica
{suggestion_instructions}
 - Justifique cada recomendação com base nos achados específicos deste caso.
 - Indique prazo de reavaliação e critérios para escalonamento do tratamento.

## Diagnóstico em Linguagem Simples
 - Explique os achados em linguagem clara e acessível ao paciente.
 - Evite jargão médico; use analogias quando necessário.
 - Relacione os resultados com os sintomas que o paciente relatou.
"""

CONSOLIDATION_PROMPT = """\
Você é um médico especialista em diagnóstico multimodal.
Baseado nas análises individuais abaixo, produza um laudo consolidado integrado.
Forneça o resultado direto, sem texto de apresentação ou encerramento.
Use EXATAMENTE as seções com headers ## conforme mostrado abaixo.

CONTEXTO DO PACIENTE:
{patient_context}

{doc_summary_section}
ANÁLISES DOS EXAMES:
{analyses}

## Análise Integrada
 - Correlacione os achados de todos os exames e documentos clínicos.
 - Identifique padrões consistentes e discrepâncias entre os exames.
 - Resumo técnico dos achados mais relevantes de cada exame.

## Correlação Clínica
 - Relacione os achados integrados com a queixa e histórico clínico do paciente.
 - Identifique quais achados explicam os sintomas relatados.

## Diagnóstico Profissional
 - **Diagnóstico principal** baseado no conjunto de evidências com nível de confiança e justificativa.
 - **Diagnósticos diferenciais** consolidados com critérios de exclusão de cada um.
 - **Achados críticos** com grau de urgência (IMEDIATA / ALTA / MODERADA / ELETIVA).
 - **Raciocínio diagnóstico**: por que este diagnóstico prevalece considerando todos os exames.
 - **Decisão sugerida pela IA**: próxima ação concreta que o médico responsável deveria tomar.
 - CID-10 sugerido quando aplicável.

## Sugestão Médica
{suggestion_instructions}
 - Justifique cada recomendação com base nos achados deste caso específico.
 - Indique prazo de reavaliação e critérios para escalonamento do tratamento.

## Diagnóstico em Linguagem Simples
 - Resumo integrado em linguagem acessível para o paciente.
 - Explique os achados de forma clara, sem jargão médico.
"""


DOC_READER_PROMPT = """\
Você é um médico clínico especializado em interpretação de documentos médicos.
Analise os documentos clínicos abaixo e extraia as informações mais relevantes de forma estruturada.
Forneça o resultado direto, sem apresentação.

CONTEXTO DO PACIENTE:
{patient_context}

DOCUMENTOS RECEBIDOS:
{documents_text}

## Informações Extraídas dos Documentos
 - Diagnósticos já estabelecidos, hipóteses diagnósticas do médico solicitante.
 - Medicamentos prescritos (nome, dose, posologia).
 - Resultados laboratoriais (valor encontrado | referência | status: normal / alterado).
 - Procedimentos realizados ou solicitados.
 - Queixas e histórico relevante mencionados.

## Achados Críticos e Correlações
 - O que os documentos indicam que é MAIS IMPORTANTE para interpretar os exames de imagem.
 - Alertas: valores críticos, medicamentos de alto risco, diagnósticos que alteram a interpretação das imagens.
 - Discrepâncias ou informações que requerem atenção especial.
"""

SUGGESTION_PROMPTS = {
    "diet": dedent("""\
        Você é um nutricionista clínico. Com base nos achados clínicos abaixo, elabore um plano alimentar
        personalizado em português. Forneça o resultado direto, sem apresentação.

        ACHADOS CLÍNICOS:
        {analysis}

        PERFIL DO PACIENTE:
        {patient_context}

        ### Orientações Gerais
        ### Alimentos Recomendados
        ### Alimentos a Evitar
        ### Sugestão de Cardápio (3 dias)
        ### Observações Importantes
    """),
    "exercise": dedent("""\
        Você é um fisioterapeuta e educador físico. Com base nos achados clínicos abaixo, elabore um plano
        de exercícios e fisioterapia personalizado em português. Forneça o resultado direto, sem apresentação.

        ACHADOS CLÍNICOS:
        {analysis}

        PERFIL DO PACIENTE:
        {patient_context}

        ### Exercícios Recomendados
        ### Exercícios a Evitar
        ### Frequência e Intensidade Sugeridas
        ### Progressão do Programa
        ### Observações de Segurança
    """),
    "lifestyle": dedent("""\
        Você é um cardiologista preventivo. Com base nos achados clínicos abaixo, elabore recomendações de
        hábitos saudáveis em português. Forneça o resultado direto, sem apresentação.

        ACHADOS CLÍNICOS:
        {analysis}

        PERFIL DO PACIENTE:
        {patient_context}

        ### Mudanças de Estilo de Vida
        ### Atividade Física Sugerida
        ### Orientações Alimentares
        ### Monitoramento Recomendado
    """),
}

DOC_ANALYSIS_PROMPT = """\
Você é um {specialty_label}.
Analise TODOS os resultados e documentos clínicos do paciente abaixo com detalhamento completo.
Forneça o resultado direto, sem texto de apresentação ou encerramento.
Use EXATAMENTE as seções com headers ## conforme mostrado abaixo.

{patient_ctx}

DIRETRIZES ESPECÍFICAS PARA ESTE ESPECIALISTA:
{specialty_instructions}

REGRA CRÍTICA: Analise CADA parâmetro sem omitir nenhum valor laboratorial.
Para cada item indique: valor encontrado | valor de referência | ✅ Normal / ⚠️ Alterado ↑ / ⚠️ Alterado ↓

## Análise Detalhada
 - Liste cada documento com data e laboratório (se disponível).
 - Para cada grupo de exames (Hemograma, Perfil Lipídico, Glicemia, Função Renal, etc.):
   → Liste: Parâmetro | Resultado | Referência | Status
   → Após cada grupo, interprete clinicamente os achados daquele painel.
 - Destaque correlações entre parâmetros (ex: glicemia ↑ + triglicerídeos ↑ = risco metabólico).

## Correlação Clínica
 - Relacione os achados laboratoriais com os sintomas e queixas relatados pelo paciente.
 - Identifique quais resultados explicam ou contradizem os sintomas descritos.

## Diagnóstico Profissional
 - **Diagnóstico principal** com nível de confiança (alto / moderado / baixo) e justificativa clínica.
 - **Diagnósticos diferenciais** em ordem de probabilidade com critérios de exclusão.
 - **Achados críticos** com grau de urgência (IMEDIATA / ALTA / MODERADA / ELETIVA).
 - **Raciocínio diagnóstico**: por que este diagnóstico prevalece sobre os diferenciais.
 - **Decisão sugerida pela IA**: próxima ação concreta que o médico responsável deveria tomar.
 - CID-10 sugerido quando aplicável.

## Sugestão Médica
{suggestion_instructions}
 - Justifique cada recomendação com base nos resultados específicos deste caso.
 - Indique prazo de retorno e exames de controle sugeridos.

## Diagnóstico em Linguagem Simples
 - Resuma o significado dos resultados em linguagem simples e acessível.
 - Explique o que os valores alterados significam para a saúde do paciente.
 - Evite jargão médico; use analogias quando necessário.
"""


def analyze_documents(documents: list, patient_ctx: str) -> str:
    """
    Dedicated document reader agent: reads all PDFs/docs and returns a structured clinical summary
    that gets passed explicitly to image analysis agents.
    """
    groq_key = os.environ.get("GROQ_API_KEY")
    if not groq_key or not documents:
        return ""
    docs_text = "\n\n".join(
        f"[Documento: {d['name']}]\n{d['text']}" for d in documents if d.get("text")
    )
    if not docs_text.strip():
        return ""
    agent = Agent(
        name="Document-Reader-Agent",
        role="médico clínico especializado em interpretação de documentos médicos",
        model=Groq(id=ID_MODEL_TEXT),
        markdown=True,
    )
    result = agent.run(DOC_READER_PROMPT.format(
        patient_context=patient_ctx,
        documents_text=docs_text[:40000],
    ))
    return _fmt(result.content)


def generate_suggestion(specialty: str, analysis: str, suggestion_type: str, patient_context: str = "") -> str:
    groq_key = os.environ.get("GROQ_API_KEY")
    if not groq_key:
        raise Exception("GROQ_API_KEY não configurada.")
    prompt_tpl = SUGGESTION_PROMPTS.get(suggestion_type)
    if not prompt_tpl:
        raise Exception(f"Tipo de sugestão inválido: {suggestion_type}")
    prompt = prompt_tpl.format(analysis=analysis[:2000], patient_context=patient_context)
    agent = Agent(
        name="Suggestion-Agent",
        role=SPECIALTY_LABELS.get(specialty, SPECIALTY_LABELS["default"]),
        model=Groq(id=ID_MODEL_TEXT),
        markdown=True,
    )
    result = agent.run(prompt)
    return _fmt(result.content)


def _fmt(text: str) -> str:
    text = text.strip()
    if "</think>" in text:
        text = text.split("</think>")[-1].strip()
    return text.replace("```", "")


def process_case(case_payload: dict) -> dict:
    """
    case_payload = {
        "patient": { name, birth_date, sex, height_cm, weight_kg,
                     conditions, chief_complaint, clinical_history },
        "exams": [ { "name", "modality", "exam_date", "image_paths": [...] } ],
        "documents": [ { "name": str, "text": str } ]   # optional
    }
    """
    groq_key = os.environ.get("GROQ_API_KEY")
    tavily_key = os.environ.get("TAVILY_API_KEY")
    if not groq_key:
        raise Exception("GROQ_API_KEY não configurada.")

    documents = case_payload.get("documents") or []
    patient_ctx = build_patient_context(case_payload.get("patient", {}))
    temp_files: List[str] = []
    exam_analyses = []

    # ── Step 1: Document Reader Agent ────────────────────────────────────────
    doc_summary = ""
    if documents:
        doc_summary = analyze_documents(documents, patient_ctx)

    doc_summary_section = (
        f"SÍNTESE DOS DOCUMENTOS CLÍNICOS (gerada por agente leitor):\n{doc_summary}\n\n"
        if doc_summary else ""
    )

    try:
        for exam in case_payload.get("exams", []):
            raw_paths = exam.get("image_paths", [])
            if not raw_paths:
                continue

            viewable = []
            for p in raw_paths:
                v = _convert_to_viewable(p)
                viewable.append(v)
                if v != p:
                    temp_files.append(v)

            frames = select_frames(viewable, max_n=9)
            grid_path = build_grid(frames)
            temp_files.append(grid_path)

            specialty = detect_specialty(exam.get("modality", ""), exam.get("name", ""))
            prompt = EXAM_PROMPT.format(
                specialty_label=SPECIALTY_LABELS[specialty],
                specialty_instructions=SPECIALTY_INSTRUCTIONS[specialty],
                suggestion_instructions=SPECIALTY_SUGGESTION_INSTRUCTIONS.get(specialty, SPECIALTY_SUGGESTION_INSTRUCTIONS["default"]),
                patient_context=patient_ctx,
                doc_summary_section=doc_summary_section,
                exam_name=exam.get("name", "Exame sem nome"),
                modality=exam.get("modality", "N/A"),
                exam_date=exam.get("exam_date", "N/A"),
                total_images=len(raw_paths),
                shown_frames=len(frames),
            )

            agent = Agent(
                name=f"Agent-{specialty}",
                role=SPECIALTY_LABELS[specialty],
                model=Groq(id=ID_MODEL_VISION),
                markdown=True,
            )
            result = agent.run(prompt, images=[AgnoImage(filepath=grid_path)])
            exam_analyses.append({
                "exam": exam.get("name", ""),
                "modality": exam.get("modality", ""),
                "specialty": specialty,
                "analysis": _fmt(result.content),
            })

        if not exam_analyses:
            if not documents:
                raise Exception("Nenhum exame ou documento encontrado para analisar.")
            specialty_key = (case_payload.get("patient", {}).get("specialty") or "default")
            if specialty_key not in SPECIALTY_LABELS:
                specialty_key = "default"
            doc_prompt = DOC_ANALYSIS_PROMPT.format(
                specialty_label=SPECIALTY_LABELS[specialty_key],
                specialty_instructions=SPECIALTY_INSTRUCTIONS[specialty_key],
                suggestion_instructions=SPECIALTY_SUGGESTION_INSTRUCTIONS.get(specialty_key, SPECIALTY_SUGGESTION_INSTRUCTIONS["default"]),
                patient_ctx=patient_ctx + ("\n\n" + doc_summary_section if doc_summary_section else ""),
            )
            text_agent = Agent(
                name=f"Agent-{specialty_key}-text",
                role=SPECIALTY_LABELS[specialty_key],
                model=Groq(id=ID_MODEL_TEXT),
                markdown=True,
            )
            r = text_agent.run(doc_prompt)
            consolidated = _fmt(r.content)

        elif len(exam_analyses) == 1:
            consolidated = exam_analyses[0]["analysis"]
        else:
            analyses_block = "\n\n---\n\n".join(
                f"**{e['exam']} ({e['modality']})**\n{e['analysis']}" for e in exam_analyses
            )
            consolidator = Agent(
                name="Consolidation-Agent",
                role="Médico especialista em diagnóstico multimodal",
                model=Groq(id=ID_MODEL_TEXT),
                markdown=True,
            )
            primary_specialty = exam_analyses[0].get("specialty", "default")
            r = consolidator.run(CONSOLIDATION_PROMPT.format(
                patient_context=patient_ctx,
                doc_summary_section=doc_summary_section,
                analyses=analyses_block,
                suggestion_instructions=SPECIALTY_SUGGESTION_INSTRUCTIONS.get(primary_specialty, SPECIALTY_SUGGESTION_INSTRUCTIONS["default"]),
            ))
            consolidated = _fmt(r.content)

        tools = [TavilyTools()] if tavily_key else []
        researcher = Agent(
            name="Research-Agent",
            role="Pesquisador médico",
            instructions=dedent("""\
            Você é um pesquisador médico especializado em literatura clínica.
            Com base nos achados clínicos fornecidos, produza um diagnóstico consolidado com referências bibliográficas.
            Forneça o resultado direto, sem texto de apresentação ou encerramento.
            Use EXATAMENTE as seções com headers ## conforme mostrado abaixo.

            ## Diagnóstico Consolidado e Recomendações
             - Síntese diagnóstica integrando todos os achados.
             - Recomendações clínicas baseadas em evidências (exames complementares, conduta sugerida).
             - Indicações de acompanhamento ou encaminhamento especializado.

            ## Referências Bibliográficas
             - Forneça exatamente 8 referências confiáveis e recentes (preferencialmente últimos 10 anos).
             - Use revistas indexadas: NEJM, Lancet, JAMA, BMJ, UpToDate, diretrizes de sociedades médicas.
             - Formato: Autores. Título. Periódico. Ano;Vol(N):páginas. DOI quando disponível.
             - Inclua referências específicas para os achados mais relevantes do caso."""),
            model=Groq(id=ID_MODEL_TEXT),
            tools=tools,
        )
        rr = researcher.run(
            f"Achados clínicos para pesquisa bibliográfica:\n\n{consolidated[:4000]}"
        )
        research = _fmt(rr.content)

        return {
            "analysis": consolidated,
            "research": research,
            "exams_processed": len(exam_analyses),
        }

    finally:
        for p in temp_files:
            try:
                if os.path.exists(p):
                    os.remove(p)
            except Exception:
                pass
