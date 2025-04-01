import google.generativeai as genai
import os

# ✅ Insira sua chave real aqui
GEMINI_API_KEY = "AIzaSyBK2dW4auXsEwBZVXA0yWcwrYLX2oh9oCc"

genai.configure(api_key=GEMINI_API_KEY)

# Usa o modelo Gemini 1.5 Flash mais recente
MODEL_NAME = "models/gemini-1.5-flash-latest"

def gerar_resposta_gemini(pergunta: str, contexto: list[str]):
    contexto_completo = "\n\n".join(contexto)

    prompt = f"""
Você é uma IA treinada para responder perguntas com base em documentos fornecidos.

📄 Contexto do documento:
{contexto_completo}

❓ Pergunta do usuário:
{pergunta}

Responda com base apenas no conteúdo acima, de forma clara e objetiva.
"""

    try:
        model = genai.GenerativeModel(model_name=MODEL_NAME)
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"❌ Erro ao chamar Gemini: {e}"
