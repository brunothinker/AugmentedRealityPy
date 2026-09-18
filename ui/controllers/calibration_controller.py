from pathlib import Path
import shutil
import threading
from typing import Callable, Dict, Optional

from src.camera_calibration.mono_calibration import run_mono_calibration
from src.camera_calibration.stereo_calibration import run_stereo_calibration
from ui.ui_utils import get_user_home_dir


class InterruptedException(Exception):
    """Exceção para interromper o pipeline de calibração via cancel_event."""
    pass


def handle_mono_calibration(
    selected_paths: Dict[str, Path],
    project_name_str: str,
    rows_str: str,
    cols_str: str,
    square_size_str: str,
    show_toast_callback: Callable[[str, bool], None],
    update_progress_callback: Callable[[float], None],
    set_ui_state_callback: Callable[[bool, str], None],
    cancel_event: Optional[threading.Event] = None,
) -> None:
    proj_name_clean = project_name_str.strip()
    if not proj_name_clean:
        show_toast_callback("Preencha o nome do projeto!", is_error=True)
        return

    in_dir: Optional[Path] = selected_paths.get("mono_in")
    if not in_dir or not in_dir.exists():
        show_toast_callback("Selecione uma pasta com os quadros de calibração!", is_error=True)
        return

    try:
        rows = int(rows_str)
        cols = int(cols_str)
        square_size = float(square_size_str.replace(",", "."))

        if rows <= 0 or cols <= 0 or square_size <= 0:
            raise ValueError
    except ValueError:
        show_toast_callback("Número de cantos e tamanho do quadrado devem ser maiores que zero!", is_error=True)
        return

    base_out: Optional[Path] = selected_paths.get("mono_out")
    if not base_out:
        base_out = Path(get_user_home_dir()) / "IC_Output" / "calibracoes"

    out_dir = base_out / proj_name_clean
    set_ui_state_callback(True, "Processando calibração monocular...")

    def checked_progress(val: float):
        if cancel_event and cancel_event.is_set():
            raise InterruptedException()
        update_progress_callback(val)

    try:
        success = run_mono_calibration(
            input_dir=in_dir,
            output_dir=out_dir,
            board_dimensions=(rows, cols),
            square_size_mm=square_size,
            project_name=proj_name_clean,
            progress_callback=checked_progress
        )
        show_toast_callback(
            "✅ Calibração Monocular realizada com sucesso!" if success else "❌ Falha na calibração monocular.",
            is_error=not success
        )
    except InterruptedException:
        if out_dir.exists():
            shutil.rmtree(out_dir, ignore_errors=True)
        show_toast_callback("⚠️ Calibração Monocular cancelada. Arquivos parciais removidos.", is_error=True)
    except Exception as e:
        show_toast_callback(f"Erro inesperado: {e}", is_error=True)
    finally:
        set_ui_state_callback(False, "")


def handle_stereo_calibration(
    selected_paths: Dict[str, Path],
    project_name_str: str,
    rows_str: str,
    cols_str: str,
    square_size_str: str,
    show_toast_callback: Callable[[str, bool], None],
    update_progress_callback: Callable[[float], None],
    set_ui_state_callback: Callable[[bool, str], None],
    cancel_event: Optional[threading.Event] = None,
) -> None:
    proj_name_clean = project_name_str.strip()
    if not proj_name_clean:
        show_toast_callback("Preencha o nome do projeto!", is_error=True)
        return

    left_dir: Optional[Path] = selected_paths.get("stereo_left_in")
    right_dir: Optional[Path] = selected_paths.get("stereo_right_in")

    if not left_dir or not left_dir.exists():
        show_toast_callback("Selecione a pasta de imagens da Câmera Esquerda!", is_error=True)
        return

    if not right_dir or not right_dir.exists():
        show_toast_callback("Selecione a pasta de imagens da Câmera Direita!", is_error=True)
        return

    try:
        rows = int(rows_str)
        cols = int(cols_str)
        square_size = float(square_size_str.replace(",", "."))

        if rows <= 0 or cols <= 0 or square_size <= 0:
            raise ValueError
    except ValueError:
        show_toast_callback("Número de cantos e tamanho do quadrado devem ser maiores que zero!", is_error=True)
        return

    base_out: Optional[Path] = selected_paths.get("stereo_out")
    if not base_out:
        base_out = Path(get_user_home_dir()) / "IC_Output" / "calibracoes"

    out_dir = base_out / proj_name_clean
    set_ui_state_callback(True, "Processando calibração estéreo...")

    def checked_progress_a(v: float):
        if cancel_event and cancel_event.is_set():
            raise InterruptedException()
        update_progress_callback(v * 0.5)

    def checked_progress_b(v: float):
        if cancel_event and cancel_event.is_set():
            raise InterruptedException()
        update_progress_callback(0.5 + v * 0.5)

    try:
        success = run_stereo_calibration(
            input_dir_a=left_dir,
            input_dir_b=right_dir,
            output_dir=out_dir,
            board_dimensions=(rows, cols),
            square_size_mm=square_size,
            project_name=proj_name_clean,
            progress_callback_a=checked_progress_a,
            progress_callback_b=checked_progress_b
        )
        show_toast_callback(
            "✅ Calibração Estéreo realizada com sucesso!" if success else "❌ Falha na calibração estéreo.",
            is_error=not success
        )
    except InterruptedException:
        if out_dir.exists():
            shutil.rmtree(out_dir, ignore_errors=True)
        show_toast_callback("⚠️ Calibração Estéreo cancelada. Arquivos parciais removidos.", is_error=True)
    except Exception as e:
        show_toast_callback(f"Erro inesperado: {e}", is_error=True)
    finally:
        set_ui_state_callback(False, "")