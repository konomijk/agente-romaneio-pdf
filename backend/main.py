import os
import io
import json
import base64
from pathlib import Path

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import StreamingResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from anthropic import Anthropic

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle


BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR.parent / "frontend"

app = FastAPI(title="Agente Romaneio")

if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


def get_anthropic_client() -> Anthropic:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="ANTHROPIC_API_KEY não configurada no servidor.",
        )
    return Anthropic(api_key=api_key)


# ---------- Modelos ----------

class Item(BaseModel):
    codigo: str = ""
    mercadoria: str = ""
    quantidade: str = ""
    custo: str = ""
    fornecedor: str = ""
    observacao: str = ""


class RomaneioData(BaseModel):
    empresa: str = "Romaneio"
    data: str = "-"
    itens: list[Item] = []


# ---------- Rotas de páginas ----------

@app.get("/")
def index():
    index_path = FRONTEND_DIR / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="Frontend não encontrado.")
    return FileResponse(str(index_path))


@app.get("/api/health")
def health():
    return {"status": "ok"}


# ---------- Extração via IA ----------

EXTRACTION_PROMPT = """Você está vendo a foto de um romaneio de compras manuscrito.
Extraia os dados em JSON, seguindo EXATAMENTE este formato, sem nenhum texto
antes ou depois do JSON:

{
  "empresa": "string",
  "data": "DD/MM/AAAA",
  "itens": [
    {
      "codigo": "string",
      "mercadoria": "string",
      "quantidade": "string",
      "custo": "string",
      "fornecedor": "string",
      "observacao": "string"
    }
  ]
}

Regras:
- Se um item estiver riscado com X (não comprado), use "-" nos campos
  quantidade, custo, fornecedor e observacao.
- Se a caligrafia estiver difícil de ler com certeza, faça sua melhor
  leitura e adicione um "*" no final do valor.
- Não invente itens que não estão na foto.
"""


@app.post("/api/extract")
async def extract(image: UploadFile = File(...)):
    if image.content_type not in ("image/jpeg", "image/png", "image/webp"):
        raise HTTPException(status_code=400, detail="Envie um arquivo de imagem (jpg, png ou webp).")

    conteudo = await image.read()
    if len(conteudo) > 15 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Imagem muito grande (máx. 15MB).")

    imagem_b64 = base64.standard_b64encode(conteudo).decode("utf-8")
    client = get_anthropic_client()

    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": image.content_type,
                            "data": imagem_b64,
                        },
                    },
                    {"type": "text", "text": EXTRACTION_PROMPT},
                ],
            }],
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Falha ao chamar o modelo: {exc}")

    texto = "".join(block.text for block in response.content if block.type == "text").strip()
    texto_limpo = texto.replace("```json", "").replace("```", "").strip()

    try:
        dados = json.loads(texto_limpo)
    except json.JSONDecodeError:
        raise HTTPException(status_code=502, detail="O modelo não retornou um JSON válido.")

    return JSONResponse(content=dados)


# ---------- Geração de PDF ----------

def montar_pdf(dados: RomaneioData) -> bytes:
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("TituloRomaneio", parent=styles["Title"], fontSize=16, spaceAfter=2)
    sub_style = ParagraphStyle("Sub", parent=styles["Normal"], fontSize=10, textColor=colors.grey)
    cell_style = ParagraphStyle("Cell", parent=styles["Normal"], fontSize=8, leading=10)

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        topMargin=1.5 * cm, bottomMargin=1.5 * cm,
        leftMargin=1.2 * cm, rightMargin=1.2 * cm,
    )
    story = []

    story.append(Paragraph(f"{dados.empresa} — Romaneio de Compras", title_style))
    story.append(Paragraph(f"Data: {dados.data}", sub_style))
    story.append(Spacer(1, 12))

    header = ["Cód.", "Mercadoria", "Qtde", "Custo (R$)", "Fornecedor", "Obs."]
    table_data = [header]
    for item in dados.itens:
        linha = [item.codigo, item.mercadoria, item.quantidade, item.custo, item.fornecedor, item.observacao]
        table_data.append([Paragraph(str(c) if c else "-", cell_style) for c in linha])

    col_widths = [1.6 * cm, 5.0 * cm, 1.8 * cm, 2.6 * cm, 3.8 * cm, 2.5 * cm]
    tabela = Table(table_data, colWidths=col_widths, repeatRows=1)
    tabela.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2c3e50")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#bdc3c7")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f4f6f7")]),
        ("ALIGN", (0, 1), (0, -1), "CENTER"),
        ("ALIGN", (2, 1), (3, -1), "CENTER"),
        ("ALIGN", (5, 1), (5, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(tabela)

    story.append(Spacer(1, 14))
    nota = Paragraph(
        "<b>Observações:</b> itens marcados com \"-\" foram riscados (não comprados). "
        "Valores marcados com * tiveram leitura incerta e devem ser conferidos com o original.",
        cell_style,
    )
    story.append(nota)

    doc.build(story)
    buffer.seek(0)
    return buffer.read()


@app.post("/api/pdf")
def gerar_pdf(dados: RomaneioData):
    pdf_bytes = montar_pdf(dados)
    nome_arquivo = "".join(c if c.isalnum() else "_" for c in dados.empresa).lower() or "romaneio"

    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="romaneio_{nome_arquivo}.pdf"'},
    )
