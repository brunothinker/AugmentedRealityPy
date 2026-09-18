from pathlib import Path
import threading
from typing import Dict
import flet as ft

from ui.components.execution_dialog import ExecutionDialog
from ui.components.io_picker_card import IOPickerCard
from ui.controllers.projection_controller import handle_render_projection
from ui.theme import (
    BUTTON_HEIGHT,
    COLOR_ICON,
    COLOR_PRIMARY,
    COLOR_TEXT,
    FORM_WIDTH,
)


def create_projection_page(page: ft.Page, selected_paths: Dict[str, Path]) -> ft.Container:
    """Gera a View da Tela de Projeção usando o componente IOPickerCard em lista."""

    tf_proj_name = ft.TextField(
        label="Nome do Projeto (Subpasta)",
        hint_text="Ex: projecao_teste",
        value="projecao_teste",
        expand=True,
    )

    card_colmap_dir = IOPickerCard(
        page=page,
        title="Pasta COLMAP (sparse)",
        icon=ft.icons.FOLDER_SPECIAL,
        path_key="colmap_dir",
        selected_paths=selected_paths,
        is_directory=True,
    )

    card_mesh_file = IOPickerCard(
        page=page,
        title="Mesh 3D (.ply / .obj)",
        icon=ft.icons.VIEW_IN_AR,
        path_key="mesh_file",
        selected_paths=selected_paths,
        is_directory=False,
    )

    card_out_dir = IOPickerCard(
        page=page,
        title="Pasta de Destino",
        icon=ft.icons.CREATE_NEW_FOLDER,
        path_key="projection_out",
        selected_paths=selected_paths,
        is_directory=True,
    )

    def on_run_click(e: ft.ControlEvent):
        dialog = ExecutionDialog(page=page, title="Projeção de Vistas Sintéticas")
        dialog.show()

        def set_ui_state(is_running: bool, status_msg: str):
            if not is_running:
                dialog.set_finished(success=True, message="Projeções renderizadas com sucesso!")

        def run_task():
            handle_render_projection(
                selected_paths=selected_paths,
                output_folder_name=tf_proj_name.value,
                show_toast_callback=lambda msg, is_error=False: page.show_snack_bar(
                    ft.SnackBar(ft.Text(msg), bgcolor=ft.colors.RED_700 if is_error else ft.colors.GREEN_700)
                ),
                set_ui_state_callback=set_ui_state,
            )

        threading.Thread(target=run_task, daemon=True).start()

    btn_run = ft.ElevatedButton(
        "Renderizar Projeções",
        icon=ft.icons.CAMERA_OUTDOOR,
        bgcolor=COLOR_PRIMARY,
        color=COLOR_TEXT,
        height=BUTTON_HEIGHT,
        on_click=on_run_click,
    )

    form_projection = ft.Column(
        [
            ft.Row([tf_proj_name]),
            ft.Container(height=5),
            card_colmap_dir.build_list_tile(),
            card_mesh_file.build_list_tile(),
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
                ft.Icon(ft.icons.CAMERA_OUTDOOR, size=45, color=COLOR_ICON),
                ft.Text("Projeção de Vistas Sintéticas", size=24, weight="bold", color=COLOR_TEXT),
                ft.Container(height=10),
                form_projection,
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )