from pathlib import Path
import shutil
import threading
from typing import Callable, Dict, Optional

from src.post_processing.clahe import run_clahe_images
from src.post_processing.resize import run_resize_images
from ui.ui_utils import get_user_home_dir


class InterruptedException(Exception):
    """Exceção customizada para interromper as etapas de pós-processamento via cancel_event."""
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
    """Orquestra a aplicação do algoritmo CLAHE (Contrast Limited Adaptive Histogram Equalization).

    Valida o diretório de entrada e os hiperparâmetros de contraste (Clip Limit e Tile Size),
    resolve o diretório de destino, notifica o progresso para a UI e assegura a remoção
    de saídas parciais em caso de cancelamento pelo utilizador.

    Args:
        selected_paths: Dicionário com os caminhos selecionados na UI ('clahe_in', 'clahe_out').
        clip_limit_str: Limite de corte do histograma adaptativo em formato string.
        tile_size_str: Dimensão da grade de blocos locais (ex: 8 para 8x8) em formato string.
        show_toast_callback: Callback para exibição de notificações toast na UI (mensagem, is_error).
        update_progress_callback: Callback para atualizar a barra de progresso no diálogo.
        set_ui_state_callback: Callback para definir o estado da UI (is_running, status_message).
        cancel_event: Evento do threading responsável por sinalizar a interrupção manual.
    """
    # 1. Validação do diretório de imagens de entrada
    in_dir: Optional[Path] = selected_paths.get("clahe_in")
    if not in_dir or not in_dir.exists():
        show_toast_callback("Selecione uma pasta de entrada válida!", is_error=True)
        return

    # 2. Validação e conversão numérica dos parâmetros do CLAHE
    try:
        clip_limit = float(clip_limit_str.replace(",", "."))
        tile_val = int(tile_size_str)
        tile_size = (tile_val, tile_val)

        if clip_limit <= 0 or tile_val <= 0:
            raise ValueError
    except ValueError:
        show_toast_callback("Valores de Clip Limit e Tile Size devem ser positivos!", is_error=True)
        return

    # 3. Resolução do diretório de saída (com fallback para ~/IC_Output/<nome_in>_clahe)
    out_dir: Optional[Path] = selected_paths.get("clahe_out")
    if not out_dir:
        out_dir = Path(get_user_home_dir()) / "IC_Output" / f"{in_dir.name}_clahe"

    set_ui_state_callback(True, "Aplicando realce CLAHE...")

    # Função interna para verificação de interrupção manual
    def checked_progress(val: float):
        if cancel_event and cancel_event.is_set():
            raise InterruptedException()
        update_progress_callback(val)

    # 4. Execução do pipeline de realce de contraste
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
        # Apaga o diretório incompleto para evitar acúmulo de imagens parcialmente processadas
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
    """Orquestra o redimensionamento em lote das imagens do diretório selecionado.

    Valida a resolução alvo (largura e altura em pixels), trata o caminho de saída,
    envia o progresso para a UI em tempo real e limpa os arquivos parciais caso o
    processo seja interrompido.

    Args:
        selected_paths: Dicionário com os caminhos na UI ('resize_in', 'resize_out').
        width_str: Largura alvo em pixels em formato string.
        height_str: Altura alvo em pixels em formato string.
        show_toast_callback: Callback para exibição de notificações toast na UI (mensagem, is_error).
        update_progress_callback: Callback para atualizar a barra de progresso no diálogo.
        set_ui_state_callback: Callback para definir o estado da UI (is_running, status_message).
        cancel_event: Evento do threading responsável por sinalizar a interrupção manual.
    """
    # 1. Validação do diretório de entrada
    in_dir: Optional[Path] = selected_paths.get("resize_in")
    if not in_dir or not in_dir.exists():
        show_toast_callback("Selecione uma pasta de entrada válida!", is_error=True)
        return

    # 2. Validação da dimensão em pixels
    try:
        target_w = int(width_str)
        target_h = int(height_str)
        if target_w <= 0 or target_h <= 0:
            raise ValueError
    except ValueError:
        show_toast_callback("Valores de largura e altura devem ser inteiros positivos!", is_error=True)
        return

    # 3. Resolução do diretório de saída (com fallback para ~/IC_Output/<nome_in>_resized)
    out_dir: Optional[Path] = selected_paths.get("resize_out")
    if not out_dir:
        out_dir = Path(get_user_home_dir()) / "IC_Output" / f"{in_dir.name}_resized"

    set_ui_state_callback(True, "Redimensionando imagens...")

    # Função interna para monitoramento de cancelamento
    def checked_progress(val: float):
        if cancel_event and cancel_event.is_set():
            raise InterruptedException()
        update_progress_callback(val)

    # 4. Execução da rotina de redimensionamento
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
        # Limpa os arquivos parciais gerados antes da interrupção
        if out_dir.exists():
            shutil.rmtree(out_dir, ignore_errors=True)
        show_toast_callback("⚠️ Redimensionamento cancelado. Diretório limpo.", is_error=True)
    except Exception as e:
        show_toast_callback(f"Erro inesperado: {e}", is_error=True)
    finally:
        set_ui_state_callback(False, "")