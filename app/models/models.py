from sqlalchemy import Column, Integer, String, Text, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from app.database import Base
from sqlalchemy.orm import relationship

class Document(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True, index=True)
    nome_arquivo = Column(String, nullable=False)
    caminho_arquivo = Column(String, nullable=False)
    texto_extraido = Column(Text, nullable=True)
    data_upload = Column(DateTime, default=datetime.utcnow)

    embeddings = relationship("Embedding", back_populates="document")
    perguntas = relationship("Question", back_populates="documento", cascade="all, delete")



class Embedding(Base):
    __tablename__ = "embeddings"
    id = Column(Integer, primary_key=True, index=True)
    documento_id = Column(Integer, ForeignKey("documents.id"))
    trecho_original = Column(Text, nullable=False)
    vetor_id_faiss = Column(Integer, nullable=True)

    document = relationship("Document", back_populates="embeddings")


class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    documento_id = Column(Integer, ForeignKey("documents.id"))
    pergunta = Column(Text)
    resposta = Column(Text)
    contexto_usado = Column(Text)
    data = Column(DateTime)
    modelo_utilizado = Column(String(50))

    documento = relationship("Document", back_populates="perguntas")