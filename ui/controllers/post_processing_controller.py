from pathlib import Path
import shutil
import threading
from typing import Callable, Dict, Optional

from src.post_processing.clahe import run_clahe_images
from src.post_processing.resize import run_resize_images
from ui.ui_utils import get_user_home_dir


class InterruptedException(Exception):
    pass


def handle_clahe(
    selected_paths: Dict[str, Path],
    clip_limit_str: str,
    tile_size_str: str,
    show_toast_callback: Callable[[str, bool], None],
    update_progress_callback: Callable[[float], None],
    set_ui_state_callback: Callable[[bool, str], None],
    cancel_event: Optional[threading.Event] = None,
) -> None:
    in_dir: Optional[Path] = selected_paths.get("clahe_in")
    if not in_dir or not in_dir.exists():
        show_toast_callback("Selecione uma pasta de entrada válida!", is_error=True)
        return

    try:
        clip_limit = float(clip_limit_str.replace(",", "."))
        tile_val = int(tile_size_str)
        tile_size = (tile_val, tile_val)

        if clip_limit <= 0 or tile_val <= 0:
            raise ValueError
    except ValueError:
        show_toast_callback("Valores de Clip Limit e Tile Size devem ser positivos!", is_error=True)
        return

    out_dir: Optional[Path] = selected_paths.get("clahe_out")
    if not out_dir:
        out_dir = Path(get_user_home_dir()) / "IC_Output" / f"{in_dir.name}_clahe"

    set_ui_state_callback(True, "Aplicando realce CLAHE...")

    def checked_progress(val: float):
        if cancel_event and cancel_event.is_set():
            raise InterruptedException()
        update_progress_callback(val)

    try:
        success = run_clahe_images(
            input_dir=in_dir,
            output_dir=out_dir,
            clip_limit=clip_limit,
            tile_size=tile_size,
            progress_callback=checked_progress,
        )
        show_toast_callback(
            "✅ CLAHE aplicado com sucesso!" if success else "❌ Falha no processamento CLAHE.",
            is_error=not success,
        )
    except InterruptedException:
        if out_dir.exists():
            shutil.rmtree(out_dir, ignore_errors=True)
        show_toast_callback("⚠️ Processamento CLAHE cancelado. Diretório limpo.", is_error=True)
    except Exception as e:
        show_toast_callback(f"Erro inesperado: {e}", is_error=True)
    finally:
        set_ui_state_callback(False, "")


def handle_resize(
    selected_paths: Dict[str, Path],
    width_str: str,
    height_str: str,
    show_toast_callback: Callable[[str, bool], None],
    update_progress_callback: Callable[[float], None],
    set_ui_state_callback: Callable[[bool, str], None],
    cancel_event: Optional[threading.Event] = None,
) -> None:
    in_dir: Optional[Path] = selected_paths.get("resize_in")
    if not in_dir or not in_dir.exists():
        show_toast_callback("Selecione uma pasta de entrada válida!", is_error=True)
        return

    try:
        target_w = int(width_str)
        target_h = int(height_str)
        if target_w <= 0 or target_h <= 0:
            raise ValueError
    except ValueError:
        show_toast_callback("Valores de largura e altura devem ser inteiros positivos!", is_error=True)
        return

    out_dir: Optional[Path] = selected_paths.get("resize_out")
    if not out_dir:
        out_dir = Path(get_user_home_dir()) / "IC_Output" / f"{in_dir.name}_resized"

    set_ui_state_callback(True, "Redimensionando imagens...")

    def checked_progress(val: float):
        if cancel_event and cancel_event.is_set():
            raise InterruptedException()
        update_progress_callback(val)

    try:
        success = run_resize_images(
            input_dir=in_dir,
            output_dir=out_dir,
            target_size=(target_h, target_w),
            progress_callback=checked_progress,
        )
        show_toast_callback(
            "✅ Redimensionamento concluído com sucesso!" if success else "❌ Falha no Redimensionamento.",
            is_error=not success,
        )
    except InterruptedException:
        if out_dir.exists():
            shutil.rmtree(out_dir, ignore_errors=True)
        show_toast_callback("⚠️ Redimensionamento cancelado. Diretório limpo.", is_error=True)
    except Exception as e:
        show_toast_callback(f"Erro inesperado: {e}", is_error=True)
    finally:
        set_ui_state_callback(False, "")