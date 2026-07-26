from fastapi import FastAPI
from fastapi import APIRouter
from .api.main_router import mainRouter
from contextlib import asynccontextmanager
from app.core.database import init_db
from pathlib import Path
from fastapi.middleware.cors import CORSMiddleware


import uvicorn


from app.core.config import settings


print(f"Aplicação rodando em ambiente [{settings.ENVIRONMENT.upper()}] - {settings.DEFAULT_ADDRESS}")



@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    print(f"Aplicação rodando em {settings.DEFAULT_ADDRESS}")
    yield 
    print("Aplicação encerrada, recursos liberados.")


app = FastAPI(
    title="spotify analytics",
    debug=settings.DEBUG,
    lifespan=lifespan
)



app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,         # ESSENCIAL para cookies/session_token
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(mainRouter)



if __name__ == "__main__":
    uvicorn.run("app.main:app", host="localhost", port=8000, reload=True)



