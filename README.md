# 🎵 Vibe Metrics — Spotify Analytics & Emotional AI

<p align="center">
  <img src="https://upload.wikimedia.org/wikipedia/commons/1/19/Spotify_logo_without_text.svg" alt="Spotify Logo" width="80" />
</p>

<p align="center">
  <b>Plataforma de Inteligência Analítica e Perfilamento Emocional de Música movida por IA e LLMs</b>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.13-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.13" />
  <img src="https://img.shields.io/badge/FastAPI-0.119-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/PostgreSQL-16-4169E1?style=for-the-badge&logo=postgresql&logoColor=white" alt="PostgreSQL" />
  <img src="https://img.shields.io/badge/Docker-Enabled-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker" />
  <img src="https://img.shields.io/badge/AI-Groq%20%2B%20Bedrock-FF4500?style=for-the-badge&logo=openai&logoColor=white" alt="AI Stack" />
  <img src="https://img.shields.io/badge/TailwindCSS-v3-38B2AC?style=for-the-badge&logo=tailwindcss&logoColor=white" alt="TailwindCSS" />
</p>

---

## 📌 Sumário
- [Visão Geral](#-visão-geral)
- [🧠 Destaque: Uso de Inteligência Artificial](#-destaque-uso-de-inteligência-artificial)
  - [1. Vetor Emocional Multi-dimensional (18 Emoções)](#1-vetor-emocional-multi-dimensional-18-emoções)
  - [2. Arquitetura LLM Resiliente & Fallback Automático](#2-arquitetura-llm-resiliente--fallback-automático)
  - [3. Perfilamento Comportamental & Análise Poética](#3-perfilamento-comportamental--análise-poética)
- [✨ Funcionalidades do Sistema](#-funcionalidades-do-sistema)
- [🛠️ Tecnologias Utilizadas](#️-tecnologias-utilizadas)
- [🏗️ Arquitetura e Fluxo de Dados](#️-arquitetura-e-fluxo-de-dados)
- [🚀 Como Executar o Projeto](#-como-executar-o-projeto)
  - [Pré-requisitos](#pré-requisitos)
  - [Executando via Docker Compose (Recomendado)](#executando-via-docker-compose-recomendado)
  - [Executando Localmente com `uv`](#executando-localmente-com-uv)
- [🌐 Endpoints Principais da API](#-endpoints-principais-da-api)
- [📂 Estrutura do Repositório](#-estrutura-do-repositório)
- [👤 Autor](#-autor)

---

## 📖 Visão Geral

O **Vibe Metrics** é uma aplicação Full-Stack avançada que conecta à conta do usuário no **Spotify** para extrair hábitos de escuta (músicas, artistas e gêneros favoritos) e cruza esses dados com a **letra das músicas** para realizar uma **análise psicológica e emocional detalhada por Inteligência Artificial (IA)**.

Em vez de apenas exibir contagens de reprodução convencionais, o Vibe Metrics busca e analisa a poesia lírica das faixas em tempo real, calculando uma assinatura emocional única para cada usuário e gerando interpretações poéticas sobre a visão de mundo refletida em seu gosto musical.

---

## 🧠 Destaque: Uso de Inteligência Artificial

A Inteligência Artificial é o núcleo central e diferencial técnico do projeto. Ela é utilizada para transformar textos brutos de letras de música em métricas estruturadas e insights em linguagem natural.

```
       ┌────────────────────────┐
       │   Histórico Spotify    │
       └───────────┬────────────┘
                   │
                   ▼
       ┌────────────────────────┐
       │ Extração de Letras     │ (Letras.mus.br ➔ Genius Fallback)
       └───────────┬────────────┘
                   │
                   ▼
 ┌────────────────────────────────────┐
 │  Groq LLM Chain / AWS Bedrock      │ ◄── [IA: Batch Analysis & Concurrency]
 └───────────┬────────────────────────┘
             │
   ┌─────────┴──────────────────────────────┐
   ▼                                        ▼
┌──────────────────────────────┐  ┌─────────────────────────────────┐
│ Vetor Emocional (18 dimensões)│  │ Perfil Poético & Citação Crítica │
└──────────────────────────────┘  └─────────────────────────────────┘
```

### 1. Vetor Emocional Multi-dimensional (18 Emoções)
Cada faixa obtida do Spotify passa por uma extração assíncrona de emoções em lote (`extrair_emocoes_batch_bedrock`), onde um modelo LLM avalia a presença e a intensidade (escala contínua de `0.0` a `1.0`) de **18 dimensões emocionais distintas**:

- **Emoções Positivas / Elevadas:** Alegria, Otimismo, Esperança, Paz, Amor, Autoafirmação.
- **Emoções Introspectivas / Profundas:** Introspecção, Nostalgia, Melancolia, Anseio.
- **Emoções Conflituosas / Intensas:** Tristeza, Raiva, Medo, Desilusão Amorosa, Desespero, Rebeldia.
- **Emoções de Expressão:** Sensualidade, Conteúdo Sensível (`sexual_explicit`).

Os resultados de todas as faixas favoritas do usuário são sintetizados em uma média ponderada (`get_media_emocoes`) para formar o **Vetor de Vibe Global**.

### 2. Arquitetura LLM Resiliente & Fallback Automático
Para garantir altíssima disponibilidade, baixíssima latência e tolerância a falhas ou limites de taxa (Rate Limits), o pipeline de IA utiliza uma **cadeia de fallback automática em 2 níveis**:

1. **Groq LLM Fallback Chain (Nível 1 - Ultra Rápido):**
   Tenta sequencialmente chamadas com retorno forçado em formato JSON strict aos seguintes modelos do Free Tier:
   - `llama-3.3-70b-versatile` *(Recomendado / Principal)*
   - `llama-3.1-70b-versatile`
   - `llama-3.1-8b-instant`
   - `mixtral-8x7b-32768`
   - `llama3-70b-8192`
   - `llama3-8b-8192`
   - `gemma2-9b-it`
   - `deepseek-r1-distill-llama-70b`

2. **AWS Bedrock Fallback (Nível 2 - Alta Confiabilidade Enterprise):**
   Caso toda a cadeia Groq exceda a quota de requisições, o sistema faz um failover transparente para o **Amazon Nova Micro** (`amazon.nova-micro-v1:0`) via AWS Bedrock Converse API.

### 3. Perfilamento Comportamental & Análise Poética
Além de números, a IA atua na interpretação qualitativa dos hábitos do usuário:
- **Perfil Emocional Consolidado (`get_perfil_emocional`):** Um prompt especializado atua como analista comportamental e gera uma síntese intuitiva (limitada a 3 linhas) conectando as emoções de maior intensidade com a visão de mundo do usuário.
- **Análise Poética por Faixa (`get_analise_musica`):** Para as faixas de maior relevância emocional, a IA localiza exatamente o verso ou estrofe que mais expressa aquela emoção e produz uma explicação poética enriquecida.

---

## ✨ Funcionalidades do Sistema

- 🔑 **Autenticação Spotify OAuth 2.0:** Login seguro utilizando o fluxo de autorização oficial do Spotify, com emissão de cookies de sessão JWT (`HTTP-Only`).
- ⚡ **Ingestão de Dados Assíncrona em Background:** Execução não bloqueante (`BackgroundTasks`) que baixa e atualiza dados do usuário ao fazer login.
- 🎵 **Métricas por Temporalidade:** Filtros configuráveis para analisar faixas e artistas mais ouvidos em 3 horizontes de tempo:
  - **Curto Prazo (`short_term`):** Últimas 4 semanas.
  - **Médio Prazo (`medium_term`):** Últimos 6 meses.
  - **Longo Prazo (`long_term`):** Histórico completo de anos.
- 📜 **Motor de Extração Dual de Letras:**
  - Busca primária via Web Scraping otimizado no `Letras.mus.br`.
  - Fallback automático para a API oficial do `Genius` com parser BeautifulSoup.
- 📊 **Dashboard Interativo e Visual:**
  - Painel com métricas gerais, gênero dominante e top faixas/artistas.
  - Página dedicada de **Análise de Emoções** com barras de intensidade, destaques poéticos e citação de versos marcantes.
  - Filtros dinâmicos e cards estilizados por paleta de cor de acordo com a emoção predominante.

---

## 🛠️ Tecnologias Utilizadas

### Backend
- **Linguagem:** Python 3.13
- **Framework Web:** FastAPI (com uvicorn / gunicorn)
- **Gerenciador de Pacotes:** `uv`
- **Banco de Dados:** PostgreSQL + SQLModel / SQLAlchemy (AsyncIO) + `asyncpg`
- **Autenticação & Segurança:** Python-JOSE (JWT), Cookies HTTP-Only
- **APIs de Terceiros:** Spotipy (Spotify Web API), Genius API, Letras.mus.br (httpx + BeautifulSoup4)

### Inteligência Artificial & NLP
- **Provedores de LLM:** Groq Cloud API & AWS Bedrock (Amazon Nova)
- **Modelos Utilizados:** Llama 3.3 70B, Llama 3.1 70B/8B, Mixtral 8x7B, DeepSeek R1, Amazon Nova Micro
- **Concorrência:** `asyncio.Semaphore` para processamento paralelo de letras

### Frontend
- **Interface:** HTML5, JavaScript Moderno (ES Modules), Vanilla CSS
- **Framework Estilização:** TailwindCSS (via CDN)
- **Design System:** Tema Dark Premium, Glassmorphism, Micro-animações e Modais de Loading em tempo real

---

## 🏗️ Arquitetura e Fluxo de Dados

```mermaid
flowchart TD
    A[Usuário] -->|1. Login OAuth2| B[FastAPI Backend]
    B -->|2. Troca de Code por Tokens| C[Spotify Web API]
    B -->|3. Dispara Ingestão Background| D[Background Processing]
    
    subgraph Ingestão de Dados
        D -->|Busca Top Tracks & Artists| C
        D -->|Scrape Letra| E[Letras.mus.br]
        E -- Falha -->|Fallback Letra| F[Genius API]
        D -->|Envia Letra para Analisar| G[Provedor LLM IA]
    end

    subgraph Pipeline de IA
        G -->|1ª Opção| H[Groq Fallback Chain]
        H -- Rate Limit -->|2ª Opção| I[AWS Bedrock Nova]
        G -->|Retorna Vetor 18 Emoções| J[Agregador & Perfilador]
    end

    J -->|Salva Estado Otimizado| K[(PostgreSQL Database)]
    K -->|Consumo REST API| L[Frontend Dashboard]
```

---

## 🚀 Como Executar o Projeto

### Pré-requisitos
- **Docker** e **Docker Compose** instalados (método recomendado), OU
- **Python 3.13+** e **uv** (para execução local).
- Uma conta no [Spotify Developer Dashboard](https://developer.spotify.com/) com as credenciais `SPOTIPY_CLIENT_ID` e `SPOTIPY_CLIENT_SECRET`.
- Chave da API do **Groq** ([Groq Console](https://console.groq.com/)) ou credenciais **AWS** com acesso ao Bedrock.

---

### Configuração das Variáveis de Ambiente (`.env`)

Crie um arquivo `.env` na raiz do projeto contendo as seguintes definições:

```env
# Spotify OAuth Credentials
SPOTIPY_CLIENT_ID=seu_client_id_aqui
SPOTIPY_CLIENT_SECRET=seu_client_secret_aqui
SPOTIPY_REDIRECT_URI=http://127.0.0.1:8000/api/v1/auth/callback

# Endereços da Aplicação
DEFAULT_ADDRESS=http://127.0.0.1:8000
FRONTEND_ADDRESS=http://127.0.0.1:5501/frontend

# Banco de Dados PostgreSQL
POSTGRES_USER=yuri
POSTGRES_PASSWORD=sua_senha
POSTGRES_DB=db_spotify_analytics
DB_HOST=db  # Use 'db' para Docker ou 'localhost' para rodar fora do Docker
DATABASE_URL=postgresql+asyncpg://yuri:sua_senha@db:5432/db_spotify_analytics

# Segurança JWT
JWT_SECRET_KEY=sua_chave_secreta_jwt
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=43200

# Provedor de IA (groq ou bedrock)
EMOTION_LLM_PROVIDER=groq
GROQ_API_KEY=sua_chave_groq_aqui

# AWS Bedrock (Opcional se usar Groq)
AWS_ACCESS_KEY_ID=sua_aws_access_key
AWS_SECRET_ACCESS_KEY=sua_aws_secret_key

# Genius API (Letras Fallback)
GENIUS_ACCESS_TOKEN=seu_token_genius_aqui
```

---

### Executando via Docker Compose (Recomendado)

O projeto possui um arquivo `docker-compose.yaml` pronto com PostgreSQL e serviço FastAPI conteinerizado via `uv`.

1. **Inicie os containers:**
   ```bash
   docker compose up -d --build
   ```

2. **Verifique os logs da aplicação:**
   ```bash
   docker compose logs -f app
   ```

3. **Acesse a aplicação:**
   - Backend API: `http://localhost:8000/docs`
   - Frontend Landing Page: `http://localhost:8000/frontend/index.html` (ou via Live Server no VSCode em `http://127.0.0.1:5501/frontend/index.html`)

---

### Executando Localmente com `uv`

Caso prefira rodar sem Docker:

1. **Instale o gerenciador de pacotes `uv`:**
   ```bash
   pip install uv
   ```

2. **Instale as dependências do projeto:**
   ```bash
   uv sync
   ```

3. **Inicie o servidor de desenvolvimento:**
   ```bash
   uv run uvicorn app.main:app --reload --port 8000
   ```

---

## 🌐 Endpoints Principais da API

| Método | Endpoint | Descrição |
|---|---|---|
| `GET` | `/api/v1/auth/login` | Redireciona o usuário para a página de autorização do Spotify. |
| `GET` | `/api/v1/auth/callback` | Processa o retorno do OAuth2 e inicia a ingestão de dados em background. |
| `GET` | `/api/v1/user/me` | Valida a sessão JWT ativa do usuário. |
| `GET` | `/api/v1/user/get_user_basic_data` | Retorna perfil do usuário, gênero dominante e destaques principais. |
| `GET` | `/api/v1/user/top_musicas` | Retorna as faixas mais ouvidas divididas por rank (`short`, `medium`, `long`). |
| `GET` | `/api/v1/user/top_artistas` | Retorna os artistas mais ouvidos com métricas e imagens de álbum. |
| `GET` | `/api/v1/user/perfil_musical` | Retorna a análise de IA: vetor de emoções, perfil em 3 linhas e destaques poéticos por faixa. |
| `POST`| `/api/v1/user/logout` | Encerra a sessão e deleta o cookie JWT. |

---

## 📂 Estrutura do Repositório

```text
spotify-analytics/
├── app/
│   ├── api/                   # Controllers e rotas da API FastAPI (auth, user, dashboard)
│   ├── core/                  # Configurações (Pydantic Settings, DB Async, AWS, Spotipy Auth)
│   ├── models/                # Modelos de dados e schemas SQLModel / Pydantic
│   ├── repositories/          # Camada de acesso ao banco de dados (CRUD)
│   ├── services/              # Regras de negócio, ingestão, letras e Inteligência Artificial
│   │   ├── emotion_extraction_service.py  # Pipeline de IA (Groq Chain + Bedrock)
│   │   ├── extracao_de_letras.py          # Scraper Letras.mus.br + Genius API
│   │   ├── spotipy_service.py             # Comunicação com a API do Spotify
│   │   └── user_service.py                # Orquestração do Perfil Musical e Emoções
│   └── main.py                # Ponto de entrada da aplicação FastAPI
├── demo/                      # Demonstração estática e mockups para testes/preview
├── frontend/                  # Interface web (HTML5, JS ES Modules, TailwindCSS)
│   ├── index.html             # Landing Page
│   ├── dashboard.html         # Visão Geral
│   ├── artistas.html          # Métricas de Artistas
│   ├── musicas.html           # Métricas de Músicas
│   └── emocoes.html           # Dashboard Visual de Inteligência Artificial & Emoções
├── docker-compose.yaml        # Orquestração Docker (PostgreSQL + FastAPI App)
├── Dockerfile                 # Multi-stage build otimizado com uv
├── pyproject.toml             # Configuração do projeto Python e dependências
└── README.md                  # Documentação oficial do projeto
```

---

## 👤 Autor

Desenvolvido por **Yuri Kiev de Sousa Barreto**.

- 📧 Email: [yurikievbarreto@gmail.com](mailto:yurikievbarreto@gmail.com)
- 🐙 GitHub: [@YuriKievBarreto](https://github.com/YuriKievBarreto)