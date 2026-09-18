from pathlib import Path
from typing import Dict, List
import flet as ft

from ui.router import ROUTE_REGISTRY, build_page_view
from ui.theme import (
    COLOR_CARD_BG,
    COLOR_PRIMARY,
    COLOR_TEXT,
)


def create_app_layout(page: ft.Page, selected_paths: Dict[str, Path]) -> ft.Container:
    """Cria a moldura (shell) principal do aplicativo com controle de navegação.

    Gerencia o histórico de navegação (`navigation_stack`), atualiza dinamicamente o
    cabeçalho com título e botão de retorno, e renderiza as views através do `build_page_view`.

    Args:
        page: Instância do Flet Page ativa na aplicação.
        selected_paths: Dicionário compartilhado contendo os caminhos selecionados pelo usuário.

    Returns:
        ft.Container: Moldura de layout contendo a barra superior fixa e a área de conteúdo.
    """
    # 1. Pilha para gerenciamento do histórico de navegação
    navigation_stack: List[str] = ["home"]

    # 2. Componentes visuais do Cabeçalho Fixo
    btn_back = ft.IconButton(
        icon=ft.icons.ARROW_BACK_IOS_NEW,
        icon_color=COLOR_PRIMARY,
        tooltip="Voltar",
        visible=False,
        on_click=lambda _: go_back(),
    )

    lbl_page_title = ft.Text(
        value="",
        size=20,
        weight="bold",
        color=COLOR_TEXT,
        text_align=ft.TextAlign.CENTER,
    )

    # 3. Container dinâmico central
    content_area = ft.Container(expand=True)

    def update_header_and_content() -> None:
        """Atualiza a barra superior e substitui a view exibida na área de conteúdo."""
        current_route = navigation_stack[-1]
        route_info = ROUTE_REGISTRY.get(current_route, {})

        lbl_page_title.value = route_info.get("title", "Visão Computacional 3D")
        btn_back.visible = len(navigation_stack) > 1

        content_area.content = build_page_view(
            route_key=current_route,
            page=page,
            selected_paths=selected_paths,
            on_navigate=navigate_to,
        )

        page.update()

    def navigate_to(target_route: str) -> None:
        """Navega para uma rota informada empilhando-a no histórico de navegação."""
        navigation_stack.append(target_route)
        update_header_and_content()

    def go_back() -> None:
        """Desempilha a rota atual e retorna para a tela anterior no histórico."""
        if len(navigation_stack) > 1:
            navigation_stack.pop()
            update_header_and_content()

    # 4. Estruturação do Cabeçalho Fixo Superior
    header_bar = ft.Container(
        height=60,
        padding=ft.padding.symmetric(horizontal=15),
        bgcolor=COLOR_CARD_BG,
        border_radius=8,
        content=ft.Row(
            [
                ft.Container(content=btn_back, width=50, alignment=ft.alignment.center_left),
                ft.Container(content=lbl_page_title, expand=True, alignment=ft.alignment.center),
                ft.Container(width=50),  # Espaçador simétrico para alinhamento central do título
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )

    # 5. Inicialização da rota padrão
    update_header_and_content()

    # 6. Container principal do aplicativo
    return ft.Container(
        expand=True,
        padding=10,
        content=ft.Column(
            [
                header_bar,
                ft.Container(height=10),
                content_area,
            ],
            expand=True,
        ),
    )