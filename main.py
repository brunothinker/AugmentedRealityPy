from pathlib import Path

import flet as ft

from ui.app_layout import create_app_layout


def start_gui():
    """Inicia a Interface Gráfica com Flet."""
    def main_ui(page: ft.Page):
        page.title = "Augmented Reality - UFOP"
        page.theme_mode = ft.ThemeMode.DARK
        page.window_width = 1024
        page.window_height = 768
        page.window_center()

        selected_paths: dict[str, Path] = {}
        page.add(create_app_layout(page, selected_paths))
    ft.app(target=main_ui)


if __name__ == "__main__":
    start_gui()