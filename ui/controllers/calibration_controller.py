from pathlib import Path
import shutil
import threading
from typing import Callable, Dict, Optional

from src.camera_calibration.mono_calibration import run_mono_calibration
from src.camera_calibration.stereo_calibration import run_stereo_calibration
from ui.ui_utils import get_user_home_dir


class InterruptedException(Exception):
    """Exceção customizada para interromper o pipeline de calibração via cancel_event."""
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
    """Orquestra o processo de calibração monocular de câmera.

    Valida os parâmetros do padrão de calibração (tabuleiro de xadrez), gerencia os
    diretórios de entrada e saída, atualiza o progresso da UI e garante a remoção de
    arquivos parciais em caso de cancelamento.

    Args:
        selected_paths: Dicionário contendo os caminhos selecionados na UI (ex: 'mono_in', 'mono_out').
        project_name_str: Nome do projeto/subpasta para salvar os parâmetros intrínsecos.
        rows_str: Número de cantos internos nas linhas do tabuleiro em formato string.
        cols_str: Número de cantos internos nas colunas do tabuleiro em formato string.
        square_size_str: Tamanho do quadrado do tabuleiro (em mm ou m) em formato string.
        show_toast_callback: Callback para exibição de notificações toast na UI (mensagem, is_error).
        update_progress_callback: Callback para atualizar a barra de progresso no diálogo.
        set_ui_state_callback: Callback para definir o estado da UI (is_running, status_message).
        cancel_event: Evento do threading responsável por sinalizar a interrupção manual.
    """
    # 1. Validação do nome do projeto
    proj_name_clean = project_name_str.strip()
    if not proj_name_clean:
        show_toast_callback("Preencha o nome do projeto!", is_error=True)
        return

    # 2. Validação da pasta de imagens de entrada
    in_dir: Optional[Path] = selected_paths.get("mono_in")
    if not in_dir or not in_dir.exists():
        show_toast_callback("Selecione uma pasta com os quadros de calibração!", is_error=True)
        return

    # 3. Validação das dimensões e geometria do tabuleiro
    try:
        rows = int(rows_str)
        cols = int(cols_str)
        square_size = float(square_size_str.replace(",", "."))

        if rows <= 0 or cols <= 0 or square_size <= 0:
            raise ValueError
    except ValueError:
        show_toast_callback("Número de cantos e tamanho do quadrado devem ser maiores que zero!", is_error=True)
        return

    # 4. Resolução do diretório de saída (com fallback para ~/IC_Output/calibracoes)
    base_out: Optional[Path] = selected_paths.get("mono_out")
    if not base_out:
        base_out = Path(get_user_home_dir()) / "IC_Output" / "calibracoes"

    out_dir = base_out / proj_name_clean
    set_ui_state_callback(True, "Processando calibração monocular...")

    # Função interna para verificação periódica de cancelamento
    def checked_progress(val: float):
        if cancel_event and cancel_event.is_set():
            raise InterruptedException()
        update_progress_callback(val)

    # 5. Execução do pipeline de calibração monocular
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
        # Apaga o diretório incompleto em caso de interrupção manual
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
    """Orquestra o processo de calibração estéreo entre duas câmeras.

    Valida os seletores dos canais Esquerdo/Direito e o tabuleiro de xadrez,
    divide a amostragem de progresso entre as duas etapas e trata o encerramento
    limpo em caso de cancelamento.

    Args:
        selected_paths: Dicionário contendo os caminhos na UI ('stereo_left_in', 'stereo_right_in', 'stereo_out').
        project_name_str: Nome do projeto/subpasta para salvar os parâmetros extrínsecos e matrizes R, T.
        rows_str: Número de cantos internos nas linhas do tabuleiro em formato string.
        cols_str: Número de cantos internos nas colunas do tabuleiro em formato string.
        square_size_str: Tamanho do quadrado do tabuleiro em formato string.
        show_toast_callback: Callback para exibição de notificações toast na UI (mensagem, is_error).
        update_progress_callback: Callback para atualizar a barra de progresso no diálogo.
        set_ui_state_callback: Callback para definir o estado da UI (is_running, status_message).
        cancel_event: Evento do threading responsável por sinalizar a interrupção manual.
    """
    # 1. Validação do nome do projeto
    proj_name_clean = project_name_str.strip()
    if not proj_name_clean:
        show_toast_callback("Preencha o nome do projeto!", is_error=True)
        return

    # 2. Validação das pastas de entrada para ambas as câmeras
    left_dir: Optional[Path] = selected_paths.get("stereo_left_in")
    right_dir: Optional[Path] = selected_paths.get("stereo_right_in")

    if not left_dir or not left_dir.exists():
        show_toast_callback("Selecione a pasta de imagens da Câmera Esquerda!", is_error=True)
        return

    if not right_dir or not right_dir.exists():
        show_toast_callback("Selecione a pasta de imagens da Câmera Direita!", is_error=True)
        return

    # 3. Validação dos parâmetros geométricos do tabuleiro
    try:
        rows = int(rows_str)
        cols = int(cols_str)
        square_size = float(square_size_str.replace(",", "."))

        if rows <= 0 or cols <= 0 or square_size <= 0:
            raise ValueError
    except ValueError:
        show_toast_callback("Número de cantos e tamanho do quadrado devem ser maiores que zero!", is_error=True)
        return

    # 4. Resolução do diretório de saída (com fallback para ~/IC_Output/calibracoes)
    base_out: Optional[Path] = selected_paths.get("stereo_out")
    if not base_out:
        base_out = Path(get_user_home_dir()) / "IC_Output" / "calibracoes"

    out_dir = base_out / proj_name_clean
    set_ui_state_callback(True, "Processando calibração estéreo...")

    # Mapeamento do progresso dividindo 50% para câmera A e 50% para câmera B
    def checked_progress_a(v: float):
        if cancel_event and cancel_event.is_set():
            raise InterruptedException()
        update_progress_callback(v * 0.5)

    def checked_progress_b(v: float):
        if cancel_event and cancel_event.is_set():
            raise InterruptedException()
        update_progress_callback(0.5 + v * 0.5)

    # 5. Execução do pipeline de calibração estéreo
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
        # Remove a pasta criada se o usuário cancelar antes do término
        if out_dir.exists():
            shutil.rmtree(out_dir, ignore_errors=True)
        show_toast_callback("⚠️ Calibração Estéreo cancelada. Arquivos parciais removidos.", is_error=True)
    except Exception as e:
        show_toast_callback(f"Erro inesperado: {e}", is_error=True)
    finally:
        set_ui_state_callback(False, "")