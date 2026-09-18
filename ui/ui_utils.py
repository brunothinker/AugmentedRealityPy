from pathlib import Path


def get_user_home_dir() -> str:
    """Retorna o caminho absoluto do diretório HOME do usuário atual.

    Returns:
        str: Caminho absoluto para a pasta HOME do usuário no sistema operacional.
    """
    return str(Path.home().resolve())