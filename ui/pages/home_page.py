from pathlib import Path
from typing import Callable, Dict
import flet as ft

from ui.theme import (
    COLOR_CARD_BG,
    COLOR_CARD_HOVER,
    COLOR_PRIMARY,
    COLOR_SUBTEXT,
    COLOR_TEXT,
)


def create_home_page(
    page: ft.Page,
    selected_paths: Dict[str, Path],
    on_navigate: Callable[[str], None],
) -> ft.Container:
    """Gera a View da Página Inicial contendo o menu dos módulos em lista estendida.

    Instancia a grade vertical de seleção para os módulos do sistema (Aquisição,
    Calibração, Reconstrução, Pós-Processamento, Projeção e Visualização), definindo
    o redirecionamento de rotas e o comportamento hover dos cards.

    Args:
        page: Instância do Flet Page ativa na aplicação.
        selected_paths: Dicionário compartilhado de caminhos selecionados pelo usuário.
        on_navigate: Callback responsável por acionar o roteador de navegação principal.

    Returns:
        ft.Container: Container Flet estruturado contendo o menu principal de navegação.
    """

    def build_module_card(
        title: str,
        description: str,
        icon: str,
        route_key: str,
    ) -> ft.Container:
        """Constrói um card retangular responsivo para exibição e navegação de módulo."""
        return ft.Container(
            content=ft.Row(
                [
                    # Lado Esquerdo: Ícone e Título do Módulo
                    ft.Row(
                        [
                            ft.Icon(icon, size=26, color=COLOR_PRIMARY),
                            ft.Text(title, size=15, weight="bold", color=COLOR_TEXT),
                        ],
                        spacing=12,
                        alignment=ft.MainAxisAlignment.START,
                    ),
                    # Lado Direito: Descrição do Módulo
                    ft.Text(
                        description,
                        size=12,
                        color=COLOR_SUBTEXT,
                        text_align=ft.TextAlign.RIGHT,
                        expand=True,
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            width=650,
            padding=ft.padding.symmetric(horizontal=20, vertical=16),
            bgcolor=COLOR_CARD_BG,
            border_radius=10,
            ink=True,
            on_click=lambda _: on_navigate(route_key),
            on_hover=lambda e: setattr(
                e.control,
                "bgcolor",
                COLOR_CARD_HOVER if e.data == "true" else COLOR_CARD_BG,
            )
            or e.control.update(),
        )

    # 1. Mapeamento de módulos do sistema e chaves de roteamento
    modules = [
        {
            "title": "Aquisição",
            "description": "Extração de frames e gerenciamento temporal de vídeos.",
            "icon": ft.icons.MOVIE_CREATION,
            "route_key": "acquisition",
        },
        {
            "title": "Calibração",
            "description": "Calibração intrínseca monocular e estéreo de câmeras.",
            "icon": ft.icons.CAMERA_ALT,
            "route_key": "calibration",
        },
        {
            "title": "Reconstrução 3D",
            "description": "Pipelines de reconstrução Monocular (SfM) e Estéreo.",
            "icon": ft.icons.LAYERS,
            "route_key": "reconstruction",
        },
        {
            "title": "Pós-Processamento",
            "description": "Filtros de contraste (CLAHE) e redimensionamento em lote.",
            "icon": ft.icons.TUNE,
            "route_key": "post_processing",
        },
        {
            "title": "Projeção 3D",
            "description": "Renderização de vistas sintéticas via COLMAP e PyVista.",
            "icon": ft.icons.CAMERA_OUTDOOR,
            "route_key": "projection",
        },
        {
            "title": "Visualização 3D",
            "description": "Inspeção e visualizador de nuvens de pontos e malhas.",
            "icon": ft.icons.VIEW_IN_AR,
            "route_key": "visualization",
        },
    ]

    # 2. Estruturação do Container principal da Home
    return ft.Container(
        alignment=ft.alignment.center,
        padding=20,
        content=ft.Column(
            controls=[
                build_module_card(
                    title=mod["title"],
                    description=mod["description"],
                    icon=mod["icon"],
                    route_key=mod["route_key"],
                )
                for mod in modules
            ],
            spacing=12,
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )