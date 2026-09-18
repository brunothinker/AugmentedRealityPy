from pathlib import Path
from typing import Any, Callable, Dict, List
import flet as ft

from ui.theme import (
    COLOR_CARD_BG,
    COLOR_CARD_HOVER,
    COLOR_ICON,
    COLOR_PRIMARY,
    COLOR_SUBTEXT,
    COLOR_TEXT,
)


def create_generic_hub_page(
    page: ft.Page,
    selected_paths: Dict[str, Path],
    on_navigate: Callable[[str], None],
    main_icon: str,
    title: str,
    subtitle: str,
    options: List[Dict[str, Any]],
) -> ft.Container:
    """
    Construtor genérico polimórfico de páginas Hub para a interface.
    Elimina a necessidade de ter controllers e telas duplicadas para hubs de navegação.
    """

    def build_option_card(
        title: str,
        description: str,
        icon: str,
        route_key: str,
    ) -> ft.Container:
        """Contrói um card clicável de opção para os módulos do app."""
        return ft.Container(
            content=ft.Column(
                [
                    ft.Icon(icon, size=40, color=COLOR_PRIMARY),
                    ft.Text(
                        title,
                        size=18,
                        weight="bold",
                        color=COLOR_TEXT,
                    ),
                    ft.Text(
                        description,
                        size=12,
                        color=COLOR_SUBTEXT,
                        text_align=ft.TextAlign.CENTER,
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            width=260,
            height=190,
            padding=20,
            bgcolor=COLOR_CARD_BG,
            border_radius=12,
            ink=True,
            on_click=lambda _: on_navigate(route_key),
            on_hover=lambda e: setattr(
                e.control,
                "bgcolor",
                COLOR_CARD_HOVER if e.data == "true" else COLOR_CARD_BG,
            )
            or e.control.update(),
        )

    return ft.Container(
        expand=True,
        alignment=ft.alignment.center,
        padding=25,
        content=ft.Column(
            [
                ft.Icon(main_icon, size=50, color=COLOR_ICON),
                ft.Text(
                    title,
                    size=26,
                    weight="bold",
                    color=COLOR_TEXT,
                ),
                ft.Text(subtitle, color=COLOR_SUBTEXT),
                ft.Container(height=20),
                ft.Row(
                    [
                        build_option_card(
                            title=opt["title"],
                            description=opt["description"],
                            icon=opt["icon"],
                            route_key=opt["route_key"],
                        )
                        for opt in options
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=20,
                    wrap=True,
                ),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )