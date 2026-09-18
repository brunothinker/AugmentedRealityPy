from pathlib import Path
import shutil
import threading
from typing import Callable, Dict, Optional

from src.acquisition.extract_frames import run_extract_frames
from ui.ui_utils import get_user_home_dir


class InterruptedException(Exception):
    """Exceção customizada lançada para interromper o fluxo de execução quando o utilizador cancela o processo."""
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
    """Orquestra a extração de fotogramas de um vídeo de entrada.

    Realiza a validação dos argumentos da interface gráfica, resolve o diretório
    de saída do projeto, lida com atualizações de progresso e garante o encerramento
    seguro com eliminação de ficheiros parciais caso o utilizador cancele a operação.

    Args:
        selected_paths: Dicionário contendo os caminhos selecionados na UI (ex: 'video', 'output_dir').
        project_name: Nome do projeto/subpasta onde os fotogramas serão guardados.
        fps_str: Valor de FPS em formato string a ser convertido e validado.
        show_toast_callback: Callback para exibição de notificações toast na UI (mensagem, is_error).
        update_progress_callback: Callback para atualizar a barra de progresso no diálogo (0.0 a 1.0).
        set_ui_state_callback: Callback para definir o estado da UI (is_running, status_message).
        cancel_event: Evento do threading responsável por sinalizar a interrupção manual.
    """
    # 1. Validação da taxa de amostragem (FPS)
    try:
        fps = int(fps_str)
        if fps <= 0:
            raise ValueError
    except ValueError:
        show_toast_callback("O FPS deve ser um número inteiro positivo!", is_error=True)
        return

    # 2. Validação da existência do ficheiro de vídeo
    video_path: Optional[Path] = selected_paths.get("video")
    if not video_path or not video_path.exists():
        show_toast_callback("Selecione um arquivo de vídeo válido!", is_error=True)
        return

    # 3. Validação do nome do projeto
    proj_name_clean = project_name.strip()
    if not proj_name_clean:
        show_toast_callback("Preencha o nome do projeto!", is_error=True)
        return

    # 4. Resolução do diretório de saída (com fallback para ~/IC_Output)
    base_out: Optional[Path] = selected_paths.get("output_dir")
    if not base_out:
        base_out = Path(get_user_home_dir()) / "IC_Output"

    out_dir = base_out / proj_name_clean
    set_ui_state_callback(True, "Extraindo frames...")

    # Função interna para monitorizar o progresso e interrupção manual
    def checked_progress(val: float):
        if cancel_event and cancel_event.is_set():
            raise InterruptedException()
        update_progress_callback(val)

    # 5. Execução do pipeline de extração de fotogramas
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
        # Apaga o diretório incompleto para evitar ficheiros corrompidos no disco
        if out_dir.exists():
            shutil.rmtree(out_dir, ignore_errors=True)
        show_toast_callback("⚠️ Processamento cancelado. Arquivos parciais removidos.", is_error=True)
    except Exception as e:
        show_toast_callback(f"Erro inesperado: {e}", is_error=True)
    finally:
        # Garante que o estado da UI é restaurado independentemente do resultado
        set_ui_state_callback(False, "")