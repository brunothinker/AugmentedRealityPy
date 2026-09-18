import sys
from typing import Callable, Optional
import flet as ft

from ui.theme import (
    COLOR_CARD_BG,
    COLOR_ERROR,
    COLOR_PRIMARY,
    COLOR_SUBTEXT,
    COLOR_SUCCESS,
    COLOR_TEXT,
)


class TextRedirector:
    """Redireciona prints do sys.stdout/stderr para o componente de texto do Flet em tempo real."""

    def __init__(self, append_func: Callable[[str], None]):
        self.append_func = append_func
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr

    def write(self, message: str):
        if message:
            self.append_func(message)
            self.original_stdout.write(message)

    def flush(self):
        self.original_stdout.flush()

    def start(self):
        sys.stdout = self
        sys.stderr = self

    def stop(self):
        sys.stdout = self.original_stdout
        sys.stderr = self.original_stderr


class ExecutionDialog:
    """Caixa de Diálogo Flutuante para Acompanhamento de Processos, Logs e Conclusão."""

    def __init__(
            self,
            page: ft.Page,
            title: str = "Processando...",
            on_cancel: Optional[Callable[[], None]] = None,
    ):
        self.page = page
        self.on_cancel = on_cancel
        self.is_finished = False

        self.icon_header = ft.Icon(ft.icons.SETTINGS_SUGGEST, color=COLOR_PRIMARY)
        self.lbl_title = ft.Text(title, size=18, weight="bold", color=COLOR_TEXT)
        self.status_text = ft.Text("Iniciando processo...", italic=True, size=13, color=COLOR_SUBTEXT)
        self.progress_bar = ft.ProgressBar(value=0.0, color=COLOR_PRIMARY, height=8)

        # Container de Logs
        self.log_text = ft.Text("", size=11, selectable=True, color=COLOR_SUBTEXT, font_family="monospace")
        self.log_container = ft.Container(
            content=ft.Column([self.log_text], scroll=ft.ScrollMode.ALWAYS, auto_scroll=True),
            bgcolor=COLOR_CARD_BG,
            padding=10,
            border_radius=6,
            height=160,
            visible=True,
        )

        self.btn_toggle_log = ft.TextButton(
            "Ocultar Logs",
            icon=ft.icons.TERMINAL,
            on_click=self._toggle_logs,
        )

        # Botão dinâmico de Ação (Muda de 'Cancelar' para 'Concluir' no final)
        self.btn_action = ft.OutlinedButton(
            "Cancelar",
            icon=ft.icons.CANCEL,
            icon_color=COLOR_ERROR,
            on_click=self._handle_action,
        )

        # Instância do Redirecionador de Prints
        self.redirector = TextRedirector(self._append_log)

        # Diálogo Modal Principal
        self.dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row([self.icon_header, self.lbl_title]),
            content=ft.Container(
                content=ft.Column(
                    [
                        self.status_text,
                        ft.Container(height=5),
                        self.progress_bar,
                        ft.Container(height=10),
                        self.btn_toggle_log,
                        self.log_container,
                    ],
                    tight=True,
                    spacing=5,
                ),
                width=520,
            ),
            actions=[self.btn_action],
            actions_alignment=ft.MainAxisAlignment.END,
        )

    def _append_log(self, text: str):
        self.log_text.value += text
        self.page.update()

    def _toggle_logs(self, e):
        self.log_container.visible = not self.log_container.visible
        self.btn_toggle_log.text = "Exibir Logs" if not self.log_container.visible else "Ocultar Logs"
        self.page.update()

    def _handle_action(self, e):
        if self.is_finished:
            self.close()
        else:
            self._confirm_cancel()

    def _confirm_cancel(self):
        """Abre caixa de diálogo secundária pedindo confirmação de cancelamento."""
        confirm_dialog = ft.AlertDialog(
            title=ft.Text("Confirmar Cancelamento"),
            content=ft.Text("Tem certeza de que deseja interromper o processamento atual?"),
            actions=[
                ft.TextButton("Não", on_click=lambda _: self._close_confirm(confirm_dialog)),
                ft.ElevatedButton(
                    "Sim, Cancelar",
                    bgcolor=COLOR_ERROR,
                    color=COLOR_TEXT,
                    on_click=lambda _: self._execute_cancel(confirm_dialog),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.dialog = confirm_dialog
        confirm_dialog.open = True
        self.page.update()

    def _close_confirm(self, confirm_dialog: ft.AlertDialog):
        confirm_dialog.open = False
        self.page.dialog = self.dialog
        self.page.update()

    def _execute_cancel(self, confirm_dialog: ft.AlertDialog):
        confirm_dialog.open = False
        if self.on_cancel:
            self.on_cancel()
        self.close()

    def show(self):
        self.redirector.start()
        self.page.dialog = self.dialog
        self.dialog.open = True
        self.page.update()

    def close(self):
        self.redirector.stop()
        self.dialog.open = False
        self.page.update()

    def update_progress(self, val: float, msg: str = ""):
        self.progress_bar.value = val
        if msg:
            self.status_text.value = msg
        self.page.update()

    def set_finished(self, success: bool = True, message: str = "Processamento Concluído!"):
        """Sinaliza o fim da tarefa, altera o título e disponibiliza o botão para fechar."""
        self.is_finished = True
        self.progress_bar.value = 1.0
        self.status_text.value = message

        if success:
            self.icon_header.name = ft.icons.CHECK_CIRCLE
            self.icon_header.color = COLOR_SUCCESS
            self.progress_bar.color = COLOR_SUCCESS
        else:
            self.icon_header.name = ft.icons.ERROR
            self.icon_header.color = COLOR_ERROR
            self.progress_bar.color = COLOR_ERROR

        self.btn_action.text = "Concluir"
        self.btn_action.icon = ft.icons.CHECK
        self.btn_action.icon_color = COLOR_SUCCESS
        self.page.update()