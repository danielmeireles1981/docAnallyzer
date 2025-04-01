from fastapi import APIRouter, UploadFile, File, Depends, Body, Request, Form, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
import os

from app.database import SessionLocal
from app.models.models import Document, Embedding, Question
from app.services.pdf_processor import extract_text_from_pdf
from app.services.embedding_engine import embed_and_index, id_mapping, buscar_contexto
from app.services.llm_interface import gerar_resposta_gemini
from app.utils.reindex import reindex_all_documents

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# ----- Sessão de banco -----
async def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        await db.close()

from fastapi.responses import RedirectResponse

# Rota real do portal de entrada
@router.get("/inicio/", response_class=HTMLResponse)
async def portal_view(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# Redirecionamento automático da raiz `/` para `/inicio`
@router.get("/")
async def redirect_root():
    return RedirectResponse(url="/inicio")

# ----- Upload API (JSON) -----
@router.post("/upload/")
async def upload_pdf(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    save_path = f"data/pdfs/{file.filename}"
    with open(save_path, "wb") as f:
        f.write(await file.read())

    texto = extract_text_from_pdf(save_path)

    novo_doc = Document(
        nome_arquivo=file.filename,
        caminho_arquivo=save_path,
        texto_extraido=texto
    )
    db.add(novo_doc)
    await db.commit()
    await db.refresh(novo_doc)

    trechos_processados = embed_and_index(novo_doc.id, texto)

    for i in range(trechos_processados):
        trecho = id_mapping[-trechos_processados + i]["chunk"]
        embedding_obj = Embedding(
            documento_id=novo_doc.id,
            trecho_original=trecho,
            vetor_id_faiss=None
        )
        db.add(embedding_obj)

    await db.commit()

    return {
        "id": novo_doc.id,
        "nome": novo_doc.nome_arquivo,
        "trechos_indexados": trechos_processados,
        "trecho_inicial": texto[:500]
    }

# ----- Upload via Form -----
@router.get("/upload", response_class=HTMLResponse)
async def upload_form(request: Request):
    return templates.TemplateResponse("upload.html", {"request": request})

@router.post("/upload", response_class=HTMLResponse)
async def upload_pdf_form(request: Request, file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    save_path = f"data/pdfs/{file.filename}"
    with open(save_path, "wb") as f:
        f.write(await file.read())

    texto = extract_text_from_pdf(save_path)

    novo_doc = Document(
        nome_arquivo=file.filename,
        caminho_arquivo=save_path,
        texto_extraido=texto
    )
    db.add(novo_doc)
    await db.commit()
    await db.refresh(novo_doc)

    embed_and_index(novo_doc.id, texto)

    return templates.TemplateResponse("upload.html", {
        "request": request,
        "resultado": {
            "id": novo_doc.id,
            "nome": novo_doc.nome_arquivo,
            "trecho": texto[:500]
        }
    })

# ----- Formulário para perguntar -----
@router.get("/perguntar", response_class=HTMLResponse)
async def form_pergunta(request: Request):
    return templates.TemplateResponse("perguntar.html", {"request": request})

@router.post("/perguntar", response_class=HTMLResponse)
async def processar_pergunta(
    request: Request,
    documento_id: int = Form(...),
    pergunta: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    contexto = buscar_contexto(pergunta, documento_id, top_k=5)
    resposta = gerar_resposta_gemini(pergunta, contexto)

    nova_pergunta = Question(
        documento_id=documento_id,
        pergunta=pergunta,
        resposta=resposta,
        data=datetime.utcnow(),
        modelo_utilizado="gemini-1.5-flash",
        contexto_usado="\n\n".join(contexto)
    )
    db.add(nova_pergunta)
    await db.commit()

    return templates.TemplateResponse("perguntar.html", {
        "request": request,
        "documento_id": documento_id,
        "pergunta": pergunta,
        "resposta": resposta,
        "contexto": contexto
    })

# ----- API JSON para perguntar/responder -----
@router.post("/perguntar/")
async def perguntar(document_id: int = Body(...), pergunta: str = Body(...)):
    contexto = buscar_contexto(pergunta, documento_id=document_id, top_k=3)
    return {
        "pergunta": pergunta,
        "documento_id": document_id,
        "contexto_encontrado": contexto
    }

@router.post("/responder/")
async def responder(
    document_id: int = Body(...),
    pergunta: str = Body(...),
    db: AsyncSession = Depends(get_db)
):
    contexto = buscar_contexto(pergunta, document_id=document_id, top_k=5)
    resposta = gerar_resposta_gemini(pergunta, contexto)

    nova_pergunta = Question(
        documento_id=document_id,
        pergunta=pergunta,
        resposta=resposta,
        data=datetime.utcnow(),
        modelo_utilizado="gemini-1.5-flash",
        contexto_usado="\n\n".join(contexto)
    )
    db.add(nova_pergunta)
    await db.commit()
    await db.refresh(nova_pergunta)

    return {
        "pergunta_id": nova_pergunta.id,
        "documento_id": document_id,
        "pergunta": pergunta,
        "resposta": resposta,
        "contexto_utilizado": contexto
    }

# ----- Visualizar histórico via Template -----
@router.get("/historico/", response_class=HTMLResponse)
async def historico_view(
        request: Request,
        documento_id: int = Query(None),
        db: AsyncSession = Depends(get_db)
):
    if documento_id:
        result = await db.execute(
            select(Question).where(Question.documento_id == documento_id)
        )
    else:
        result = await db.execute(select(Question))

    perguntas = result.scalars().all()

    return templates.TemplateResponse("historico.html", {
        "request": request,
        "perguntas": perguntas
    })

# ----- Reindexa todos os documentos -----
@router.get("/reindexar/", response_class=HTMLResponse)
async def reindexar_interface(request: Request, db: AsyncSession = Depends(get_db)):
    total = reindex_all_documents()
    mensagem = f"✅ Reindexação completa! Total de trechos indexados: {total}"

    result = await db.execute(select(Question))
    perguntas = result.scalars().all()

    return templates.TemplateResponse("historico.html", {
        "request": request,
        "mensagem": mensagem,
        "perguntas": perguntas
    })


