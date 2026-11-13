import threading
from collections.abc import Callable
from pathlib import Path

from src.reconstruction.mono_reconstruction import run_mono_reconstruction
from src.reconstruction.stereo_reconstruction import run_stereo_reconstruction
from ui.controllers.base_controller import BaseController


class ReconstructionController(BaseController):
    """Controller responsável pelos pipelines de reconstrução 3D monocular e estéreo."""

    def __init__(self) -> None:
        super().__init__(default_subfolder="reconstrucoes")

    def reconstruct_mono(
        self,
        selected_paths: dict[str, Path],
        project_name: str,
        show_toast_callback: Callable[[str, bool], None],
        update_progress_callback: Callable[[float, str], None],
        set_ui_state_callback: Callable[[bool, str], None],
        cancel_event: threading.Event | None = None,
    ) -> None:
        proj_name_clean = self.validate_project_name(project_name, show_toast_callback)
        if not proj_name_clean:
            return

        images_dir = self.validate_path_exists(
            selected_paths.get("mono_rec_images"),
            "Selecione a pasta com as imagens de entrada!",
            show_toast_callback,
        )
        if not images_dir:
            return

        out_dir = self.resolve_output_dir(selected_paths.get("mono_rec_out"), proj_name_clean)
        checked_progress = self.make_checked_status_progress(update_progress_callback, cancel_event)

        self._execute_task(
            task_fn=lambda: run_mono_reconstruction(
                pasta_frames=images_dir,
                pasta_projeto_saida=out_dir,
                progress_callback=checked_progress,
            ),
            out_dir=out_dir,
            running_msg="Iniciando reconstrução monocular (COLMAP)...",
            success_msg="Reconstrução Monocular concluída com sucesso!",
            fail_msg="Falha na reconstrução monocular.",
            cancel_msg="⚠️ Reconstrução Monocular cancelada. Pasta de saída removida.",
            show_toast=show_toast_callback,
            set_ui_state=set_ui_state_callback,
        )

    def reconstruct_stereo(
        self,
        selected_paths: dict[str, Path],
        project_name: str,
        baseline_str: str,
        show_toast_callback: Callable[[str, bool], None],
        update_progress_callback: Callable[[float, str], None],
        set_ui_state_callback: Callable[[bool, str], None],
        cancel_event: threading.Event | None = None,
    ) -> None:
        proj_name_clean = self.validate_project_name(project_name, show_toast_callback)
        if not proj_name_clean:
            return

        cam_left_dir = selected_paths.get("stereo_rec_left")
        cam_right_dir = selected_paths.get("stereo_rec_right")
        if (
            not cam_left_dir
            or not cam_left_dir.exists()
            or not cam_right_dir
            or not cam_right_dir.exists()
        ):
            show_toast_callback("Selecione ambas as pastas de câmeras (Esquerda e Direita)!", True)
            return

        images_dir = cam_left_dir.parent

        try:
            baseline = float(baseline_str.replace(",", "."))
            if baseline <= 0:
                raise ValueError
        except ValueError:
            show_toast_callback("Informe um valor positivo para a baseline (metros)!", True)
            return

        out_dir = self.resolve_output_dir(selected_paths.get("stereo_rec_out"), proj_name_clean)
        checked_progress = self.make_checked_status_progress(update_progress_callback, cancel_event)

        self._execute_task(
            task_fn=lambda: run_stereo_reconstruction(
                pasta_frames=images_dir,
                pasta_projeto_saida=out_dir,
                baseline_metros=baseline,
                progress_callback=checked_progress,
            ),
            out_dir=out_dir,
            running_msg="Iniciando pipeline de reconstrução estéreo...",
            success_msg="Reconstrução Estéreo concluída com sucesso!",
            fail_msg="Falha na reconstrução estéreo.",
            cancel_msg="⚠️ Reconstrução Estéreo cancelada. Diretório de saída limpo.",
            show_toast=show_toast_callback,
            set_ui_state=set_ui_state_callback,
        )


_controller = ReconstructionController()


def handle_mono_reconstruction(
    selected_paths: dict[str, Path],
    project_name: str,
    show_toast_callback: Callable[[str, bool], None],
    update_progress_callback: Callable[[float, str], None],
    set_ui_state_callback: Callable[[bool, str], None],
    cancel_event: threading.Event | None = None,
) -> None:
    """Wrapper de compatibilidade para chamadas funcionais das views."""
    _controller.reconstruct_mono(
        selected_paths=selected_paths,
        project_name=project_name,
        show_toast_callback=show_toast_callback,
        update_progress_callback=update_progress_callback,
        set_ui_state_callback=set_ui_state_callback,
        cancel_event=cancel_event,
    )


def handle_stereo_reconstruction(
    selected_paths: dict[str, Path],
    project_name: str,
    baseline_str: str,
    show_toast_callback: Callable[[str, bool], None],
    update_progress_callback: Callable[[float, str], None],
    set_ui_state_callback: Callable[[bool, str], None],
    cancel_event: threading.Event | None = None,
) -> None:
    """Wrapper de compatibilidade para chamadas funcionais das views."""
    _controller.reconstruct_stereo(
        selected_paths=selected_paths,
        project_name=project_name,
        baseline_str=baseline_str,
        show_toast_callback=show_toast_callback,
        update_progress_callback=update_progress_callback,
        set_ui_state_callback=set_ui_state_callback,
        cancel_event=cancel_event,
    )