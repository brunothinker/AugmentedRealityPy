from pathlib import Path
from typing import Dict
import flet as ft

from ui.controllers.projection.projection_controller import handle_render_projection
from ui.theme import (
    COLOR_PRIMARY,
    COLOR_ICON,
    COLOR_TEXT,
    COLOR_SUBTEXT,
    COLOR_SUCCESS,
    COLOR_ERROR,
    FORM_WIDTH,
    BUTTON_HEIGHT,
)
from ui.ui_utils import get_user_home_dir


def create_projection_page(page: ft.Page, selected_paths: Dict[str, Path]) -> ft.Container:
    """
    Gera a View da Tela de Projeção de Vistas Sintéticas (Mesh 3D + Poses COLMAP).
    """

    def show_toast(message: str, is_error: bool = False):
        color = COLOR_ERROR if is_error else COLOR_SUCCESS
        page.show_snack_bar(
            ft.SnackBar(ft.Text(message, weight="bold"), bgcolor=color)
        )

    # Elementos de Feedback Local
    progress_bar = ft.ProgressBar(width=FORM_WIDTH, value=0.0, visible=False, color=COLOR_PRIMARY)
    status_text = ft.Text("", italic=True, color=COLOR_SUBTEXT)

    def set_ui_state(is_running: bool, status_msg: str):
        progress_bar.visible = is_running
        # Mantém a barra em modo indeterminado se is_running for True
        progress_bar.value = None if is_running else 0.0
        status_text.value = status_msg
        btn_run.disabled = is_running
        page.update()

    # Campos do Formulário
    tf_proj_name = ft.TextField(
        label="Nome da Pasta de Saída",
        hint_text="Ex: projecao_teste",
        expand=True
    )

    # Labels de Seleção
    txt_colmap_dir = ft.Text(
        "Nenhum diretório COLMAP selecionado...",
        color=COLOR_SUBTEXT,
        expand=True,
        no_wrap=True,
        overflow=ft.TextOverflow.ELLIPSIS
    )

    txt_mesh_file = ft.Text(
        "Nenhuma Mesh (.ply/.obj) selecionada...",
        color=COLOR_SUBTEXT,
        expand=True,
        no_wrap=True,
        overflow=ft.TextOverflow.ELLIPSIS
    )

    # Handlers dos Pickers
    def on_colmap_dir_result(e: ft.FilePickerResultEvent):
        if e.path:
            selected_paths["colmap_dir"] = Path(e.path)
            txt_colmap_dir.value = f".../{selected_paths['colmap_dir'].name}"
            txt_colmap_dir.color = COLOR_TEXT
            page.update()

    def on_mesh_result(e: ft.FilePickerResultEvent):
        if e.files:
            selected_paths["mesh_file"] = Path(e.files[0].path)
            txt_mesh_file.value = f".../{selected_paths['mesh_file'].name}"
            txt_mesh_file.color = COLOR_TEXT
            page.update()

    picker_colmap_dir = ft.FilePicker(on_result=on_colmap_dir_result)
    picker_mesh_file = ft.FilePicker(on_result=on_mesh_result)
    page.overlay.extend([picker_colmap_dir, picker_mesh_file])

    btn_run = ft.ElevatedButton(
        "Renderizar Projeções",
        on_click=lambda e: handle_render_projection(
            selected_paths=selected_paths,
            output_folder_name=tf_proj_name.value,
            show_toast_callback=show_toast,
            set_ui_state_callback=set_ui_state,
        ),
        icon=ft.icons.CAMERA_OUTDOOR,
        bgcolor=COLOR_PRIMARY,
        color=COLOR_TEXT,
        height=BUTTON_HEIGHT
    )

    form_projection = ft.Column([
        ft.Row([tf_proj_name]),
        ft.Container(height=5),

        # Seleção da Pasta do COLMAP (onde ficam os .bin)
        ft.Row([
            ft.ElevatedButton(
                "Pasta COLMAP (sparse)",
                icon=ft.icons.FOLDER_SPECIAL,
                on_click=lambda _: picker_colmap_dir.get_directory_path(
                    initial_directory=get_user_home_dir()
                ),
                width=200
            ),
            txt_colmap_dir
        ]),

        # Seleção da Mesh 3D
        ft.Row([
            ft.ElevatedButton(
                "Selecionar Mesh (.ply)",
                icon=ft.icons.VIEW_IN_AR,
                on_click=lambda _: picker_mesh_file.pick_files(
                    allowed_extensions=["ply", "obj", "stl"],
                    initial_directory=get_user_home_dir()
                ),
                width=200
            ),
            txt_mesh_file
        ]),

        ft.Container(height=10),
        progress_bar,
        status_text,
        ft.Container(height=5),
        btn_run
    ], width=FORM_WIDTH, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)

    return ft.Container(
        alignment=ft.alignment.center,
        padding=25,
        content=ft.Column([
            ft.Icon(ft.icons.CAMERA_OUTDOOR, size=45, color=COLOR_ICON),
            ft.Text("Projeção de Vistas Sintéticas", size=24, weight="bold", color=COLOR_TEXT),
            ft.Container(height=10),
            form_projection
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    )


# Teste Isolado da Página
def main(page: ft.Page):
    page.title = "Teste - Projeção de Vistas"
    page.theme_mode = ft.ThemeMode.DARK
    page.window_width = 800
    page.window_height = 650
    page.window_center()

    selected_paths = {}
    page.add(create_projection_page(page, selected_paths))


if __name__ == "__main__":
    ft.app(target=main)