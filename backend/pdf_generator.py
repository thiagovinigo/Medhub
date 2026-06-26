import re
from datetime import datetime
from typing import Optional
from fpdf import FPDF
from markdown_it import MarkdownIt

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

    md = MarkdownIt()
    
    # Inject HTML color tags into the markdown headers to keep our CYAN color
    analysis_colored = re.sub(r'^(#{1,4})\s+(.*)$', r'\1 <font color="#06b6d4">\2</font>', analysis, flags=re.MULTILINE)
    research_colored = re.sub(r'^(#{1,4})\s+(.*)$', r'\1 <font color="#06b6d4">\2</font>', research, flags=re.MULTILINE)

    html_analysis = md.render(analysis_colored)
    
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*DARK)
    pdf.write_html(html_analysis)

    pdf.ln(4)
    pdf.set_draw_color(*CYAN)
    pdf.set_line_width(0.5)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.set_line_width(0.2)
    pdf.ln(6)
    
    html_research = md.render("## <font color=\"#06b6d4\">Pesquisa Acadêmica Relacionada</font>\n\n" + research_colored)
    pdf.write_html(html_research)

    return bytes(pdf.output())
