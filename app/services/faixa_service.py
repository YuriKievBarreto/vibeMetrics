from app.core.database import async_engine
from app.services.spotipy_service import get_top_faixas
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.faixa import FaixaCreate
from app.repositories.faixa_repository import salvar_faixas_em_batch
from app.services.extracao_de_letras import buscar_letras_em_batch
from app.services.emotion_extraction_service import extrair_emocoes_batch_bedrock
from app.models.faixa import UnifiedTrack
from app.services.usuario_top_faixa_service import salvar_relacionamentos_top_faixas



async def salvar_top_faixas(user_id: str, access_token: str):
    print("iniciando salvamento de top faixas do usuario no banco de dados")

    async with AsyncSession(async_engine) as db:

        print("puxando top 10 faixas de todos os periodos de tempo")
        top_faixas = await get_top_faixas(
            access_token,
            quantitade=1,
            time_ranges=["short_term", "medium_term", "long_term"],
        )

        top_faixas_unicas: dict[str, UnifiedTrack] = {}
        tuplas_vistas = set()

        for id_faixa, faixa_dados in top_faixas.tracks.items():
            chave_de_unicidade = (
                faixa_dados.artista_principal,
                faixa_dados.nome_faixa,
            )

            if chave_de_unicidade not in tuplas_vistas:
                tuplas_vistas.add(chave_de_unicidade)
                top_faixas_unicas[id_faixa] = faixa_dados

        print("--------------------------")

        lista_musicas = [
            (faixa.artista_principal, faixa.nome_faixa)
            for faixa in top_faixas_unicas.values()
        ]

        print("extraindo letras de musicas")
        letras_musicas = await buscar_letras_em_batch(lista_musicas)

        print("TAMANHO", len(letras_musicas))

        for i, (_, dados_faixa) in enumerate(top_faixas_unicas.items()):
            dados_faixa.letra = letras_musicas[i]["letra"]

        print("extraindo emocoes")

        faixas_com_letra = [
            faixa
            for faixa in top_faixas_unicas.values()
            if faixa.letra is not None
        ]

        lista_letras = [faixa.letra for faixa in faixas_com_letra]

        if lista_letras:
            lista_emocoes = await extrair_emocoes_batch_bedrock(
                lista_letras,
                chunk_size=5,
            )

            for faixa, emocoes in zip(faixas_com_letra, lista_emocoes):
                faixa.emocoes = emocoes

        for faixa in top_faixas_unicas.values():
            if faixa.emocoes is None:
                faixa.emocoes = None

        rank_map = {}
        lista_faixas_para_adicionar = []

        print("AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA")

        for faixa_id, valor_faixa in top_faixas_unicas.items():
            print(valor_faixa)

            faixa_create = FaixaCreate(
                id_faixa=valor_faixa.id_faixa,
                nome_faixa=valor_faixa.nome_faixa,
                emocoes=valor_faixa.emocoes,
                duracao_ms=valor_faixa.duracao_ms,
                popularidade=valor_faixa.popularidade,
                album=valor_faixa.album,
                link_imagem=valor_faixa.link_imagem,
                letra_faixa=valor_faixa.letra,
                artista_principal=valor_faixa.artista_principal,
            )

            lista_faixas_para_adicionar.append(faixa_create)

            rank_map[faixa_id] = {
                "short": valor_faixa.short_term_rank,
                "medium": valor_faixa.medium_term_rank,
                "long": valor_faixa.long_term_rank,
            }

        print("salvando/atualizando faixas no banco de dados (Passo 1/2)")

        await salvar_faixas_em_batch(db, lista_faixas_para_adicionar)

        faixa_ids = list(top_faixas_unicas.keys())

        await salvar_relacionamentos_top_faixas(
            db,
            user_id,
            faixa_ids,
            rank_map,
        )