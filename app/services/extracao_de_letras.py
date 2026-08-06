import os
import re
import asyncio
import unicodedata
import httpx
from bs4 import BeautifulSoup
from app.core.config import settings

GENIUS_ACCESS_TOKEN = settings.GENIUS_ACCESS_TOKEN
GENIUS_SEARCH_URL = "https://api.genius.com/search"


def normalizar_nome(nome: str) -> str:
    nome = nome.lower().strip()
    nome = unicodedata.normalize('NFD', nome)
    nome = nome.encode('ascii', 'ignore').decode('utf-8')
    nome = re.sub(r'[^a-z0-9 -]', '', nome)   # agora permite hífen
    nome = re.sub(r'\s+', '-', nome)          # espaços viram hífen
    nome = re.sub(r'-+', '-', nome)           # colapsa hífens duplicados
    return nome


import re

def limpar_letra_genius(texto: str) -> str:
    match = re.search(r'\[(Verse|Chorus|Intro|Hook|Bridge|Outro|Refrão|Verso)', texto, re.IGNORECASE)
    if match:
        return texto[match.start():].strip()
    return texto.strip()

# ============================================================
# PLANO A: letras.mus.br (seu código original, mantido intacto)
# ============================================================
def _parse_letras_mus(html: str, artista: str, musica: str, musica_fmt: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    titulo_tag = soup.find("h1")
    titulo_pagina = normalizar_nome(titulo_tag.get_text(strip=True)) if titulo_tag else ""

    if not titulo_pagina or (musica_fmt not in titulo_pagina and titulo_pagina not in musica_fmt):
        return {
            "artista": artista,
            "musica": musica,
            "erro": f"Título da página ('{titulo_tag.get_text(strip=True) if titulo_tag else '???'}') não bate com a música pedida",
            "letra": None,
            "fonte": None
        }

    lyrics_div = soup.find("div", {"class": "lyric-original"})
    if not lyrics_div:
        return {"artista": artista, "musica": musica, "erro": "Letra não encontrada", "letra": None, "fonte": None}

    letra = lyrics_div.get_text("\n", strip=True)
    return {"artista": artista, "musica": musica, "erro": None, "letra": letra, "fonte": "letras.mus.br"}


async def buscar_letra_letras_mus(artista: str, musica: str) -> dict:
    artista_fmt = normalizar_nome(artista)
    musica_fmt = normalizar_nome(musica)
    url = f"https://www.letras.mus.br/{artista_fmt}/{musica_fmt}/"

    try:
        async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
            resp = await client.get(url)

        if resp.status_code != 200:
            return {"artista": artista, "musica": musica, "erro": f"HTTP {resp.status_code}", "letra": None, "fonte": None}

        return await asyncio.to_thread(_parse_letras_mus, resp.text, artista, musica, musica_fmt)

    except Exception as e:
        return {"artista": artista, "musica": musica, "erro": str(e), "letra": None, "fonte": None}


# ============================================================
# PLANO B: Genius (busca + scraping da página encontrada)
# ============================================================
async def buscar_url_genius(artista: str, musica: str) -> str | None:
    """Usa a API oficial do Genius para achar a URL correta da música."""
    if not GENIUS_ACCESS_TOKEN:
        return None

    query = f"{artista} {musica}"
    headers = {"Authorization": f"Bearer {GENIUS_ACCESS_TOKEN}"}

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(GENIUS_SEARCH_URL, params={"q": query}, headers=headers)

        if resp.status_code != 200:
            return None

        data = resp.json()
        hits = data.get("response", {}).get("hits", [])
        if not hits:
            return None

        melhor_hit = hits[0]["result"]
        return melhor_hit.get("url")

    except Exception:
        return None


def _parse_genius(html: str, artista: str, musica: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    lyrics_divs = soup.find_all("div", {"data-lyrics-container": "true"})

    if not lyrics_divs:
        return {"artista": artista, "musica": musica, "erro": "Letra não encontrada (Genius)", "letra": None, "fonte": None}

    partes = []
    for div in lyrics_divs:
        for br in div.find_all("br"):
            br.replace_with("\n")
        partes.append(div.get_text())

    letra = "\n".join(partes).strip()
    letra = limpar_letra_genius(letra)
    return {"artista": artista, "musica": musica, "erro": None, "letra": letra, "fonte": "genius.com"}


async def buscar_letra_genius(artista: str, musica: str) -> dict:
    genius_url = await buscar_url_genius(artista, musica)

    if not genius_url:
        return {"artista": artista, "musica": musica, "erro": "Não encontrado no Genius", "letra": None, "fonte": None}

    try:
        async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
            resp = await client.get(genius_url)

        if resp.status_code != 200:
            return {"artista": artista, "musica": musica, "erro": f"HTTP {resp.status_code} (Genius)", "letra": None, "fonte": None}

        return await asyncio.to_thread(_parse_genius, resp.text, artista, musica)

    except Exception as e:
        return {"artista": artista, "musica": musica, "erro": str(e), "letra": None, "fonte": None}


# ============================================================
# ORQUESTRADOR: tenta letras.mus.br, cai pro Genius se falhar
# ============================================================
async def buscar_letra(artista: str, musica: str, semaphore: asyncio.Semaphore) -> dict:
    async with semaphore:
        resultado = await buscar_letra_letras_mus(artista, musica)

        if resultado["letra"] is not None:
            return resultado

        # Fallback: tenta Genius
        print(f"[fallback] '{artista} - {musica}' falhou no letras.mus.br ({resultado['erro']}), tentando Genius...")
        resultado_genius = await buscar_letra_genius(artista, musica)
        return resultado_genius


async def buscar_letras_em_batch(lista_musicas: list, max_concurrency: int = 5):
    semaphore = asyncio.Semaphore(max_concurrency)
    tasks = [
        buscar_letra(artista, musica, semaphore)
        for artista, musica in lista_musicas
    ]

    resultados = await asyncio.gather(*tasks)
    return resultados