import re
from datetime import datetime
from typing import Optional
from fpdf import FPDF

CYAN = (6, 182, 212)
DARK = (20, 20, 30)
GRAY = (120, 120, 130)
LIGHT_GRAY = (200, 200, 210)


class MedAIPDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 16)
        self.set_text_color(*CYAN)
        self.cell(120, 10, "MedAI Diagnostics", align="L")
        self.set_font("Helvetica", "", 8)
        self.set_text_color(*GRAY)
        self.cell(0, 10, f"Gerado em {datetime.now().strftime('%d/%m/%Y as %H:%M')}", align="R")
        self.ln(2)
        self.set_draw_color(*CYAN)
        self.set_line_width(0.5)
        self.line(10, self.get_y(), 200, self.get_y())
        self.set_line_width(0.2)
        self.ln(6)

    def footer(self):
        self.set_y(-14)
        self.set_font("Helvetica", "I", 7)
        self.set_text_color(*GRAY)
        self.cell(0, 5, "Este laudo e gerado por inteligencia artificial e nao substitui avaliacao medica profissional.", align="C")
        self.ln(3)
        self.set_font("Helvetica", "", 7)
        self.cell(0, 5, f"Pagina {self.page_no()}", align="C")


def _strip_inline(text: str) -> str:
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'\*(.*?)\*', r'\1', text)
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    text = re.sub(r'`([^`]+)`', r'\1', text)
    # Remove non-latin1 characters to avoid fpdf encoding issues
    return text.encode('latin-1', errors='replace').decode('latin-1')


def _render_markdown(pdf: FPDF, text: str):
    for line in text.split("\n"):
        line = line.rstrip()
        if not line:
            pdf.ln(2)
            continue

        if line.startswith("### "):
            pdf.set_font("Helvetica", "B", 11)
            pdf.set_text_color(*CYAN)
            pdf.ln(3)
            pdf.multi_cell(0, 6, _strip_inline(line[4:]))
            pdf.set_draw_color(*LIGHT_GRAY)
            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(3)
            continue

        if line.startswith("## "):
            pdf.set_font("Helvetica", "B", 13)
            pdf.set_text_color(*CYAN)
            pdf.ln(4)
            pdf.multi_cell(0, 7, _strip_inline(line[3:]))
            pdf.ln(2)
            continue

        if re.match(r'^[\-\*] ', line):
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(*DARK)
            pdf.set_x(16)
            pdf.multi_cell(184, 5, "- " + _strip_inline(line[2:]))
            continue

        if re.match(r'^\s{2,}[\-\*] ', line):
            content = re.sub(r'^\s+[\-\*] ', '', line)
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(*GRAY)
            pdf.set_x(22)
            pdf.multi_cell(178, 5, "  " + _strip_inline(content))
            continue

        content = _strip_inline(line)
        if content:
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(*DARK)
            pdf.multi_cell(0, 5.5, content)


def generate_report_pdf(
    analysis: str,
    research: str,
    metadata: Optional[dict] = None,
) -> bytes:
    pdf = MedAIPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()
    pdf.set_margins(10, 10, 10)

    if metadata:
        fields = [
            ("Modalidade", metadata.get("modality")),
            ("Paciente", metadata.get("patient_name")),
            ("Data do exame", metadata.get("study_date")),
        ]
        visible = [(k, v) for k, v in fields if v]
        if visible:
            pdf.set_font("Helvetica", "", 8)
            pdf.set_text_color(*GRAY)
            pdf.cell(0, 5, "   |   ".join(f"{k}: {v}" for k, v in visible))
            pdf.ln(8)

    _render_markdown(pdf, analysis)

    pdf.ln(4)
    pdf.set_draw_color(*CYAN)
    pdf.set_line_width(0.5)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.set_line_width(0.2)
    pdf.ln(6)
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(*CYAN)
    pdf.cell(0, 7, "Pesquisa Academica Relacionada")
    pdf.ln(9)

    _render_markdown(pdf, research)

    return bytes(pdf.output())
