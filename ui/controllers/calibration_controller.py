import threading
from collections.abc import Callable
from pathlib import Path

from src.camera_calibration.mono_calibration import run_mono_calibration
from src.camera_calibration.stereo_calibration import run_stereo_calibration
from ui.controllers.base_controller import BaseController


class CalibrationController(BaseController):
    """Controller responsável pelas calibrações monocular e estéreo."""

    def __init__(self) -> None:
        super().__init__(default_subfolder="calibracoes")

    @staticmethod
    def _validate_board_params(
        rows_str: str,
        cols_str: str,
        square_size_str: str,
        show_toast: Callable[[str, bool], None],
    ) -> tuple[int, int, float] | None:
        try:
            rows = int(rows_str)
            cols = int(cols_str)
            square_size = float(square_size_str.replace(",", "."))
            if rows <= 0 or cols <= 0 or square_size <= 0:
                raise ValueError
            return rows, cols, square_size
        except ValueError:
            show_toast(
                "Número de cantos e tamanho do quadrado devem ser maiores que zero!",
                True,
            )
            return None

    def calibrate_mono(
        self,
        selected_paths: dict[str, Path],
        project_name_str: str,
        rows_str: str,
        cols_str: str,
        square_size_str: str,
        show_toast_callback: Callable[[str, bool], None],
        update_progress_callback: Callable[[float], None],
        set_ui_state_callback: Callable[[bool, str], None],
        cancel_event: threading.Event | None = None,
    ) -> None:
        proj_name_clean = self.validate_project_name(project_name_str, show_toast_callback)
        if not proj_name_clean:
            return

        in_dir = self.validate_path_exists(
            selected_paths.get("mono_in"),
            "Selecione uma pasta com os quadros de calibração!",
            show_toast_callback,
        )
        if not in_dir:
            return

        board_params = self._validate_board_params(
            rows_str, cols_str, square_size_str, show_toast_callback
        )
        if not board_params:
            return
        rows, cols, square_size = board_params

        out_dir = self.resolve_output_dir(selected_paths.get("mono_out"), proj_name_clean)
        checked_progress = self.make_checked_progress(update_progress_callback, cancel_event)

        self._execute_task(
            task_fn=lambda: run_mono_calibration(
                input_dir=in_dir,
                output_dir=out_dir,
                board_dimensions=(rows, cols),
                square_size_mm=square_size,
                project_name=proj_name_clean,
                progress_callback=checked_progress,
            ),
            out_dir=out_dir,
            running_msg="Processando calibração monocular...",
            success_msg="✅ Calibração Monocular realizada com sucesso!",
            fail_msg="❌ Falha na calibração monocular.",
            cancel_msg="⚠️ Calibração Monocular cancelada. Arquivos parciais removidos.",
            show_toast=show_toast_callback,
            set_ui_state=set_ui_state_callback,
        )

    def calibrate_stereo(
        self,
        selected_paths: dict[str, Path],
        project_name_str: str,
        rows_str: str,
        cols_str: str,
        square_size_str: str,
        show_toast_callback: Callable[[str, bool], None],
        update_progress_callback: Callable[[float], None],
        set_ui_state_callback: Callable[[bool, str], None],
        cancel_event: threading.Event | None = None,
    ) -> None:
        proj_name_clean = self.validate_project_name(project_name_str, show_toast_callback)
        if not proj_name_clean:
            return

        left_dir = self.validate_path_exists(
            selected_paths.get("stereo_left_in"),
            "Selecione a pasta de imagens da Câmera Esquerda!",
            show_toast_callback,
        )
        if not left_dir:
            return

        right_dir = self.validate_path_exists(
            selected_paths.get("stereo_right_in"),
            "Selecione a pasta de imagens da Câmera Direita!",
            show_toast_callback,
        )
        if not right_dir:
            return

        board_params = self._validate_board_params(
            rows_str, cols_str, square_size_str, show_toast_callback
        )
        if not board_params:
            return
        rows, cols, square_size = board_params

        out_dir = self.resolve_output_dir(selected_paths.get("stereo_out"), proj_name_clean)
        checked_progress_a = self.make_checked_progress(
            update_progress_callback, cancel_event, scale=0.5, offset=0.0
        )
        checked_progress_b = self.make_checked_progress(
            update_progress_callback, cancel_event, scale=0.5, offset=0.5
        )

        self._execute_task(
            task_fn=lambda: run_stereo_calibration(
                input_dir_a=left_dir,
                input_dir_b=right_dir,
                output_dir=out_dir,
                board_dimensions=(rows, cols),
                square_size_mm=square_size,
                project_name=proj_name_clean,
                progress_callback_a=checked_progress_a,
                progress_callback_b=checked_progress_b,
            ),
            out_dir=out_dir,
            running_msg="Processando calibração estéreo...",
            success_msg="✅ Calibração Estéreo realizada com sucesso!",
            fail_msg="❌ Falha na calibração estéreo.",
            cancel_msg="⚠️ Calibração Estéreo cancelada. Arquivos parciais removidos.",
            show_toast=show_toast_callback,
            set_ui_state=set_ui_state_callback,
        )


_controller = CalibrationController()


def handle_mono_calibration(
    selected_paths: dict[str, Path],
    project_name_str: str,
    rows_str: str,
    cols_str: str,
    square_size_str: str,
    show_toast_callback: Callable[[str, bool], None],
    update_progress_callback: Callable[[float], None],
    set_ui_state_callback: Callable[[bool, str], None],
    cancel_event: threading.Event | None = None,
) -> None:
    """Wrapper de compatibilidade para chamadas funcionais das views."""
    _controller.calibrate_mono(
        selected_paths=selected_paths,
        project_name_str=project_name_str,
        rows_str=rows_str,
        cols_str=cols_str,
        square_size_str=square_size_str,
        show_toast_callback=show_toast_callback,
        update_progress_callback=update_progress_callback,
        set_ui_state_callback=set_ui_state_callback,
        cancel_event=cancel_event,
    )


def handle_stereo_calibration(
    selected_paths: dict[str, Path],
    project_name_str: str,
    rows_str: str,
    cols_str: str,
    square_size_str: str,
    show_toast_callback: Callable[[str, bool], None],
    update_progress_callback: Callable[[float], None],
    set_ui_state_callback: Callable[[bool, str], None],
    cancel_event: threading.Event | None = None,
) -> None:
    """Wrapper de compatibilidade para chamadas funcionais das views."""
    _controller.calibrate_stereo(
        selected_paths=selected_paths,
        project_name_str=project_name_str,
        rows_str=rows_str,
        cols_str=cols_str,
        square_size_str=square_size_str,
        show_toast_callback=show_toast_callback,
        update_progress_callback=update_progress_callback,
        set_ui_state_callback=set_ui_state_callback,
        cancel_event=cancel_event,
    )