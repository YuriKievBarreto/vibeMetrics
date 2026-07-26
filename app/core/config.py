import os
from pathlib import Path
from typing import List, Optional
from dotenv import load_dotenv
from pydantic import BaseModel, Field

# Diretório raiz do projeto
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Define o ambiente: 'production', 'staging', ou 'development'
ENVIRONMENT = os.getenv("ENVIRONMENT", os.getenv("APP_ENV", "development")).lower()

# Carrega o arquivo .env apropriado (.env.prod para produção, .env para desenvolvimento)
env_file_name = ".env.prod" if ENVIRONMENT in ("production", "prod") else ".env"
env_file_path = BASE_DIR / env_file_name

if env_file_path.exists():
    load_dotenv(dotenv_path=env_file_path, override=True)
else:
    load_dotenv(override=True)


class Settings(BaseModel):
    # Ambiente e Modo de Depuração
    ENVIRONMENT: str = Field(default=ENVIRONMENT)
    DEBUG: bool = Field(default=(ENVIRONMENT not in ("production", "prod")))

    # Endereços Base
    DEFAULT_ADDRESS: str = Field(default_factory=lambda: os.getenv("DEFAULT_ADDRESS", "http://127.0.0.1:8000").strip())
    FRONTEND_ADDRESS: str = Field(default_factory=lambda: os.getenv("FRONTEND_ADDRESS", "http://127.0.0.1:5501/frontend").strip())

    # Origens Permitidas no CORS
    @property
    def allowed_origins(self) -> List[str]:
        raw_origins = os.getenv("ALLOWED_ORIGINS")
        if raw_origins:
            return [o.strip() for o in raw_origins.split(",") if o.strip()]
        return [
            "http://localhost:5501",
            "http://127.0.0.1:5501",
            "http://localhost:8000",
            "http://127.0.0.1:8000",
            "https://yurikievbarreto.github.io",
        ]

    # Banco de Dados
    DATABASE_URL: str = Field(default_factory=lambda: os.getenv("DATABASE_URL", ""))

    # Segurança e Tokens JWT
    SECRET_KEY: str = Field(default_factory=lambda: os.getenv("SECRET_KEY", "secret_key"))
    JWT_SECRET_KEY: str = Field(default_factory=lambda: os.getenv("JWT_SECRET_KEY", "jwt_secret_key"))
    ALGORITHM: str = Field(default_factory=lambda: os.getenv("ALGORITHM", "HS256"))
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default_factory=lambda: int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "43200"))
    )

    # Spotify OAuth
    SPOTIPY_CLIENT_ID: Optional[str] = Field(default_factory=lambda: os.getenv("SPOTIPY_CLIENT_ID"))
    SPOTIPY_CLIENT_SECRET: Optional[str] = Field(default_factory=lambda: os.getenv("SPOTIPY_CLIENT_SECRET"))
    SPOTIPY_REDIRECT_URI: Optional[str] = Field(default_factory=lambda: os.getenv("SPOTIPY_REDIRECT_URI"))

    # AWS e Serviços de IA
    AWS_ACCESS_KEY_ID: Optional[str] = Field(default_factory=lambda: os.getenv("AWS_ACCESS_KEY_ID"))
    AWS_SECRET_ACCESS_KEY: Optional[str] = Field(default_factory=lambda: os.getenv("AWS_SECRET_ACCESS_KEY"))
    AWS_REGION: str = Field(default_factory=lambda: os.getenv("AWS_REGION", "us-east-1"))
    EMOTION_LLM_PROVIDER: str = Field(default_factory=lambda: os.getenv("EMOTION_LLM_PROVIDER", "groq"))
    GROQ_API_KEY: Optional[str] = Field(default_factory=lambda: os.getenv("GROQ_API_KEY"))

    # Genius API
    GENIUS_CLIENT_ID: Optional[str] = Field(default_factory=lambda: os.getenv("GENIUS_CLIENT_ID"))
    GENIUS_CLIENT_SECRET: Optional[str] = Field(default_factory=lambda: os.getenv("GENIUS_CLIENT_SECRET"))
    GENIUS_ACCESS_TOKEN: Optional[str] = Field(default_factory=lambda: os.getenv("GENIUS_ACCESS_TOKEN"))


settings = Settings()
