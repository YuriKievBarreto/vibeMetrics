import sys
import asyncio
from functools import partial
import os
import json
import time
from dotenv import load_dotenv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from app.core.config import settings
from app.core.aws_config import aws_bedrock_client

# ==============================================================================
# CONFIGURAÇÃO DE PROVEDORES E MODELOS
# ==============================================================================

# Defina o provedor ativo: "groq" ou "bedrock" (pode ser alternado via env EMOTION_LLM_PROVIDER)
PROVEDOR_LLM = settings.EMOTION_LLM_PROVIDER.lower()# Lista de modelos do Groq (Free Tier) ordenados por prioridade para fallback automático
GROQ_FALLBACK_CHAIN = [
    "llama-3.3-70b-versatile",        # 1. Recomendado (Llama 3.3 70B)
    "llama-3.1-70b-versatile",        # 2. Llama 3.1 70B
    "llama-3.1-8b-instant",           # 3. Llama 3.1 8B (Ultra Rápido)
    "mixtral-8x7b-32768",             # 4. Mixtral 8x7B (Excelente em JSON)
    "llama3-70b-8192",                # 5. Llama 3 70B
    "llama3-8b-8192",                 # 6. Llama 3 8B
    "gemma2-9b-it",                   # 7. Google Gemma 2 9B
    "deepseek-r1-distill-llama-70b"   # 8. DeepSeek R1 Distill 70B
]

MODELO_BEDROCK_ATUAL = "amazon.nova-micro-v1:0"


# ==============================================================================
# FUNÇÕES DE CHAMADA GENÉRICA ÀS APIS DOS LLMS
# ==============================================================================

async def chamar_groq_api(prompt: str, is_json: bool = True) -> str:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY não foi encontrada no arquivo .env ou variáveis de ambiente.")

    erros = []
    for model_id in GROQ_FALLBACK_CHAIN:
        try:
            try:
                from groq import AsyncGroq
                client = AsyncGroq(api_key=api_key)
                kwargs = {
                    "model": model_id,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.1
                }
                if is_json:
                    kwargs["response_format"] = {"type": "json_object"}
                response = await client.chat.completions.create(**kwargs)
                return response.choices[0].message.content
            except ImportError:
                import urllib.request
                url = "https://api.groq.com/openai/v1/chat/completions"
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "model": model_id,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.1
                }
                if is_json:
                    payload["response_format"] = {"type": "json_object"}
                    
                req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers)
                
                def _fetch():
                    with urllib.request.urlopen(req) as resp:
                        res_body = resp.read().decode("utf-8")
                        res_json = json.loads(res_body)
                        return res_json["choices"][0]["message"]["content"]

                return await asyncio.to_thread(_fetch)
        except Exception as e:
            print(f"⚠️ Groq [{model_id}] falhou ou atingiu limite ({e}). Alternando para o próximo modelo do Free Tier...")
            erros.append((model_id, str(e)))
            await asyncio.sleep(0.3)

    raise RuntimeError(f"Todos os {len(GROQ_FALLBACK_CHAIN)} modelos do Groq falharam. Detalhes: {erros}")


async def chamar_bedrock_api(prompt: str, model_id: str = MODELO_BEDROCK_ATUAL) -> str:
    call = partial(
        aws_bedrock_client.converse,
        modelId=model_id,
        messages=[{"role": "user", "content": [{"text": prompt}]}]
    )
    response = await asyncio.to_thread(call)
    return response["output"]["message"]["content"][0]["text"]


async def executar_chamada_llm(prompt: str, is_json: bool = True) -> str:
    if PROVEDOR_LLM == "groq":
        try:
            return await chamar_groq_api(prompt, is_json=is_json)
        except Exception as e:
            print(f"⚠️ Todos os modelos Groq no Free Tier falharam ({e}). Fazendo fallback de emergência para AWS Bedrock...")
            return await chamar_bedrock_api(prompt, model_id=MODELO_BEDROCK_ATUAL)
    else:
        return await chamar_bedrock_api(prompt, model_id=MODELO_BEDROCK_ATUAL)


# ==============================================================================
# FUNÇÕES DA APLICAÇÃO
# ==============================================================================

async def get_perfil_emocional(emocoes: dict) -> str:
    print(f"analisando perfil emocional (Provedor: {PROVEDOR_LLM.upper()})...")
    prompt = f"""
Você é um analista especializado em comportamento musical e perfil emocional.

A seguir está um JSON com a média das intensidades emocionais (0 a 1) identificadas nas músicas mais ouvidas do usuário:

{json.dumps(emocoes)}

Com base nesses valores, escreva um texto curto (OBRIGATORIAMENTE no máximo 3 linhas) descrevendo:
1. O perfil musical do usuário.
2. Como essa preferência musical se conecta com a visão de mundo dele.

- Seja intuitivo, direto e humano.
- Escreva um texto direcionado para o usuário (usando "Você" e/ou palavras que direcionem o texto ao usuário)
- Não cite números ou valores do JSON.
- Não repita o JSON.
- Não use linguagem técnica de análise; apenas interpretação natural.
- Dê ênfase nas duas emoções com pontuação mais alta, mas sem citar valores.
"""
    try:
        raw_output = await executar_chamada_llm(prompt, is_json=False)
        raw_output = raw_output.replace("```json", "").replace("```", "").strip()
        print("perfil emocional analisado com sucesso!")
        return raw_output
    except Exception as e:
        print(f"Erro ao analisar perfil emocional: {e}")
        chaves = list(emocoes.keys())[:2] if isinstance(emocoes, dict) else []
        return f"Perfil musical diversificado focado em {chaves}."


async def get_analise_musica(EMOCAO: str, LETRA: str):
    print(f"analisando musica (Provedor: {PROVEDOR_LLM.upper()})...")
    prompt = f"""
Instruções:
Você receberá:
Uma emoção predominante, já identificada por outro modelo.
A letra completa de uma música.

Sua tarefa é:
Identificar qual verso ou estrofe da letra tem maior relação direta com a emoção fornecida.
A resposta deve trazer apenas um trecho (o mais relevante).
Explique brevemente por que esse trecho se conecta com a emoção.

Regras:
- Retorne SOMENTE o JSON.
- Seja intuitivo, direto e humano.
- Faça questão de embelezar a explicação, evidenciando um lado poético.

Formato exato da resposta:
{{
  "citacao": "<TRECHO DA LETRA>",
  "explicacao": "<EXPLICAÇÃO CURTA>"
}}

Dados fornecidos:
Emoção predominante: '{EMOCAO}'
Letra da música:
'{LETRA}'
"""
    try:
        raw_output = await executar_chamada_llm(prompt, is_json=True)
        raw_output = raw_output.replace("```json", "").replace("```", "").strip()
        print(f"musica de emocao {EMOCAO} analisada com sucesso!")
        return raw_output
    except Exception as e:
        print(f"Erro ao analisar musica: {e}")
        return json.dumps({"citacao": "Não foi possível extrair a citação.", "explicacao": "Erro na análise."})


async def get_media_emocoes(emocoes: list):
    print("extraindo media de emocoes...")
    dict_media_emocoes = {}
    emocoes_validas = []

    for item in emocoes:
        if isinstance(item, str):
            try:
                item = json.loads(item)
            except Exception:
                item = None
        if isinstance(item, dict):
            emocoes_validas.append(item)

    if not emocoes_validas:
        return {}

    for item in emocoes_validas:
        for a, b in item.items():
            if isinstance(b, (int, float)):
                dict_media_emocoes[a] = dict_media_emocoes.get(a, 0.0) + b

    total = len(emocoes_validas)
    for chave, valor in dict_media_emocoes.items():
        dict_media_emocoes[chave] = round(valor / total, 2)

    return dict_media_emocoes


def montar_prompt_individual(letra: str) -> str:
    return f"""
Você é um analisador emocional especializado.

Sua tarefa é analisar a letra de música fornecida abaixo e identificar a intensidade de cada emoção listada.

IMPORTANTE:
- O raciocínio deve acontecer INTERNAMENTE.
- NÃO revele explicações, etapas, análises ou qualquer texto fora do JSON final.
- A saída final deve conter APENAS um ÚNICO OBJETO JSON com as emoções da letra fornecida.

REGRAS:
- A saída deve ser SOMENTE um OBJETO JSON (chave: valor).
- Não explique nada.
- Não descreva nada fora do JSON.
- Não infira nada que não esteja explícito na letra.
- Não interprete símbolos, metáforas ou contexto cultural.
- Não adivinhe sentimentos implícitos.
- Não altere nomes das chaves.
- O objeto deve conter TODAS as emoções listadas.
- Valores entre 0.0 e 1.0.
- Use 0.0 quando a emoção não estiver presente de forma clara.

FORMATO DA RESPOSTA (OBJETO JSON):
{{
  "alegria": 0.0, "otimismo": 0.0, "esperanca": 0.0,
  "introspeccao": 0.0, "paz": 0.0, "amor": 0.0,
  "tristeza": 0.0, "raiva": 0.0, "medo": 0.0,
  "nostalgia": 0.0, "melancolia": 0.0, "desilusao_amorosa": 0.0,
  "desespero": 0.0, "rebeldia": 0.0, "anseio": 0.0,
  "autoafirmacao": 0.0, "sensualidade": 0.0, "sexual_explicit": 0.0
}}

LETRA DA MÚSICA:
{letra}

Retorne agora SOMENTE o OBJETO JSON.
"""


async def extrair_emocao_individual(idx: int, total: int, letra: str, semaphore: asyncio.Semaphore) -> dict | None:
    if not letra or not str(letra).strip():
        return None

    async with semaphore:
        print(f"🚀 [{idx + 1}/{total}] Enviando letra ({PROVEDOR_LLM.upper()})...")
        prompt = montar_prompt_individual(letra)

        try:
            t0 = time.time()
            raw = await executar_chamada_llm(prompt, is_json=True)
            t1 = time.time()
            raw = raw.replace("```json", "").replace("```", "").strip()
            parsed = json.loads(raw)
            print(f"✅ [{idx + 1}/{total}] Concluído em {t1 - t0:.2f}s")
            if isinstance(parsed, dict):
                return parsed
            elif isinstance(parsed, list) and len(parsed) > 0 and isinstance(parsed[0], dict):
                return parsed[0]
            return None
        except Exception as e:
            print(f"❌ [{idx + 1}/{total}] Erro na extração: {e}")
            return None


from typing import Any

async def extrair_emocoes_batch_bedrock(
    lista_de_letras: list[str],
    chunk_size: int = 5,
    max_concurrency: int = 5,
) -> list[dict[str, float] | None]:
    total = len(lista_de_letras)
    print(
        f"\n⚙️ Iniciando extração emocional ({PROVEDOR_LLM.upper()}) "
        f"de {total} letras (concorrência máx: {max_concurrency})..."
    )

    semaphore = asyncio.Semaphore(max_concurrency)
    tarefas = [
        extrair_emocao_individual(i, total, letra, semaphore)
        for i, letra in enumerate(lista_de_letras)
    ]

    resultados: list[dict[str, Any] | None] = await asyncio.gather(*tarefas)

    print(
        f"🎉 Extração de {total} letras finalizada com sucesso! "
        f"Total de resultados: {len(resultados)}\n"
    )

    return resultados
