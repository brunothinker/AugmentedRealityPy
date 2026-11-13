"""Estratégia de avaliação topológica (Característica de Euler e IoU de cavidades)."""

from typing import ClassVar

import cv2
import numpy as np

from .base import BaseMetric, EvaluationContext


class TopologyMetric(BaseMetric):
    """Avalia se buracos internos e componentes conectados foram preservados."""

    name: ClassVar[str] = "topology"

    descriptions: ClassVar[dict[str, tuple[str, str]]] = {
        "holes_gt": (
            "Topologia: Furos Reais (ref)",
            "Média de cavidades internas detectadas na foto real (alvo).",
        ),
        "holes_pred": (
            "Topologia: Furos 3D (≈ ref)",
            "Média de cavidades detectadas no render (ideal = igual a Furos Reais).",
        ),
        "euler_error": (
            "Topologia: Erro Euler (↓)",
            "Diferença topológica |χ_real - χ_3D| (0 = sem furos fechados/falsos).",
        ),
        "hole_iou_pct": (
            "Topologia: IoU Furos (↑ %)",
            "Sobreposição exclusiva das cavidades internas (100% = preservado).",
        ),
    }

    @staticmethod
    def _analyze_topology(
        mask: np.ndarray, min_area: int = 500
    ) -> tuple[int, int, np.ndarray]:
        """Extrai componentes conectados, buracos fechados e a máscara de cavidades.

        Args:
            mask: Máscara binária (0 ou 255).
            min_area: Área mínima em pixels para filtrar ruídos de segmentação.

        Returns:
            Tupla ``(num_componentes, num_buracos, mascara_booleana_buracos)``.
        """
        bin_mask = (mask > 127).astype(np.uint8)
        h, w = bin_mask.shape

        n_comp, _, stats_fg, _ = cv2.connectedComponentsWithStats(
            bin_mask, connectivity=8
        )
        valid_comps = sum(
            1 for i in range(1, n_comp) if stats_fg[i, cv2.CC_STAT_AREA] >= min_area
        )

        inverted = 1 - bin_mask
        n_bg, labels_bg, stats_bg, _ = cv2.connectedComponentsWithStats(
            inverted, connectivity=4
        )

        holes = 0
        holes_mask = np.zeros_like(bin_mask, dtype=bool)
        for i in range(1, n_bg):
            x, y, bw, bh, area = stats_bg[i]
            touches_border = (
                x <= 1 or y <= 1 or (x + bw) >= (w - 1) or (y + bh) >= (h - 1)
            )
            if not touches_border and area >= min_area:
                holes += 1
                holes_mask |= labels_bg == i

        return valid_comps, holes, holes_mask

    def compute(self, ctx: EvaluationContext) -> dict[str, float]:
        """Calcula o erro absoluto da Característica de Euler (C - H) e o Hole IoU.

        Args:
            ctx: Contexto da vista contendo ``mask_gt`` e ``mask_pred``.

        Returns:
            Dicionário com ``holes_gt``, ``holes_pred``, ``euler_error`` e ``hole_iou_pct``.
        """
        comp_gt, holes_gt, holes_mask_gt = self._analyze_topology(ctx.mask_gt)
        comp_pred, holes_pred, holes_mask_pred = self._analyze_topology(ctx.mask_pred)

        euler_gt = comp_gt - holes_gt
        euler_pred = comp_pred - holes_pred
        euler_abs_error = float(abs(euler_gt - euler_pred))

        if holes_gt == 0 and holes_pred == 0:
            hole_iou = 100.0
        else:
            inter = np.logical_and(holes_mask_gt, holes_mask_pred).sum()
            union = np.logical_or(holes_mask_gt, holes_mask_pred).sum()
            hole_iou = float(inter / union) * 100.0 if union > 0 else 0.0

        return {
            "holes_gt": float(holes_gt),
            "holes_pred": float(holes_pred),
            "euler_error": euler_abs_error,
            "hole_iou_pct": hole_iou,
        }