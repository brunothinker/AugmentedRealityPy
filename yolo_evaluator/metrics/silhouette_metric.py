"""Estratégia de avaliação de silhueta externa (IoU Global e Boundary F1-Score)."""

from typing import ClassVar

import cv2
import numpy as np

from .base import BaseMetric, EvaluationContext


class SilhouetteMetric(BaseMetric):
    """Avalia a preservação da área projetada e a nitidez do contorno externo."""

    name: ClassVar[str] = "silhouette"

    descriptions: ClassVar[dict[str, tuple[str, str]]] = {
        "iou_pct": (
            "Silhueta: IoU Área (↑ %)",
            "Sobreposição total da forma 2D (100% = idêntica).",
        ),
        "boundary_f1_pct": (
            "Silhueta: Borda F1 (↑ %)",
            "Precisão do contorno externo em 3px (cai se quinas arredondarem).",
        ),
    }

    def compute(self, ctx: EvaluationContext) -> dict[str, float]:
        """Calcula IoU de área e Boundary F1-Score com tolerância de 3 pixels.

        Args:
            ctx: Contexto da vista contendo ``mask_gt`` e ``mask_pred``.

        Returns:
            Dicionário com ``iou_pct`` e ``boundary_f1_pct`` (escala 0 a 100).
        """
        gt_bool = ctx.mask_gt > 127
        pred_bool = ctx.mask_pred > 127

        intersection = np.logical_and(gt_bool, pred_bool).sum()
        union = np.logical_or(gt_bool, pred_bool).sum()
        iou = float(intersection / union) * 100.0 if union > 0 else 0.0

        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        gt_boundary = (
            cv2.morphologyEx(gt_bool.astype(np.uint8), cv2.MORPH_GRADIENT, kernel) > 0
        )
        pred_boundary = (
            cv2.morphologyEx(pred_bool.astype(np.uint8), cv2.MORPH_GRADIENT, kernel) > 0
        )

        if not gt_boundary.any() or not pred_boundary.any():
            bf1 = 0.0
        else:
            tol_px = 3
            tol_kernel = cv2.getStructuringElement(
                cv2.MORPH_ELLIPSE, (2 * tol_px + 1, 2 * tol_px + 1)
            )
            gt_dilated = cv2.dilate(gt_boundary.astype(np.uint8), tol_kernel) > 0
            pred_dilated = cv2.dilate(pred_boundary.astype(np.uint8), tol_kernel) > 0

            precision = (
                np.logical_and(pred_boundary, gt_dilated).sum() / pred_boundary.sum()
            )
            recall = np.logical_and(gt_boundary, pred_dilated).sum() / gt_boundary.sum()
            bf1 = (
                float(2 * (precision * recall) / (precision + recall)) * 100.0
                if (precision + recall) > 0
                else 0.0
            )

        return {
            "iou_pct": iou,
            "boundary_f1_pct": bf1,
        }