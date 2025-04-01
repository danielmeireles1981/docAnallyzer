from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import os
import pickle

MODEL_NAME = 'all-MiniLM-L6-v2'
INDEX_PATH = 'embeddings/index.faiss'
MAPPING_PATH = 'embeddings/id_mapping.pkl'

# 🔹 Carrega o modelo
model = SentenceTransformer(MODEL_NAME)
embedding_dim = model.get_sentence_embedding_dimension()

# 🔹 Carrega ou cria o índice FAISS
if os.path.exists(INDEX_PATH):
    index = faiss.read_index(INDEX_PATH)
    print("✅ Índice FAISS carregado.")
else:
    index = faiss.IndexFlatL2(embedding_dim)
    print("⚠️ Índice FAISS novo criado.")

# 🔹 Carrega ou inicia o mapeamento
if os.path.exists(MAPPING_PATH):
    with open(MAPPING_PATH, "rb") as f:
        id_mapping = pickle.load(f)
    print("✅ Mapeamento de trechos carregado.")
else:
    id_mapping = []
    print("⚠️ Mapeamento novo iniciado.")


def split_text(text: str, max_tokens: int = 500) -> list:
    chunks = []
    current = ""

    for line in text.split("\n"):
        if len(current) + len(line) < max_tokens:
            current += line.strip() + " "
        else:
            chunks.append(current.strip())
            current = line.strip() + " "
    if current:
        chunks.append(current.strip())

    return chunks


def embed_and_index(document_id: int, text: str):
    chunks = split_text(text)

    embeddings = model.encode(chunks)

    # Garantir tipo correto
    index.add(np.array(embeddings).astype("float32"))

    for chunk in chunks:
        id_mapping.append({
            "document_id": document_id,
            "chunk": chunk
        })

    # Salva o índice e o mapeamento
    faiss.write_index(index, INDEX_PATH)
    with open(MAPPING_PATH, "wb") as f:
        pickle.dump(id_mapping, f)

    return len(chunks)


def buscar_contexto(pergunta: str, documento_id: int, top_k: int = 3):
    if not os.path.exists(INDEX_PATH) or not os.path.exists(MAPPING_PATH):
        return ["❌ Índice ainda não criado. Faça o upload de pelo menos um PDF primeiro."]

    embedding_pergunta = model.encode([pergunta]).astype("float32")

    index_loaded = faiss.read_index(INDEX_PATH)
    with open(MAPPING_PATH, "rb") as f:
        id_map = pickle.load(f)

    # Busca os top_k * 5 e filtra só os do documento
    D, I = index_loaded.search(embedding_pergunta, top_k * 5)

    trechos_relevantes = []
    for idx in I[0]:
        if idx < len(id_map):
            item = id_map[idx]
            if item["document_id"] == documento_id:
                trechos_relevantes.append(item["chunk"])
                if len(trechos_relevantes) == top_k:
                    break

    return trechos_relevantes or ["⚠️ Nenhum trecho correspondente ao documento encontrado."]
