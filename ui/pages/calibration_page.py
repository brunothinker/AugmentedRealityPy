from pathlib import Path
import threading
from typing import Dict
import flet as ft

from ui.components.execution_dialog import ExecutionDialog
from ui.components.io_picker_card import IOPickerCard
from ui.controllers.calibration_controller import handle_mono_calibration, handle_stereo_calibration
from ui.theme import (
    BUTTON_HEIGHT,
    COLOR_ICON,
    COLOR_PRIMARY,
    COLOR_TEXT,
    FORM_WIDTH,
)


def create_mono_calibration_page(page: ft.Page, selected_paths: Dict[str, Path]) -> ft.Container:
    """Gera a interface gráfica para a página de calibração de câmera monocular.

    Configura os campos de entrada de texto (nome do projeto e dimensões do tabuleiro de xadrez),
    instancia os seletores de entrada e saída no formato lista estendida (`build_list_tile`),
    e gerencia a execução assíncrona da calibração através do `ExecutionDialog`.

    Args:
        page: Instância do Flet Page ativa na aplicação.
        selected_paths: Dicionário compartilhado de caminhos selecionados pelo usuário.

    Returns:
        ft.Container: Container Flet contendo a estrutura do formulário monocular.
    """
    # 1. Definição dos campos de texto e hiperparâmetros do tabuleiro de xadrez
    tf_project_name = ft.TextField(
        label="Nome do Projeto (Subpasta)",
        hint_text="Ex: meu_projeto_mono",
        value="meu_projeto_mono",
        expand=True,
    )
    tf_grid_rows = ft.TextField(label="Linhas de Cantos Internos", value="6", expand=True)
    tf_grid_cols = ft.TextField(label="Colunas de Cantos Internos", value="9", expand=True)
    tf_square_size = ft.TextField(label="Tamanho do Quadrado (m)", value="0.025", expand=True)

    # 2. Instanciação dos cards de seleção I/O em formato de lista
    card_mono_in = IOPickerCard(
        page=page,
        title="Pasta de Imagens",
        icon=ft.icons.FOLDER_OPEN,
        path_key="mono_in",
        selected_paths=selected_paths,
    )

    card_mono_out = IOPickerCard(
        page=page,
        title="Pasta de Destino",
        icon=ft.icons.CREATE_NEW_FOLDER,
        path_key="mono_out",
        selected_paths=selected_paths,
    )

    # 3. Handler de execução para a rotina monocular
    def on_run_click(e: ft.ControlEvent):
        cancel_event = threading.Event()

        dialog = ExecutionDialog(
            page=page,
            title="Calibração Monocular",
            on_cancel=lambda: cancel_event.set(),
        )
        dialog.show()

        def set_ui_state(is_running: bool, status_msg: str):
            if not is_running:
                dialog.set_finished(success=True, message="Processamento finalizado com sucesso!")

        def run_task():
            handle_mono_calibration(
                selected_paths=selected_paths,
                project_name_str=tf_project_name.value,
                rows_str=tf_grid_rows.value,
                cols_str=tf_grid_cols.value,
                square_size_str=tf_square_size.value,
                show_toast_callback=lambda msg, is_error=False: page.show_snack_bar(
                    ft.SnackBar(ft.Text(msg), bgcolor=ft.colors.RED_700 if is_error else ft.colors.GREEN_700)
                ),
                update_progress_callback=dialog.update_progress,
                set_ui_state_callback=set_ui_state,
                cancel_event=cancel_event,
            )

        threading.Thread(target=run_task, daemon=True).start()

    btn_run = ft.ElevatedButton(
        "Executar Calibração Monocular",
        icon=ft.icons.PLAY_ARROW,
        bgcolor=COLOR_PRIMARY,
        color=COLOR_TEXT,
        height=BUTTON_HEIGHT,
        on_click=on_run_click,
    )

    # 4. Estruturação visual do formulário monocular
    form_mono = ft.Column(
        [
            ft.Row([tf_project_name]),
            ft.Container(height=5),
            card_mono_in.build_list_tile(),
            card_mono_out.build_list_tile(),
            ft.Divider(),
            ft.Row([tf_grid_rows, tf_grid_cols]),
            ft.Row([tf_square_size]),
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
                ft.Icon(ft.icons.CAMERA_ALT, size=45, color=COLOR_ICON),
                ft.Text("Calibração Monocular", size=24, weight="bold", color=COLOR_TEXT),
                ft.Container(height=10),
                form_mono,
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )


def create_stereo_calibration_page(page: ft.Page, selected_paths: Dict[str, Path]) -> ft.Container:
    """Gera a interface gráfica para a página de calibração de sistema estéreo.

    Configura a seleção independente das câmeras esquerda e direita, campos para geometria
    do padrão de calibração e vincula o processamento assíncrono estéreo ao `ExecutionDialog`.

    Args:
        page: Instância do Flet Page ativa na aplicação.
        selected_paths: Dicionário compartilhado de caminhos selecionados pelo usuário.

    Returns:
        ft.Container: Container Flet contendo a estrutura do formulário estéreo.
    """
    # 1. Definição dos campos de texto e hiperparâmetros do tabuleiro
    tf_project_name = ft.TextField(
        label="Nome do Projeto (Subpasta)",
        hint_text="Ex: meu_projeto_stereo",
        value="meu_projeto_stereo",
        expand=True,
    )
    tf_grid_rows = ft.TextField(label="Linhas de Cantos Internos", value="6", expand=True)
    tf_grid_cols = ft.TextField(label="Colunas de Cantos Internos", value="9", expand=True)
    tf_square_size = ft.TextField(label="Tamanho do Quadrado (m)", value="0.025", expand=True)

    # 2. Instanciação dos cards de seleção I/O para ambas as câmeras e saída
    card_left = IOPickerCard(
        page=page,
        title="Câmera Esquerda",
        icon=ft.icons.CAMERA_ALT,
        path_key="stereo_left_in",
        selected_paths=selected_paths,
    )

    card_right = IOPickerCard(
        page=page,
        title="Câmera Direita",
        icon=ft.icons.CAMERA_ALT,
        path_key="stereo_right_in",
        selected_paths=selected_paths,
    )

    card_out = IOPickerCard(
        page=page,
        title="Pasta de Destino",
        icon=ft.icons.CREATE_NEW_FOLDER,
        path_key="stereo_out",
        selected_paths=selected_paths,
    )

    # 3. Handler de execução para a rotina estéreo
    def on_run_click(e: ft.ControlEvent):
        cancel_event = threading.Event()

        dialog = ExecutionDialog(
            page=page,
            title="Calibração Estéreo",
            on_cancel=lambda: cancel_event.set(),
        )
        dialog.show()

        def set_ui_state(is_running: bool, status_msg: str):
            if not is_running:
                dialog.set_finished(success=True, message="Processamento finalizado com sucesso!")

        def run_task():
            handle_stereo_calibration(
                selected_paths=selected_paths,
                project_name_str=tf_project_name.value,
                rows_str=tf_grid_rows.value,
                cols_str=tf_grid_cols.value,
                square_size_str=tf_square_size.value,
                show_toast_callback=lambda msg, is_error=False: page.show_snack_bar(
                    ft.SnackBar(ft.Text(msg), bgcolor=ft.colors.RED_700 if is_error else ft.colors.GREEN_700)
                ),
                update_progress_callback=dialog.update_progress,
                set_ui_state_callback=set_ui_state,
                cancel_event=cancel_event,
            )

        threading.Thread(target=run_task, daemon=True).start()

    btn_run = ft.ElevatedButton(
        "Executar Calibração Estéreo",
        icon=ft.icons.PLAY_ARROW,
        bgcolor=COLOR_PRIMARY,
        color=COLOR_TEXT,
        height=BUTTON_HEIGHT,
        on_click=on_run_click,
    )

    # 4. Estruturação visual do formulário estéreo
    form_stereo = ft.Column(
        [
            ft.Row([tf_project_name]),
            ft.Container(height=5),
            card_left.build_list_tile(),
            card_right.build_list_tile(),
            card_out.build_list_tile(),
            ft.Divider(),
            ft.Row([tf_grid_rows, tf_grid_cols]),
            ft.Row([tf_square_size]),
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
                ft.Icon(ft.icons.CAMERA, size=45, color=COLOR_ICON),
                ft.Text("Calibração Estéreo", size=24, weight="bold", color=COLOR_TEXT),
                ft.Container(height=10),
                form_stereo,
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )