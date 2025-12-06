from reportlab.lib.pagesizes import landscape, A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm

OUT = 'PROJECT_SUMMARY_SLIDES.pdf'

slides = [
    {"title": "FITFINDER — Project Summary", "lines": [
        "One-line: Flask backend + static frontend for outfit generation and try-on.",
        "Optional Hugging Face integration; Pillow demo fallback."]},

    {"title": "Architecture", "lines": [
        "Flask app serving APIs under /api/* and static/ frontend.",
        "Image generation: HF Inference API (if token) or Pillow demo images.",
        "Try-on: simple Pillow compositing; uploads saved to uploads/."]},

    {"title": "Key Endpoints", "lines": [
        "GET /api/health — status + HF configured flag.",
        "POST /api/generate-outfit — JSON: scene, style, gender, custom_prompt.",
        "POST /api/tryon — multipart: person_image + cloth_image.",
        "POST /api/contact — stores submissions to contacts.json."]},

    {"title": "Deployment & Runtime", "lines": [
        "Procfile: gunicorn -w 2 -b 0.0.0.0:$PORT app:app (Railway/Heroku).",
        "Set HF_API_TOKEN in environment to enable real AI generation.",
        "Generated images saved to generated_outfits/ (consider S3 for prod)."]},

    {"title": "Security & Next Steps", "lines": [
        "Do NOT commit API tokens; use platform env vars or secrets.",
        "Next: persistent storage, DB for metadata, better try-on model, auth for admin."]},

    {"title": "Where to find things", "lines": [
        "app.py, app_clean.py — backend source.",
        "PROJECT_REPORT.md / PROJECT_REPORT.pdf — full documentation and annotated app.py.",
        "Generated files: generated_outfits/, uploads/."]}
]


def draw_slide(c, title, lines):
    w, h = landscape(A4)
    c.setFont('Helvetica-Bold', 28)
    c.drawCentredString(w/2, h - 2*cm, title)
    c.setFont('Helvetica', 14)
    y = h - 3.5*cm
    for line in lines:
        c.drawString(2*cm, y, u"• " + line)
        y -= 1*cm


if __name__ == '__main__':
    c = canvas.Canvas(OUT, pagesize=landscape(A4))
    for s in slides:
        draw_slide(c, s['title'], s['lines'])
        c.showPage()
    c.save()
    print('Wrote', OUT)
