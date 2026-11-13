import threading
from collections.abc import Callable
from pathlib import Path

from src.post_processing.clahe import run_clahe_images
from src.post_processing.resize import run_resize_images
from ui.controllers.base_controller import BaseController


class PostProcessingController(BaseController):
    """Controller responsável pelas etapas de pré/pós-processamento (CLAHE e Resize)."""

    def __init__(self) -> None:
        super().__init__(default_subfolder="")

    def apply_clahe(
        self,
        selected_paths: dict[str, Path],
        clip_limit_str: str,
        tile_size_str: str,
        show_toast_callback: Callable[[str, bool], None],
        update_progress_callback: Callable[[float], None],
        set_ui_state_callback: Callable[[bool, str], None],
        cancel_event: threading.Event | None = None,
    ) -> None:
        in_dir = self.validate_path_exists(
            selected_paths.get("clahe_in"),
            "Selecione uma pasta de entrada válida!",
            show_toast_callback,
        )
        if not in_dir:
            return

        try:
            clip_limit = float(clip_limit_str.replace(",", "."))
            tile_val = int(tile_size_str)
            tile_size = (tile_val, tile_val)
            if clip_limit <= 0 or tile_val <= 0:
                raise ValueError
        except ValueError:
            show_toast_callback("Valores de Clip Limit e Tile Size devem ser positivos!", True)
            return

        out_dir = selected_paths.get("clahe_out") or self.resolve_output_dir(
            None, f"{in_dir.name}_clahe"
        )
        checked_progress = self.make_checked_progress(update_progress_callback, cancel_event)

        self._execute_task(
            task_fn=lambda: run_clahe_images(
                input_dir=in_dir,
                output_dir=out_dir,
                clip_limit=clip_limit,
                tile_size=tile_size,
                progress_callback=checked_progress,
            ),
            out_dir=out_dir,
            running_msg="Aplicando realce CLAHE...",
            success_msg="✅ CLAHE aplicado com sucesso!",
            fail_msg="❌ Falha no processamento CLAHE.",
            cancel_msg="⚠️ Processamento CLAHE cancelado. Diretório limpo.",
            show_toast=show_toast_callback,
            set_ui_state=set_ui_state_callback,
        )

    def resize_images(
        self,
        selected_paths: dict[str, Path],
        width_str: str,
        height_str: str,
        show_toast_callback: Callable[[str, bool], None],
        update_progress_callback: Callable[[float], None],
        set_ui_state_callback: Callable[[bool, str], None],
        cancel_event: threading.Event | None = None,
    ) -> None:
        in_dir = self.validate_path_exists(
            selected_paths.get("resize_in"),
            "Selecione uma pasta de entrada válida!",
            show_toast_callback,
        )
        if not in_dir:
            return

        try:
            target_w = int(width_str)
            target_h = int(height_str)
            if target_w <= 0 or target_h <= 0:
                raise ValueError
        except ValueError:
            show_toast_callback("Valores de largura e altura devem ser inteiros positivos!", True)
            return

        out_dir = selected_paths.get("resize_out") or self.resolve_output_dir(
            None, f"{in_dir.name}_resized"
        )
        checked_progress = self.make_checked_progress(update_progress_callback, cancel_event)

        self._execute_task(
            task_fn=lambda: run_resize_images(
                input_dir=in_dir,
                output_dir=out_dir,
                target_size=(target_h, target_w),
                progress_callback=checked_progress,
            ),
            out_dir=out_dir,
            running_msg="Redimensionando imagens...",
            success_msg="✅ Redimensionamento concluído com sucesso!",
            fail_msg="❌ Falha no Redimensionamento.",
            cancel_msg="⚠️ Redimensionamento cancelado. Diretório limpo.",
            show_toast=show_toast_callback,
            set_ui_state=set_ui_state_callback,
        )


_controller = PostProcessingController()


def handle_clahe(
    selected_paths: dict[str, Path],
    clip_limit_str: str,
    tile_size_str: str,
    show_toast_callback: Callable[[str, bool], None],
    update_progress_callback: Callable[[float], None],
    set_ui_state_callback: Callable[[bool, str], None],
    cancel_event: threading.Event | None = None,
) -> None:
    """Wrapper de compatibilidade para chamadas funcionais das views."""
    _controller.apply_clahe(
        selected_paths=selected_paths,
        clip_limit_str=clip_limit_str,
        tile_size_str=tile_size_str,
        show_toast_callback=show_toast_callback,
        update_progress_callback=update_progress_callback,
        set_ui_state_callback=set_ui_state_callback,
        cancel_event=cancel_event,
    )


def handle_resize(
    selected_paths: dict[str, Path],
    width_str: str,
    height_str: str,
    show_toast_callback: Callable[[str, bool], None],
    update_progress_callback: Callable[[float], None],
    set_ui_state_callback: Callable[[bool, str], None],
    cancel_event: threading.Event | None = None,
) -> None:
    """Wrapper de compatibilidade para chamadas funcionais das views."""
    _controller.resize_images(
        selected_paths=selected_paths,
        width_str=width_str,
        height_str=height_str,
        show_toast_callback=show_toast_callback,
        update_progress_callback=update_progress_callback,
        set_ui_state_callback=set_ui_state_callback,
        cancel_event=cancel_event,
    )