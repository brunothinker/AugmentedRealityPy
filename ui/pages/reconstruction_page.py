from pathlib import Path
import threading
from typing import Dict
import flet as ft

from ui.components.execution_dialog import ExecutionDialog
from ui.components.io_picker_card import IOPickerCard
from ui.controllers.reconstruction_controller import (
    handle_mono_reconstruction,
    handle_stereo_reconstruction,
)
from ui.theme import (
    BUTTON_HEIGHT,
    COLOR_ICON,
    COLOR_PRIMARY,
    COLOR_TEXT,
    FORM_WIDTH,
)


def create_mono_reconstruction_page(page: ft.Page, selected_paths: Dict[str, Path]) -> ft.Container:
    """Gera a View da Reconstrução Monocular 3D usando componentes reutilizáveis."""

    tf_project_name = ft.TextField(
        label="Nome do Projeto (Subpasta)",
        hint_text="Ex: meu_projeto_mono_3d",
        value="meu_projeto_mono_3d",
        expand=True,
    )

    card_mono_images = IOPickerCard(
        page=page,
        title="Pasta de Imagens",
        icon=ft.icons.FOLDER,
        path_key="mono_rec_images",
        selected_paths=selected_paths,
    )

    card_mono_out = IOPickerCard(
        page=page,
        title="Pasta de Destino",
        icon=ft.icons.CREATE_NEW_FOLDER,
        path_key="mono_rec_out",
        selected_paths=selected_paths,
    )

    def on_run_click(e: ft.ControlEvent):
        cancel_event = threading.Event()

        dialog = ExecutionDialog(
            page=page,
            title="Reconstrução Monocular 3D",
            on_cancel=lambda: cancel_event.set(),
        )
        dialog.show()

        def set_ui_state(is_running: bool, status_msg: str):
            if not is_running:
                dialog.set_finished(success=True, message="Processamento finalizado com sucesso!")

        def run_task():
            handle_mono_reconstruction(
                selected_paths=selected_paths,
                project_name=tf_project_name.value,
                show_toast_callback=lambda msg, is_error=False: page.show_snack_bar(
                    ft.SnackBar(ft.Text(msg), bgcolor=ft.colors.RED_700 if is_error else ft.colors.GREEN_700)
                ),
                update_progress_callback=dialog.update_progress,
                set_ui_state_callback=set_ui_state,
                cancel_event=cancel_event,
            )

        threading.Thread(target=run_task, daemon=True).start()

    btn_run = ft.ElevatedButton(
        "Executar Reconstrução Monocular",
        icon=ft.icons.PLAY_ARROW,
        bgcolor=COLOR_PRIMARY,
        color=COLOR_TEXT,
        height=BUTTON_HEIGHT,
        on_click=on_run_click,
    )

    form_mono_rec = ft.Column(
        [
            ft.Row([tf_project_name]),
            ft.Container(height=5),
            card_mono_images.build_list_tile(),
            card_mono_out.build_list_tile(),
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
                ft.Text("Reconstrução Monocular (3D)", size=24, weight="bold", color=COLOR_TEXT),
                ft.Container(height=10),
                form_mono_rec,
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )


def create_stereo_reconstruction_page(page: ft.Page, selected_paths: Dict[str, Path]) -> ft.Container:
    """Gera a View da Reconstrução Estéreo 3D usando componentes reutilizáveis."""

    tf_project_name = ft.TextField(
        label="Nome do Projeto (Subpasta)",
        hint_text="Ex: meu_projeto_stereo_3d",
        value="meu_projeto_stereo_3d",
        expand=True,
    )

    tf_baseline = ft.TextField(
        label="Baseline (Distância entre Câmeras em Metros)",
        value="0.10",
        expand=True,
    )

    card_cam_left = IOPickerCard(
        page=page,
        title="Câmera Esquerda",
        icon=ft.icons.FOLDER,
        path_key="stereo_rec_left",
        selected_paths=selected_paths,
    )

    card_cam_right = IOPickerCard(
        page=page,
        title="Câmera Direita",
        icon=ft.icons.FOLDER,
        path_key="stereo_rec_right",
        selected_paths=selected_paths,
    )

    card_out_dir = IOPickerCard(
        page=page,
        title="Pasta de Destino",
        icon=ft.icons.CREATE_NEW_FOLDER,
        path_key="stereo_rec_out",
        selected_paths=selected_paths,
    )

    def on_run_click(e: ft.ControlEvent):
        cancel_event = threading.Event()

        dialog = ExecutionDialog(
            page=page,
            title="Reconstrução Estéreo 3D",
            on_cancel=lambda: cancel_event.set(),
        )
        dialog.show()

        def set_ui_state(is_running: bool, status_msg: str):
            if not is_running:
                dialog.set_finished(success=True, message="Processamento finalizado com sucesso!")

        def run_task():
            handle_stereo_reconstruction(
                selected_paths=selected_paths,
                project_name=tf_project_name.value,
                baseline_str=tf_baseline.value,
                show_toast_callback=lambda msg, is_error=False: page.show_snack_bar(
                    ft.SnackBar(ft.Text(msg), bgcolor=ft.colors.RED_700 if is_error else ft.colors.GREEN_700)
                ),
                update_progress_callback=dialog.update_progress,
                set_ui_state_callback=set_ui_state,
                cancel_event=cancel_event,
            )

        threading.Thread(target=run_task, daemon=True).start()

    btn_run = ft.ElevatedButton(
        "Executar Reconstrução Estéreo",
        icon=ft.icons.PLAY_ARROW,
        bgcolor=COLOR_PRIMARY,
        color=COLOR_TEXT,
        height=BUTTON_HEIGHT,
        on_click=on_run_click,
    )

    form_stereo_rec = ft.Column(
        [
            ft.Row([tf_project_name]),
            ft.Container(height=5),
            card_cam_left.build_list_tile(),
            card_cam_right.build_list_tile(),
            card_out_dir.build_list_tile(),
            ft.Divider(),
            ft.Row([tf_baseline]),
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
                ft.Icon(ft.icons.LAYERS, size=45, color=COLOR_ICON),
                ft.Text("Reconstrução Estéreo (3D)", size=24, weight="bold", color=COLOR_TEXT),
                ft.Container(height=10),
                form_stereo_rec,
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )