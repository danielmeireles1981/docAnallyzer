# Importa as bibliotecas necessárias
from fastapi import FastAPI, File, UploadFile, Form, HTTPException  # Framework FastAPI para criação da API
import pdfplumber  # Biblioteca para extração de texto de arquivos PDF
import os  # Biblioteca para manipulação de arquivos e diretórios
import shutil  # Biblioteca para operações de manipulação de arquivos
import requests  # Biblioteca para realizar requisições HTTP
from dotenv import load_dotenv  # Biblioteca para carregar variáveis de ambiente de um arquivo .env
from fastapi.middleware.cors import CORSMiddleware  # Middleware para permitir requisições CORS

# Inicializa a aplicação FastAPI
app = FastAPI()

# Configuração do CORS para permitir chamadas do frontend (evita bloqueios de segurança)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permite requisições de qualquer origem (pode ser ajustado para um domínio específico)
    allow_credentials=True,  # Permite envio de cookies e credenciais em requisições
    allow_methods=["*"],  # Permite todos os métodos HTTP (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Permite todos os cabeçalhos HTTP
)

# Carrega as credenciais da API do Google Gemini a partir do arquivo .env
load_dotenv()  # Carrega as variáveis de ambiente
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")  # Obtém a chave da API do Google armazenada no arquivo .env

# Define a pasta onde os arquivos PDF serão armazenados
UPLOAD_FOLDER = "uploads/"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)  # Cria a pasta 'uploads/' caso ela não exista

# Dicionário para armazenar temporariamente o texto extraído dos documentos
documents = {}

# Define a URL da API do Google Gemini 2.0 Flash, incluindo a chave de API no parâmetro da URL
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GOOGLE_API_KEY}"


def save_pdf(file: UploadFile):
    """
    Salva um arquivo PDF no diretório 'uploads/' e retorna o caminho do arquivo.
    """
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)  # Define o caminho onde o arquivo será salvo
    with open(file_path, "wb") as buffer:  # Abre o arquivo para escrita binária
        shutil.copyfileobj(file.file, buffer)  # Copia o conteúdo do arquivo enviado para o armazenamento local
    return file_path  # Retorna o caminho do arquivo salvo


def extract_text_from_pdf(file_path):
    """
    Extrai o texto de um arquivo PDF salvo no servidor.
    """
    text = ""  # Inicializa a variável que armazenará o texto extraído
    with pdfplumber.open(file_path) as pdf:  # Abre o PDF para leitura com pdfplumber
        for page in pdf.pages:  # Percorre todas as páginas do PDF
            page_text = page.extract_text()  # Extrai o texto da página
            if page_text:  # Se houver texto na página, adiciona ao texto extraído
                text += page_text + "\n"
    return text  # Retorna o texto extraído do PDF


@app.post("/upload/")
async def upload_pdf(file: UploadFile = File(...)):
    """
    Rota para receber um arquivo PDF, armazená-lo no servidor e extrair seu conteúdo.
    Retorna uma mensagem de sucesso e o nome do arquivo salvo.
    """
    file_path = save_pdf(file)  # Salva o arquivo PDF no servidor
    text = extract_text_from_pdf(file_path)  # Extrai o texto do PDF

    if not text.strip():  # Verifica se o texto extraído está vazio
        raise HTTPException(status_code=400, detail="Não foi possível extrair texto do PDF.")  # Retorna erro 400

    documents[file.filename] = text  # Armazena o texto do documento na memória
    return {"message": "PDF enviado com sucesso!", "filename": file.filename}  # Retorna mensagem de sucesso


@app.post("/ask/")
async def ask_question(filename: str = Form(...), question: str = Form(...)):
    """
    Rota para responder perguntas com base no conteúdo do PDF.
    O usuário deve informar o nome do arquivo (filename) e a pergunta (question).
    A resposta é gerada pela API do Google Gemini 2.0 Flash.
    """
    if filename not in documents:  # Verifica se o arquivo foi enviado anteriormente
        raise HTTPException(status_code=400, detail="Arquivo não encontrado. Faça o upload do PDF primeiro.")

    text = documents[filename]  # Recupera o texto armazenado do PDF

    # Criação do payload (corpo da requisição) para a API do Google
    payload = {
        "contents": [{
            "parts": [{"text": f"Baseado no seguinte documento: {text}\n\nPergunta: {question}"}]
        }]
    }

    headers = {"Content-Type": "application/json"}  # Define o cabeçalho para envio de JSON

    # Faz a requisição para a API do Google Gemini
    response = requests.post(GEMINI_API_URL, json=payload, headers=headers)

    if response.status_code != 200:  # Se houver erro na API
        return {
            "error": "Erro na API do Google Gemini",
            "status_code": response.status_code,
            "response": response.json()
        }

    # Retorna a resposta da IA extraída da resposta JSON da API do Google
    return {"answer": response.json()["candidates"][0]["content"]["parts"][0]["text"]}
