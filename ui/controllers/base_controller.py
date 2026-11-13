import shutil
import threading
from collections.abc import Callable
from pathlib import Path

from ui.ui_utils import get_user_home_dir


class InterruptedException(Exception):
    """Exceção customizada para interromper pipelines de execução via cancel_event."""


class BaseController:
    """Controller base fornecendo validação, resolução de caminhos, progresso e limpeza segura."""

    def __init__(self, default_subfolder: str = "") -> None:
        self.default_subfolder = default_subfolder

    def resolve_output_dir(
        self,
        selected_out: Path | None,
        folder_name: str,
        subfolder: str | None = None,
    ) -> Path:
        """Resolve o diretório de saída do projeto com fallback para ~/IC_Output."""
        if selected_out:
            base_out = selected_out
        else:
            target_sub = self.default_subfolder if subfolder is None else subfolder
            base_out = Path(get_user_home_dir()) / "IC_Output"
            if target_sub:
                base_out = base_out / target_sub
        return base_out / folder_name

    @staticmethod
    def validate_project_name(
        project_name: str,
        show_toast: Callable[[str, bool], None],
    ) -> str | None:
        """Valida e limpa o nome do projeto, exibindo toast de erro se vazio."""
        clean_name = project_name.strip()
        if not clean_name:
            show_toast("Preencha o nome do projeto!", True)
            return None
        return clean_name

    @staticmethod
    def validate_path_exists(
        path: Path | None,
        error_msg: str,
        show_toast: Callable[[str, bool], None],
    ) -> Path | None:
        """Valida se o caminho foi selecionado e existe no disco."""
        if not path or not path.exists():
            show_toast(error_msg, True)
            return None
        return path

    @staticmethod
    def make_checked_progress(
        update_progress: Callable[[float], None],
        cancel_event: threading.Event | None,
        scale: float = 1.0,
        offset: float = 0.0,
    ) -> Callable[[float], None]:
        """Cria callback de progresso (0.0 a 1.0) com verificação de cancelamento."""
        def _progress(val: float) -> None:
            if cancel_event and cancel_event.is_set():
                raise InterruptedException()
            update_progress(offset + val * scale)

        return _progress

    @staticmethod
    def make_checked_status_progress(
        update_progress: Callable[[float, str], None],
        cancel_event: threading.Event | None,
    ) -> Callable[[float | None, str], None]:
        """Cria callback de progresso com mensagem de status e checagem de cancelamento."""
        def _progress(val: float | None, msg: str = "") -> None:
            if cancel_event and cancel_event.is_set():
                raise InterruptedException()
            update_progress(val if val is not None else 0.0, msg)

        return _progress

    def _execute_task(
        self,
        task_fn: Callable[[], bool],
        out_dir: Path,
        running_msg: str,
        success_msg: str,
        fail_msg: str,
        cancel_msg: str,
        show_toast: Callable[[str, bool], None],
        set_ui_state: Callable[[bool, str], None],
        cleanup_on_cancel: bool = True,
    ) -> None:
        """Executa a tarefa encapsulando ciclo de vida da UI, erros e limpeza parcial."""
        set_ui_state(True, running_msg)
        try:
            success = task_fn()
            show_toast(
                success_msg if success else fail_msg,
                not success,
            )
        except InterruptedException:
            if cleanup_on_cancel and out_dir.exists():
                shutil.rmtree(out_dir, ignore_errors=True)
            show_toast(cancel_msg, True)
        except Exception as e:
            show_toast(f"Erro inesperado: {e}", True)
        finally:
            set_ui_state(False, "")