from pathlib import Path
from typing import Dict
import flet as ft

from ui.components.io_picker_card import IOPickerCard
from ui.controllers.visualization_controller import handle_visualization
from ui.theme import (
    BUTTON_HEIGHT,
    COLOR_ICON,
    COLOR_PRIMARY,
    COLOR_TEXT,
    FORM_WIDTH,
)


def create_visualization_page(page: ft.Page, selected_paths: Dict[str, Path]) -> ft.Container:
    """Gera a interface gráfica para a página de inspeção e visualização volumétrica 3D.

    Instancia o seletor de arquivos de malha/nuvem de pontos (`.ply` ou `.obj`) utilizando
    o componente `IOPickerCard` no layout de lista estendida (`build_list_tile`), e configura
    o callback de notificação e acionamento da janela externa do PyVista.

    Args:
        page: Instância do Flet Page ativa na aplicação.
        selected_paths: Dicionário compartilhado de caminhos selecionados pelo usuário.

    Returns:
        ft.Container: Container Flet estruturado contendo a view de visualização 3D.
    """

    # 1. Função utilitária interna para exibição de SnackBars/Toasts de feedback
    def show_toast(message: str, is_error: bool = False):
        page.show_snack_bar(
            ft.SnackBar(
                ft.Text(message, weight="bold"),
                bgcolor=ft.colors.RED_700 if is_error else ft.colors.GREEN_700,
            )
        )

    # 2. Instanciação do card de seleção I/O para arquivos de malha 3D
    card_model = IOPickerCard(
        page=page,
        title="Modelo 3D (.ply / .obj)",
        icon=ft.icons.VIEW_IN_AR,
        path_key="model",
        selected_paths=selected_paths,
        is_directory=False,
    )

    # 3. Botão para acionamento do renderizador
    btn_run = ft.ElevatedButton(
        "Renderizar Modelo 3D",
        icon=ft.icons.PLAY_CIRCLE_FILL,
        bgcolor=COLOR_PRIMARY,
        color=COLOR_TEXT,
        height=BUTTON_HEIGHT,
        on_click=lambda e: handle_visualization(selected_paths, show_toast),
    )

    # 4. Estruturação visual do formulário de visualização
    form_visualization = ft.Column(
        [
            card_model.build_list_tile(),
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
                ft.Icon(ft.icons.VIEW_IN_AR, size=45, color=COLOR_ICON),
                ft.Text("Inspeção Volumétrica 3D", size=24, weight="bold", color=COLOR_TEXT),
                ft.Container(height=10),
                form_visualization,
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )