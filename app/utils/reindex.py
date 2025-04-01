import os
import pickle
import faiss
import numpy as np
from app.database import SyncSessionLocal
from app.models.models import Document
from app.services.embedding_engine import model, split_text, INDEX_PATH, MAPPING_PATH

def reindex_all_documents():
    session = SyncSessionLocal()

    documentos = session.query(Document).all()

    embedding_dim = model.get_sentence_embedding_dimension()
    index = faiss.IndexFlatL2(embedding_dim)
    id_mapping = []

    total_chunks = 0

    for doc in documentos:
        chunks = split_text(doc.texto_extraido)
        embeddings = model.encode(chunks)
        index.add(np.array(embeddings).astype("float32"))

        for chunk in chunks:
            id_mapping.append({
                "document_id": doc.id,
                "chunk": chunk
            })

        total_chunks += len(chunks)

    # Salva os arquivos
    faiss.write_index(index, INDEX_PATH)
    with open(MAPPING_PATH, "wb") as f:
        pickle.dump(id_mapping, f)

    session.close()
    return total_chunks
