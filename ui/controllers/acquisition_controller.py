from pathlib import Path
import shutil
import threading
from typing import Callable, Dict, Optional

from src.acquisition.extract_frames import run_extract_frames
from ui.ui_utils import get_user_home_dir


class InterruptedException(Exception):
    pass


def handle_extract_frames(
    selected_paths: Dict[str, Path],
    project_name: str,
    fps_str: str,
    show_toast_callback: Callable[[str, bool], None],
    update_progress_callback: Callable[[float], None],
    set_ui_state_callback: Callable[[bool, str], None],
    cancel_event: Optional[threading.Event] = None,
) -> None:
    try:
        fps = int(fps_str)
        if fps <= 0:
            raise ValueError
    except ValueError:
        show_toast_callback("O FPS deve ser um número inteiro positivo!", is_error=True)
        return

    video_path: Optional[Path] = selected_paths.get("video")
    if not video_path or not video_path.exists():
        show_toast_callback("Selecione um arquivo de vídeo válido!", is_error=True)
        return

    proj_name_clean = project_name.strip()
    if not proj_name_clean:
        show_toast_callback("Preencha o nome do projeto!", is_error=True)
        return

    base_out: Optional[Path] = selected_paths.get("output_dir")
    if not base_out:
        base_out = Path(get_user_home_dir()) / "IC_Output"

    out_dir = base_out / proj_name_clean
    set_ui_state_callback(True, "Extraindo frames...")

    def checked_progress(val: float):
        if cancel_event and cancel_event.is_set():
            raise InterruptedException()
        update_progress_callback(val)

    try:
        success = run_extract_frames(
            video_path=video_path,
            output_dir=out_dir,
            desired_fps=fps,
            progress_callback=checked_progress,
        )
        show_toast_callback(
            "✅ Extração concluída com sucesso!" if success else "❌ Falha na extração dos frames.",
            is_error=not success,
        )
    except InterruptedException:
        # Apaga a pasta incompleta do projeto se o usuário cancelar
        if out_dir.exists():
            shutil.rmtree(out_dir, ignore_errors=True)
        show_toast_callback("⚠️ Processamento cancelado. Arquivos parciais removidos.", is_error=True)
    except Exception as e:
        show_toast_callback(f"Erro inesperado: {e}", is_error=True)
    finally:
        set_ui_state_callback(False, "")