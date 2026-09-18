from pathlib import Path
import shutil
import threading
from typing import Callable, Dict, Optional

from src.reconstruction.mono_reconstruction import run_mono_reconstruction
from src.reconstruction.stereo_reconstruction import run_stereo_reconstruction
from ui.ui_utils import get_user_home_dir


class InterruptedException(Exception):
    """Exceção para interromper as etapas da reconstrução via cancel_event."""
    pass


def handle_mono_reconstruction(
    selected_paths: Dict[str, Path],
    project_name: str,
    show_toast_callback: Callable[[str, bool], None],
    update_progress_callback: Callable[[float, str], None],
    set_ui_state_callback: Callable[[bool, str], None],
    cancel_event: Optional[threading.Event] = None,
) -> None:
    proj_name_clean = project_name.strip()
    if not proj_name_clean:
        show_toast_callback("Preencha o nome do projeto!", is_error=True)
        return

    images_dir: Optional[Path] = selected_paths.get("mono_rec_images")
    if not images_dir or not images_dir.exists():
        show_toast_callback("Selecione a pasta com as imagens de entrada!", is_error=True)
        return

    base_out: Optional[Path] = selected_paths.get("mono_rec_out")
    if not base_out:
        base_out = Path(get_user_home_dir()) / "IC_Output" / "reconstrucoes"

    out_dir = base_out / proj_name_clean
    set_ui_state_callback(True, "Iniciando reconstrução monocular (COLMAP)...")

    def checked_progress(val: float, msg: str = ""):
        if cancel_event and cancel_event.is_set():
            raise InterruptedException()
        update_progress_callback(val, msg)

    try:
        success = run_mono_reconstruction(
            pasta_frames=images_dir,
            pasta_projeto_saida=out_dir,
            progress_callback=checked_progress
        )
        show_toast_callback(
            "Reconstrução Monocular concluída com sucesso!" if success else "Falha na reconstrução monocular.",
            is_error=not success
        )
    except InterruptedException:
        if out_dir.exists():
            shutil.rmtree(out_dir, ignore_errors=True)
        show_toast_callback("⚠️ Reconstrução Monocular cancelada. Pasta de saída removida.", is_error=True)
    except Exception as e:
        show_toast_callback(f"Erro inesperado: {e}", is_error=True)
    finally:
        set_ui_state_callback(False, "")


def handle_stereo_reconstruction(
    selected_paths: Dict[str, Path],
    project_name: str,
    baseline_str: str,
    show_toast_callback: Callable[[str, bool], None],
    update_progress_callback: Callable[[float, str], None],
    set_ui_state_callback: Callable[[bool, str], None],
    cancel_event: Optional[threading.Event] = None,
) -> None:
    proj_name_clean = project_name.strip()
    if not proj_name_clean:
        show_toast_callback("Preencha o nome do projeto!", is_error=True)
        return

    cam_left_dir: Optional[Path] = selected_paths.get("stereo_rec_left")
    cam_right_dir: Optional[Path] = selected_paths.get("stereo_rec_right")

    if not cam_left_dir or not cam_left_dir.exists() or not cam_right_dir or not cam_right_dir.exists():
        show_toast_callback("Selecione ambas as pastas de câmeras (Esquerda e Direita)!", is_error=True)
        return

    images_dir: Path = cam_left_dir.parent

    try:
        baseline = float(baseline_str.replace(",", "."))
        if baseline <= 0:
            raise ValueError
    except ValueError:
        show_toast_callback("Informe um valor positivo para a baseline (metros)!", is_error=True)
        return

    base_out: Optional[Path] = selected_paths.get("stereo_rec_out")
    if not base_out:
        base_out = Path(get_user_home_dir()) / "IC_Output" / "reconstrucoes"

    out_dir = base_out / proj_name_clean
    set_ui_state_callback(True, "Iniciando pipeline de reconstrução estéreo...")

    def checked_progress(val: float, msg: str = ""):
        if cancel_event and cancel_event.is_set():
            raise InterruptedException()
        update_progress_callback(val, msg)

    try:
        success = run_stereo_reconstruction(
            pasta_frames=images_dir,
            pasta_projeto_saida=out_dir,
            baseline_metros=baseline,
            progress_callback=checked_progress
        )
        show_toast_callback(
            "Reconstrução Estéreo concluída com sucesso!" if success else "Falha na reconstrução estéreo.",
            is_error=not success
        )
    except InterruptedException:
        if out_dir.exists():
            shutil.rmtree(out_dir, ignore_errors=True)
        show_toast_callback("⚠️ Reconstrução Estéreo cancelada. Diretório de saída limpo.", is_error=True)
    except Exception as e:
        show_toast_callback(f"Erro inesperado: {e}", is_error=True)
    finally:
        set_ui_state_callback(False, "")