from collections import Counter

async def contar_elementos(lista_generos: list[str]) -> dict[str, int]:
    contagem = Counter(lista_generos)
    dict_contagem = dict(contagem.most_common()[:6])

    return dict_contagem