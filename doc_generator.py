from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from datetime import datetime


# ── Brand colours ─────────────────────────────────────────────────────────────
NAVY  = RGBColor(15, 27, 51)    # #0F1B33
GOLD  = RGBColor(212, 175, 55)  # #D4AF37
GREY  = RGBColor(180, 180, 180)


def generate_doc(data: dict) -> str:
    doc = Document()

    # Default font
    style = doc.styles['Normal']
    style.font.name = 'Calibri'
    style.font.size = Pt(11)

    # ── Helpers ──────────────────────────────────────────────────────────────
    def heading(text: str, level: int = 1, color: RGBColor = NAVY):
        p = doc.add_heading(text, level=level)
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        for run in p.runs:
            run.font.color.rgb = color
        return p

    def field(label: str, value):
        p = doc.add_paragraph()
        run = p.add_run(f"{label}: ")
        run.bold = True
        run.font.size = Pt(11)
        p.add_run(str(value)).font.size = Pt(11)
        return p

    def divider():
        p = doc.add_paragraph("━" * 50)
        p.runs[0].font.color.rgb = GREY
        p.runs[0].font.size = Pt(9)

    # ── Header ───────────────────────────────────────────────────────────────
    title = doc.add_heading('NASIHA — BUYURTMA SHAKLI', 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for run in title.runs:
        run.font.color.rgb = NAVY

    sub = doc.add_paragraph('Mehr va Tarbiya Olami')
    sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sub.runs[0].font.color.rgb = GOLD
    sub.runs[0].font.size = Pt(12)

    doc.add_paragraph()

    # ── Client info ──────────────────────────────────────────────────────────
    heading("MIJOZ MA'LUMOTLARI", level=1)
    field("Ism va Familiya",  data.get('client_name', ''))
    field("Telefon",          data.get('client_phone', ''))
    field("Manzil",           data.get('client_city', ''))
    field("Buyurtma sanasi",  datetime.now().strftime("%d.%m.%Y %H:%M"))
    field("Bolalar soni",     len(data.get('children', [])))
    divider()

    # ── Children ─────────────────────────────────────────────────────────────
    for i, child in enumerate(data.get('children', []), 1):
        heading(f"{i}-BOLA: {child.get('name', '').upper()}", level=1)
        field("Ismi",          child.get('name', ''))
        field("Yoshi",         child.get('age', ''))
        field("Jinsi",         child.get('gender', ''))
        field("Asosiy xarakteri", child.get('character', ''))

        doc.add_paragraph()
        p = doc.add_paragraph()
        p.add_run("Muammo tavsifi:").bold = True
        doc.add_paragraph(child.get('problem', ''))

        field("Qahramon turi",   child.get('hero', ''))
        field("Rasmlar soni",    f"{len(child.get('photos', []))} ta")
        field("Ishtirokchi rasmlari", f"{len(child.get('participant_photos', []))} ta")
        divider()

    # ── Extra notes ──────────────────────────────────────────────────────────
    notes = data.get('extra_notes', '')
    if notes and notes.lower() not in ("yo'q", "yoq", ""):
        heading("QO'SHIMCHA IZOHLAR", level=1)
        doc.add_paragraph(notes)
        divider()

    # ── Footer ───────────────────────────────────────────────────────────────
    doc.add_paragraph()
    footer = doc.add_paragraph("NASIHA — Bola qalbidagi yaxshilik uchun sehrli eshik. 💛")
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    footer.runs[0].font.color.rgb = GOLD
    footer.runs[0].font.size = Pt(10)

    # ── Save ─────────────────────────────────────────────────────────────────
    name_safe = data.get('client_name', 'Buyurtma').replace(' ', '_')
    path = f"/tmp/Buyurtma_{name_safe}.docx"
    doc.save(path)
    return path
