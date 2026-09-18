from pathlib import Path
import threading
from typing import Dict
import flet as ft

from ui.components.execution_dialog import ExecutionDialog
from ui.components.io_picker_card import IOPickerCard
from ui.controllers.acquisition_controller import handle_extract_frames
from ui.theme import (
    BUTTON_HEIGHT,
    COLOR_ICON,
    COLOR_PRIMARY,
    COLOR_TEXT,
    FORM_WIDTH,
)


def create_extract_frames_page(page: ft.Page, selected_paths: Dict[str, Path]) -> ft.Container:
    """Gera a interface gráfica para a página de decomposição temporal e extração de fotogramas.

    Instancia os campos de texto para nome do projeto e FPS, os componentes `IOPickerCard`
    no layout de lista estendida (`build_list_tile`), e configura a execução assíncrona da tarefa
    vinculada ao modal de progresso `ExecutionDialog`.

    Args:
        page: Instância do Flet Page ativa na aplicação.
        selected_paths: Dicionário compartilhado de caminhos selecionados pelo usuário.

    Returns:
        ft.Container: Container Flet estruturado contendo o formulário de aquisição.
    """
    # 1. Definição dos campos de entrada de texto
    tf_acq_proj = ft.TextField(
        label="Nome do Projeto (Subpasta)",
        hint_text="Ex: amostragem_video",
        expand=True,
    )
    tf_acq_fps = ft.TextField(
        label="FPS Desejado",
        value="5",
        width=130,
    )

    # 2. Instanciação dos cards de seleção I/O em formato de lista retangular
    card_video = IOPickerCard(
        page=page,
        title="Vídeo de Origem",
        icon=ft.icons.VIDEO_FILE,
        path_key="video",
        selected_paths=selected_paths,
        is_directory=False,
    )

    card_out_dir = IOPickerCard(
        page=page,
        title="Pasta de Destino",
        icon=ft.icons.FOLDER_OPEN,
        path_key="output_dir",
        selected_paths=selected_paths,
        is_directory=True,
    )

    # 3. Handler de acionamento do processamento em thread separada
    def on_run_click(e: ft.ControlEvent):
        cancel_event = threading.Event()

        # Configuração do modal de execução com callback de cancelamento
        dialog = ExecutionDialog(
            page=page,
            title="Decomposição Temporal de Vídeo",
            on_cancel=lambda: cancel_event.set(),
        )
        dialog.show()

        def set_ui_state(is_running: bool, status_msg: str):
            if not is_running:
                dialog.set_finished(success=True, message="Processamento finalizado com sucesso!")

        def run_task():
            handle_extract_frames(
                selected_paths=selected_paths,
                project_name=tf_acq_proj.value,
                fps_str=tf_acq_fps.value,
                show_toast_callback=lambda msg, is_error=False: page.show_snack_bar(
                    ft.SnackBar(ft.Text(msg), bgcolor=ft.colors.RED_700 if is_error else ft.colors.GREEN_700)
                ),
                update_progress_callback=dialog.update_progress,
                set_ui_state_callback=set_ui_state,
                cancel_event=cancel_event,
            )

        # Dispara a tarefa em uma thread daemon para não travar a UI
        threading.Thread(target=run_task, daemon=True).start()

    # 4. Botão de execução
    btn_run = ft.ElevatedButton(
        "Extrair Frames",
        icon=ft.icons.PLAY_ARROW,
        bgcolor=COLOR_PRIMARY,
        color=COLOR_TEXT,
        height=BUTTON_HEIGHT,
        on_click=on_run_click,
    )

    # 5. Montagem da estrutura visual do formulário
    form_acquisition = ft.Column(
        [
            ft.Row([tf_acq_proj, tf_acq_fps]),
            ft.Container(height=5),
            card_video.build_list_tile(),
            card_out_dir.build_list_tile(),
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
                ft.Icon(ft.icons.MOVIE_CREATION, size=45, color=COLOR_ICON),
                ft.Text("Decomposição Temporal de Vídeo", size=24, weight="bold", color=COLOR_TEXT),
                ft.Container(height=10),
                form_acquisition,
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )