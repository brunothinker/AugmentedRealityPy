from pathlib import Path
import threading
from typing import Dict
import flet as ft

from ui.components.execution_dialog import ExecutionDialog
from ui.components.io_picker_card import IOPickerCard
from ui.controllers.post_processing_controller import handle_clahe, handle_resize
from ui.theme import (
    BUTTON_HEIGHT,
    COLOR_ICON,
    COLOR_PRIMARY,
    COLOR_TEXT,
    FORM_WIDTH,
)


def create_clahe_page(page: ft.Page, selected_paths: Dict[str, Path]) -> ft.Container:
    """Gera a interface gráfica para a página de realce de contraste adaptativo (CLAHE).

    Instancia os seletores de pasta de entrada e destino utilizando o `IOPickerCard` no
    layout de lista (`build_list_tile`), configura os campos de texto para os parâmetros
    de histograma (Clip Limit e Tile Size) e gerencia o envio assíncrono para a controller.

    Args:
        page: Instância do Flet Page ativa na aplicação.
        selected_paths: Dicionário compartilhado de caminhos selecionados pelo usuário.

    Returns:
        ft.Container: Container Flet estruturado contendo a view do CLAHE.
    """
    # 1. Definição dos campos de texto para parâmetros do CLAHE
    tf_norm_clip = ft.TextField(label="Clip Limit", value="2.0", expand=True)
    tf_norm_tile = ft.TextField(label="Tile Size", value="8", expand=True)

    # 2. Cards de seleção I/O no formato lista
    card_clahe_in = IOPickerCard(
        page=page,
        title="Pasta de Entrada",
        icon=ft.icons.FOLDER_OPEN,
        path_key="clahe_in",
        selected_paths=selected_paths,
    )

    card_clahe_out = IOPickerCard(
        page=page,
        title="Pasta de Destino",
        icon=ft.icons.CREATE_NEW_FOLDER,
        path_key="clahe_out",
        selected_paths=selected_paths,
    )

    # 3. Handler de execução para aplicação do filtro
    def on_run_click(e: ft.ControlEvent):
        cancel_event = threading.Event()

        dialog = ExecutionDialog(
            page=page,
            title="Realce de Contraste (CLAHE)",
            on_cancel=lambda: cancel_event.set(),
        )
        dialog.show()

        def set_ui_state(is_running: bool, status_msg: str):
            if not is_running:
                dialog.set_finished(success=True, message="Processamento finalizado com sucesso!")

        def run_task():
            handle_clahe(
                selected_paths=selected_paths,
                clip_limit_str=tf_norm_clip.value,
                tile_size_str=tf_norm_tile.value,
                show_toast_callback=lambda msg, is_error=False: page.show_snack_bar(
                    ft.SnackBar(ft.Text(msg), bgcolor=ft.colors.RED_700 if is_error else ft.colors.GREEN_700)
                ),
                update_progress_callback=dialog.update_progress,
                set_ui_state_callback=set_ui_state,
                cancel_event=cancel_event,
            )

        threading.Thread(target=run_task, daemon=True).start()

    btn_run = ft.ElevatedButton(
        "Aplicar CLAHE",
        icon=ft.icons.PLAY_ARROW,
        bgcolor=COLOR_PRIMARY,
        color=COLOR_TEXT,
        height=BUTTON_HEIGHT,
        on_click=on_run_click,
    )

    # 4. Estruturação visual do formulário CLAHE
    form_clahe = ft.Column(
        [
            card_clahe_in.build_list_tile(),
            card_clahe_out.build_list_tile(),
            ft.Divider(),
            ft.Row([tf_norm_clip, tf_norm_tile]),
            ft.Container(height=10),
            btn_run,
        ],
        width=FORM_WIDTH,
        spacing=10,
        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
    )

    return ft.Container(
        alignment=ft.alignment.center,
        padding=25,
        content=ft.Column(
            [
                ft.Icon(ft.icons.IMAGE_SEARCH, size=45, color=COLOR_ICON),
                ft.Text("Realce Contraste (CLAHE)", size=24, weight="bold", color=COLOR_TEXT),
                ft.Container(height=10),
                form_clahe,
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )


def create_resize_page(page: ft.Page, selected_paths: Dict[str, Path]) -> ft.Container:
    """Gera a interface gráfica para a página de redimensionamento de imagens em lote.

    Configura os seletores de entrada e saída, os campos para inserção da resolução alvo
    (largura e altura em pixels) e gerencia o disparo do processamento com modal de progresso.

    Args:
        page: Instância do Flet Page ativa na aplicação.
        selected_paths: Dicionário compartilhado de caminhos selecionados pelo usuário.

    Returns:
        ft.Container: Container Flet estruturado contendo a view de redimensionamento.
    """
    # 1. Definição dos campos para resolução em pixels
    tf_resize_w = ft.TextField(label="Largura Alvo (px)", value="4000", expand=True)
    tf_resize_h = ft.TextField(label="Altura Alvo (px)", value="3000", expand=True)

    # 2. Cards de seleção I/O no formato lista
    card_resize_in = IOPickerCard(
        page=page,
        title="Pasta de Entrada",
        icon=ft.icons.FOLDER_OPEN,
        path_key="resize_in",
        selected_paths=selected_paths,
    )

    card_resize_out = IOPickerCard(
        page=page,
        title="Pasta de Destino",
        icon=ft.icons.CREATE_NEW_FOLDER,
        path_key="resize_out",
        selected_paths=selected_paths,
    )

    # 3. Handler de execução do redimensionamento
    def on_run_click(e: ft.ControlEvent):
        cancel_event = threading.Event()

        dialog = ExecutionDialog(
            page=page,
            title="Redimensionamento de Imagens",
            on_cancel=lambda: cancel_event.set(),
        )
        dialog.show()

        def set_ui_state(is_running: bool, status_msg: str):
            if not is_running:
                dialog.set_finished(success=True, message="Processamento finalizado com sucesso!")

        def run_task():
            handle_resize(
                selected_paths=selected_paths,
                width_str=tf_resize_w.value,
                height_str=tf_resize_h.value,
                show_toast_callback=lambda msg, is_error=False: page.show_snack_bar(
                    ft.SnackBar(ft.Text(msg), bgcolor=ft.colors.RED_700 if is_error else ft.colors.GREEN_700)
                ),
                update_progress_callback=dialog.update_progress,
                set_ui_state_callback=set_ui_state,
                cancel_event=cancel_event,
            )

        threading.Thread(target=run_task, daemon=True).start()

    btn_run = ft.ElevatedButton(
        "Redimensionar Imagens",
        icon=ft.icons.PLAY_ARROW,
        bgcolor=COLOR_PRIMARY,
        color=COLOR_TEXT,
        height=BUTTON_HEIGHT,
        on_click=on_run_click,
    )

    # 4. Estruturação visual do formulário de redimensionamento
    form_resize = ft.Column(
        [
            card_resize_in.build_list_tile(),
            card_resize_out.build_list_tile(),
            ft.Divider(),
            ft.Row([tf_resize_w, tf_resize_h]),
            ft.Container(height=10),
            btn_run,
        ],
        width=FORM_WIDTH,
        spacing=10,
        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
    )

    return ft.Container(
        alignment=ft.alignment.center,
        padding=25,
        content=ft.Column(
            [
                ft.Icon(ft.icons.ASPECT_RATIO, size=45, color=COLOR_ICON),
                ft.Text("Redimensionamento de Imagens", size=24, weight="bold", color=COLOR_TEXT),
                ft.Container(height=10),
                form_resize,
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )