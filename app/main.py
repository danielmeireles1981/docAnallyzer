from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.routing import APIRoute
from app.api.routes import router
import logging

# ---------- Logger ----------
logging.basicConfig(
    level=logging.INFO,
    format="📘 [%(asctime)s] [%(levelname)s] - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

# ---------- Instância da aplicação ----------
app = FastAPI(title="DocAnallyzer")

# ---------- Middleware de CORS ----------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Pode ajustar conforme segurança desejada
    allow_methods=["*"],
    allow_headers=["*"]
)

# ---------- Inclusão das rotas principais ----------
app.include_router(router)
logger.info("✅ Rotas principais registradas!")

# ---------- Log das rotas na inicialização ----------
@app.on_event("startup")
async def startup_log():
    logger.info("🚀 Aplicação iniciando...")
    logger.info("📚 Rotas disponíveis:")
    for route in app.routes:
        if isinstance(route, APIRoute):
            logger.info(f"➡️ {route.path}  [{', '.join(route.methods)}]")

@app.on_event("shutdown")
async def shutdown_log():
    logger.info("🛑 Aplicação finalizando...")

# ---------- Rota de teste (opcional) ----------
@app.get("/ping")
async def ping():
    return {"status": "ok"}
