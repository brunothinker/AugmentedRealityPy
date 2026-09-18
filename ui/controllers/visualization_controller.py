from pathlib import Path
from typing import Callable, Dict, Optional

from src.visualization.visualization import run_show_mesh


def handle_visualization(
    selected_paths: Dict[str, Path],
    show_toast_callback: Callable[[str, bool], None],
) -> None:
    """Orquestra a inicialização da janela de visualização 3D interativa via PyVista.

    Valida a existência e integridade do arquivo de malha/nuvem de pontos selecionado
    (.ply ou .obj), notifica o usuário via toast e dispara a renderização em janela dedicada.

    Args:
        selected_paths: Dicionário contendo os caminhos selecionados na UI (ex: 'model').
        show_toast_callback: Callback para exibição de notificações toast na UI (mensagem, is_error).
    """
    # 1. Validação da seleção e existência do arquivo de malha 3D
    model_path: Optional[Path] = selected_paths.get("model")

    if not model_path or not model_path.exists():
        show_toast_callback("Selecione uma malha 3D válida (.ply ou .obj)!", is_error=True)
        return

    # 2. Notificação de início de renderização
    show_toast_callback("Iniciando renderizador PyVista...", is_error=False)

    # 3. Disparo da janela interativa do PyVista
    try:
        run_show_mesh(model_path)
    except Exception as e:
        show_toast_callback(f"Erro ao renderizar modelo: {e}", is_error=True)