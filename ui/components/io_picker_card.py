from pathlib import Path
from typing import Dict, Optional
import flet as ft

from ui.theme import (
    COLOR_CARD_BG,
    COLOR_CARD_HOVER,
    COLOR_PRIMARY,
    COLOR_SUBTEXT,
    COLOR_TEXT,
)


class IOPickerCard:
    """Componente reutilizável para Seleção de Arquivos e Diretórios."""

    def __init__(
        self,
        page: ft.Page,
        title: str,
        icon: str,
        path_key: str,
        selected_paths: Dict[str, Path],
        is_directory: bool = True,
        width: int = 185,
        height: int = 125,
    ):
        self.page = page
        self.title = title
        self.icon = icon
        self.path_key = path_key
        self.selected_paths = selected_paths
        self.is_directory = is_directory
        self.width = width
        self.height = height

        self.lbl_path = ft.Text(
            "Nenhum selecionado...",
            size=11,
            color=COLOR_SUBTEXT,
            overflow=ft.TextOverflow.ELLIPSIS,
            max_lines=1,
        )

        self.picker = ft.FilePicker(on_result=self._on_result)
        if self.picker not in self.page.overlay:
            self.page.overlay.append(self.picker)

    def _on_result(self, e: ft.FilePickerResultEvent):
        if self.is_directory and e.path:
            p = Path(e.path)
            self.selected_paths[self.path_key] = p
            self.lbl_path.value = p.name
            self.lbl_path.color = COLOR_TEXT
        elif not self.is_directory and e.files and len(e.files) > 0:
            p = Path(e.files[0].path)
            self.selected_paths[self.path_key] = p
            self.lbl_path.value = p.name
            self.lbl_path.color = COLOR_TEXT
        self.page.update()

    def _open_picker(self, e):
        if self.is_directory:
            self.picker.get_directory_path(dialog_title=f"Selecionar {self.title}")
        else:
            self.picker.pick_files(dialog_title=f"Selecionar {self.title}")

    def build(self) -> ft.Container:
        """Gera o Card em formato de bloco/grade vertical."""
        return ft.Container(
            width=self.width,
            height=self.height,
            bgcolor=COLOR_CARD_BG,
            border=ft.border.all(1, ft.colors.OUTLINE_VARIANT),
            border_radius=12,
            padding=10,
            ink=True,
            on_click=self._open_picker,
            on_hover=lambda e: setattr(
                e.control, "bgcolor", COLOR_CARD_HOVER if e.data == "true" else COLOR_CARD_BG
            ) or self.page.update(),
            content=ft.Column(
                [
                    ft.Icon(self.icon, size=28, color=COLOR_PRIMARY),
                    ft.Text(
                        self.title,
                        size=12,
                        weight="bold",
                        color=COLOR_TEXT,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    self.lbl_path,
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=4,
            ),
        )

    def build_list_tile(self) -> ft.Container:
        """Gera o Card em formato retangular estendido de lista (faixa horizontal)."""
        return ft.Container(
            height=55,
            bgcolor=COLOR_CARD_BG,
            border_radius=8,
            padding=ft.padding.symmetric(horizontal=15, vertical=8),
            ink=True,
            on_click=self._open_picker,
            on_hover=lambda e: setattr(
                e.control, "bgcolor", COLOR_CARD_HOVER if e.data == "true" else COLOR_CARD_BG
            ) or self.page.update(),
            content=ft.Row(
                [
                    ft.Icon(self.icon, size=24, color=COLOR_PRIMARY),
                    ft.Column(
                        [
                            ft.Text(self.title, size=13, weight="bold", color=COLOR_TEXT),
                            self.lbl_path,
                        ],
                        spacing=1,
                        alignment=ft.MainAxisAlignment.CENTER,
                        expand=True,
                    ),
                    ft.Icon(ft.icons.CHEVRON_RIGHT, size=18, color=COLOR_SUBTEXT),
                ],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=12,
            ),
        )