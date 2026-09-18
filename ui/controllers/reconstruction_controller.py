from pathlib import Path
import shutil
import threading
from typing import Callable, Dict, Optional

from src.reconstruction.mono_reconstruction import run_mono_reconstruction
from src.reconstruction.stereo_reconstruction import run_stereo_reconstruction
from ui.ui_utils import get_user_home_dir


class InterruptedException(Exception):
    """Exceção customizada para interromper as etapas da reconstrução 3D via cancel_event."""
    pass


def handle_mono_reconstruction(
    selected_paths: Dict[str, Path],
    project_name: str,
    show_toast_callback: Callable[[str, bool], None],
    update_progress_callback: Callable[[float, str], None],
    set_ui_state_callback: Callable[[bool, str], None],
    cancel_event: Optional[threading.Event] = None,
) -> None:
    """Orquestra o pipeline de reconstrução monocular 3D (Structure from Motion / SfM via COLMAP).

    Valida os seletores da interface, resolve a pasta de projeto e destino, acompanha
    o progresso da extração de características/esparsa/densa e garante a remoção de
    diretórios corrompidos ou incompletos em caso de interrupção manual.

    Args:
        selected_paths: Dicionário contendo os caminhos na UI ('mono_rec_images', 'mono_rec_out').
        project_name: Nome do projeto/subpasta para salvar os resultados da reconstrução.
        show_toast_callback: Callback para exibição de notificações toast na UI (mensagem, is_error).
        update_progress_callback: Callback para atualizar a barra e mensagem de progresso no diálogo.
        set_ui_state_callback: Callback para definir o estado da UI (is_running, status_message).
        cancel_event: Evento do threading responsável por sinalizar a interrupção manual.
    """
    # 1. Validação do nome do projeto
    proj_name_clean = project_name.strip()
    if not proj_name_clean:
        show_toast_callback("Preencha o nome do projeto!", is_error=True)
        return

    # 2. Validação da pasta de imagens de entrada
    images_dir: Optional[Path] = selected_paths.get("mono_rec_images")
    if not images_dir or not images_dir.exists():
        show_toast_callback("Selecione a pasta com as imagens de entrada!", is_error=True)
        return

    # 3. Resolução do diretório de saída (com fallback para ~/IC_Output/reconstrucoes)
    base_out: Optional[Path] = selected_paths.get("mono_rec_out")
    if not base_out:
        base_out = Path(get_user_home_dir()) / "IC_Output" / "reconstrucoes"

    out_dir = base_out / proj_name_clean
    set_ui_state_callback(True, "Iniciando reconstrução monocular (COLMAP)...")

    # Função interna para verificação contínua do sinal de cancelamento
    def checked_progress(val: float, msg: str = ""):
        if cancel_event and cancel_event.is_set():
            raise InterruptedException()
        update_progress_callback(val, msg)

    # 4. Execução do pipeline de reconstrução monocular
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
        # Garante a limpeza do diretório em caso de interrupção pelo usuário
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
    """Orquestra o pipeline de reconstrução estéreo 3D baseado em par de câmeras e distância física.

    Valida as pastas dos canais esquerdo/direito, calcula e valida o valor de baseline
    (metros), executa o alinhamento e geração do mapa de disparidade/nuvem de pontos, e
    remove arquivos parciais caso ocorra cancelamento.

    Args:
        selected_paths: Dicionário contendo os caminhos na UI ('stereo_rec_left', 'stereo_rec_right', 'stereo_rec_out').
        project_name: Nome do projeto/subpasta onde os artefatos 3D serão armazenados.
        baseline_str: Valor da distância física entre os centros ópticos das câmeras (metros) em string.
        show_toast_callback: Callback para exibição de notificações toast na UI (mensagem, is_error).
        update_progress_callback: Callback para atualizar a barra e mensagem de progresso no diálogo.
        set_ui_state_callback: Callback para definir o estado da UI (is_running, status_message).
        cancel_event: Evento do threading responsável por sinalizar a interrupção manual.
    """
    # 1. Validação do nome do projeto
    proj_name_clean = project_name.strip()
    if not proj_name_clean:
        show_toast_callback("Preencha o nome do projeto!", is_error=True)
        return

    # 2. Validação das pastas de imagens das câmeras esquerda e direita
    cam_left_dir: Optional[Path] = selected_paths.get("stereo_rec_left")
    cam_right_dir: Optional[Path] = selected_paths.get("stereo_rec_right")

    if not cam_left_dir or not cam_left_dir.exists() or not cam_right_dir or not cam_right_dir.exists():
        show_toast_callback("Selecione ambas as pastas de câmeras (Esquerda e Direita)!", is_error=True)
        return

    # Assume a pasta pai como diretório base das amostras estéreo
    images_dir: Path = cam_left_dir.parent

    # 3. Validação numérica da baseline
    try:
        baseline = float(baseline_str.replace(",", "."))
        if baseline <= 0:
            raise ValueError
    except ValueError:
        show_toast_callback("Informe um valor positivo para a baseline (metros)!", is_error=True)
        return

    # 4. Resolução do diretório de saída (com fallback para ~/IC_Output/reconstrucoes)
    base_out: Optional[Path] = selected_paths.get("stereo_rec_out")
    if not base_out:
        base_out = Path(get_user_home_dir()) / "IC_Output" / "reconstrucoes"

    out_dir = base_out / proj_name_clean
    set_ui_state_callback(True, "Iniciando pipeline de reconstrução estéreo...")

    # Função interna para verificação do evento de interrupção
    def checked_progress(val: float, msg: str = ""):
        if cancel_event and cancel_event.is_set():
            raise InterruptedException()
        update_progress_callback(val, msg)

    # 5. Execução do pipeline de reconstrução estéreo
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
        # Limpa resíduos gerados antes do cancelamento
        if out_dir.exists():
            shutil.rmtree(out_dir, ignore_errors=True)
        show_toast_callback("⚠️ Reconstrução Estéreo cancelada. Diretório de saída limpo.", is_error=True)
    except Exception as e:
        show_toast_callback(f"Erro inesperado: {e}", is_error=True)
    finally:
        set_ui_state_callback(False, "")