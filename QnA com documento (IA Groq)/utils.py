import os

def garantir_pasta_conversas():
    """Garante que a pasta 'conversas' exista."""
    if not os.path.exists('conversas'):
        os.makedirs('conversas')


def criar_pasta_conversa(nome_conversa: str) -> str:
    """Cria uma subpasta para uma nova conversa e retorna o caminho."""
    caminho = os.path.join('conversas', nome_conversa)
    if not os.path.exists(caminho):
        os.makedirs(caminho)
    return caminho 