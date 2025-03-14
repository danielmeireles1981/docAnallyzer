from fastapi import FastAPI, File, UploadFile, Form, HTTPException
import pdfplumber
import os
import shutil
import requests
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Configuração do CORS para permitir chamadas do frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permitir requisições de qualquer origem (ajuste se necessário)
    allow_credentials=True,
    allow_methods=["*"],  # Permitir todos os métodos (GET, POST, etc.)
    allow_headers=["*"],  # Permitir todos os headers
)

# Carregar credenciais da API
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")


UPLOAD_FOLDER = "uploads/"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)  # Criar a pasta 'uploads/' se não existir

documents = {}  # Dicionário para armazenar o texto dos documentos temporariamente

# URL do modelo correto da API do Google Gemini 2.0 Flash
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GOOGLE_API_KEY}"


def save_pdf(file: UploadFile):
    """Salva o PDF no diretório uploads/ e retorna o caminho do arquivo"""
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return file_path


def extract_text_from_pdf(file_path):
    """Extrai o texto de um PDF armazenado no servidor"""
    text = ""
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text


@app.post("/upload/")
async def upload_pdf(file: UploadFile = File(...)):
    """Recebe um PDF, armazena no servidor e extrai o texto"""
    file_path = save_pdf(file)
    text = extract_text_from_pdf(file_path)

    if not text.strip():
        raise HTTPException(status_code=400, detail="Não foi possível extrair texto do PDF.")

    documents[file.filename] = text  # Armazena o texto do documento na memória
    return {"message": "PDF enviado com sucesso!", "filename": file.filename}


@app.post("/ask/")
async def ask_question(filename: str = Form(...), question: str = Form(...)):
    """Responde perguntas com base no conteúdo do PDF usando a API do Google Gemini 2.0"""
    if filename not in documents:
        raise HTTPException(status_code=400, detail="Arquivo não encontrado. Faça o upload do PDF primeiro.")

    text = documents[filename]  # Recupera o texto armazenado do PDF

    # Criando payload para API do Google
    payload = {
        "contents": [{
            "parts": [{"text": f"Baseado no seguinte documento: {text}\n\nPergunta: {question}"}]
        }]
    }

    headers = {"Content-Type": "application/json"}

    # Fazendo a requisição para a API do Google Gemini
    response = requests.post(GEMINI_API_URL, json=payload, headers=headers)

    if response.status_code != 200:
        return {"error": "Erro na API do Google Gemini", "status_code": response.status_code,
                "response": response.json()}

    return {"answer": response.json()["candidates"][0]["content"]["parts"][0]["text"]}
