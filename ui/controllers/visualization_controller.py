from collections.abc import Callable
from pathlib import Path

from src.visualization.visualization import run_show_mesh
from ui.controllers.base_controller import BaseController


class VisualizationController(BaseController):
    """Controller responsável pela inicialização do visualizador 3D interativo."""

    def __init__(self) -> None:
        super().__init__()

    def show_mesh(
        self,
        selected_paths: dict[str, Path],
        show_toast_callback: Callable[[str, bool], None],
    ) -> None:
        model_path = self.validate_path_exists(
            selected_paths.get("model"),
            "Selecione uma malha 3D válida (.ply ou .obj)!",
            show_toast_callback,
        )
        if not model_path:
            return

        show_toast_callback("Iniciando renderizador PyVista...", False)
        try:
            run_show_mesh(model_path)
        except Exception as e:
            show_toast_callback(f"Erro ao renderizar modelo: {e}", True)


_controller = VisualizationController()


def handle_visualization(
    selected_paths: dict[str, Path],
    show_toast_callback: Callable[[str, bool], None],
) -> None:
    """Wrapper de compatibilidade para chamadas funcionais das views."""
    _controller.show_mesh(
        selected_paths=selected_paths,
        show_toast_callback=show_toast_callback,
    )