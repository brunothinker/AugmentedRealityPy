import threading
from collections.abc import Callable
from pathlib import Path

from src.acquisition.extract_frames import run_extract_frames
from ui.controllers.base_controller import BaseController


class AcquisitionController(BaseController):
    """Controller responsável pela etapa de aquisição e extração de frames de vídeo."""

    def __init__(self) -> None:
        super().__init__(default_subfolder="")

    def extract_frames(
        self,
        selected_paths: dict[str, Path],
        project_name: str,
        fps_str: str,
        show_toast_callback: Callable[[str, bool], None],
        update_progress_callback: Callable[[float], None],
        set_ui_state_callback: Callable[[bool, str], None],
        cancel_event: threading.Event | None = None,
    ) -> None:
        try:
            fps = int(fps_str)
            if fps <= 0:
                raise ValueError
        except ValueError:
            show_toast_callback("O FPS deve ser um número inteiro positivo!", True)
            return

        video_path = self.validate_path_exists(
            selected_paths.get("video"),
            "Selecione um arquivo de vídeo válido!",
            show_toast_callback,
        )
        if not video_path:
            return

        proj_name_clean = self.validate_project_name(project_name, show_toast_callback)
        if not proj_name_clean:
            return

        out_dir = self.resolve_output_dir(selected_paths.get("output_dir"), proj_name_clean)
        checked_progress = self.make_checked_progress(update_progress_callback, cancel_event)

        self._execute_task(
            task_fn=lambda: run_extract_frames(
                video_path=video_path,
                output_dir=out_dir,
                desired_fps=fps,
                progress_callback=checked_progress,
            ),
            out_dir=out_dir,
            running_msg="Extraindo frames...",
            success_msg="✅ Extração concluída com sucesso!",
            fail_msg="❌ Falha na extração dos frames.",
            cancel_msg="⚠️ Processamento cancelado. Arquivos parciais removidos.",
            show_toast=show_toast_callback,
            set_ui_state=set_ui_state_callback,
        )


_controller = AcquisitionController()


def handle_extract_frames(
    selected_paths: dict[str, Path],
    project_name: str,
    fps_str: str,
    show_toast_callback: Callable[[str, bool], None],
    update_progress_callback: Callable[[float], None],
    set_ui_state_callback: Callable[[bool, str], None],
    cancel_event: threading.Event | None = None,
) -> None:
    """Wrapper de compatibilidade para chamadas funcionais das views."""
    _controller.extract_frames(
        selected_paths=selected_paths,
        project_name=project_name,
        fps_str=fps_str,
        show_toast_callback=show_toast_callback,
        update_progress_callback=update_progress_callback,
        set_ui_state_callback=set_ui_state_callback,
        cancel_event=cancel_event,
    )