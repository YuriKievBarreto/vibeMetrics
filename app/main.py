from fastapi import FastAPI
from fastapi import APIRouter
from .api.main_router import mainRouter
from contextlib import asynccontextmanager
from app.core.database import init_db
from pathlib import Path
from fastapi.middleware.cors import CORSMiddleware


import uvicorn


print("rodando em http://localhost:8000")



@asynccontextmanager
async def lifespan(app: FastAPI):
  
    await init_db()
    print("aplicação rodando e conectada com o banco de dados")
    print("rodando em http://localhost:8000/api/v1/auth/login")
    print("rodando em http://127.0.0.1:8000/")


    yield 
    
   
    print("Aplicação encerrada, recursos liberados.")


app = FastAPI(
    title="spotify analytics",
    lifespan=lifespan
)



app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5501",    # Live Server (comum no VS Code)
        "http://127.0.0.1:5501",
        "http://localhost:8000",    # Seu front rodando no Docker/Local
        "http://127.0.0.1:8000",
        "https://yurikievbarreto.github.io", # URL do seu projeto no GitHub Pages
    ],
    allow_credentials=True,         # ESSENCIAL para cookies/session_token
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(mainRouter)



if __name__ == "__main__":
    uvicorn.run("app.main:app", host="localhost", port=8000, reload=True)



