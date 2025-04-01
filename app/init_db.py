import asyncio
from app.models import models  # Isso garante o registro das tabelas
from app.database import engine, Base

async def init_db():
    print("🔧 Iniciando criação do banco de dados e tabelas...")
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("✅ Banco de dados e tabelas criados com sucesso!")
    except Exception as e:
        print(f"❌ Erro ao criar o banco de dados: {e}")

if __name__ == "__main__":
    asyncio.run(init_db())
