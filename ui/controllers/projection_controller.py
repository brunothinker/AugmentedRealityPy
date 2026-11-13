from collections.abc import Callable
from pathlib import Path

from src.projection.projection import render_synthetic_views
from src.projection.projecton_utils import organize_output_by_camera
from ui.controllers.base_controller import BaseController


class ProjectionController(BaseController):
    """Controller responsável pela renderização de projeções e vistas sintéticas 3D."""

    def __init__(self) -> None:
        super().__init__(default_subfolder="projection")

    def render_projection(
        self,
        selected_paths: dict[str, Path],
        output_folder_name: str,
        show_toast_callback: Callable[[str, bool], None],
        set_ui_state_callback: Callable[[bool, str], None],
    ) -> None:
        colmap_dir = self.validate_path_exists(
            selected_paths.get("colmap_dir"),
            "Selecione um diretório COLMAP válido (com cameras.bin e images.bin)!",
            show_toast_callback,
        )
        if not colmap_dir:
            return

        if not (colmap_dir / "cameras.bin").exists() or not (colmap_dir / "images.bin").exists():
            show_toast_callback(
                "O diretório COLMAP selecionado não possui 'cameras.bin' e 'images.bin'!",
                True,
            )
            return

        mesh_path = self.validate_path_exists(
            selected_paths.get("mesh_file"),
            "Selecione um arquivo de Mesh (.ply/.obj) válido!",
            show_toast_callback,
        )
        if not mesh_path:
            return

        folder_name_clean = self.validate_project_name(output_folder_name, show_toast_callback)
        if not folder_name_clean:
            return

        output_dir = self.resolve_output_dir(selected_paths.get("projection_out"), folder_name_clean)
        output_dir.mkdir(parents=True, exist_ok=True)

        set_ui_state_callback(True, "Renderizando vistas sintéticas...")
        try:
            render_synthetic_views(
                colmap_dir=str(colmap_dir),
                mesh_path=str(mesh_path),
                output_dir=str(output_dir),
            )
            set_ui_state_callback(True, "Organizando subpastas por câmera...")
            organize_output_by_camera(str(output_dir))
            show_toast_callback("✅ Projeções geradas e organizadas com sucesso!", False)
        except Exception as e:
            show_toast_callback(f"Erro no processo de projeção: {e}", True)
        finally:
            set_ui_state_callback(False, "")


_controller = ProjectionController()


def handle_render_projection(
    selected_paths: dict[str, Path],
    output_folder_name: str,
    show_toast_callback: Callable[[str, bool], None],
    set_ui_state_callback: Callable[[bool, str], None],
) -> None:
    """Wrapper de compatibilidade para chamadas funcionais das views."""
    _controller.render_projection(
        selected_paths=selected_paths,
        output_folder_name=output_folder_name,
        show_toast_callback=show_toast_callback,
        set_ui_state_callback=set_ui_state_callback,
    )