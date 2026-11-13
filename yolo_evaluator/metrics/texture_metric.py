"""Estratégia de avaliação de aparência/textura desacoplada da geometria."""

from typing import ClassVar

import cv2
import numpy as np

from .base import BaseMetric, EvaluationContext


class TextureMetric(BaseMetric):
    """Mede fidelidade estrutural (SSIM) e cromática (HSV) apenas na interseção do objeto."""

    name: ClassVar[str] = "texture"

    descriptions: ClassVar[dict[str, tuple[str, str]]] = {
        "masked_ssim_pct": (
            "Textura: SSIM Interno (↑ %)",
            "Fidelidade estrutural e nitidez da textura dentro da máscara.",
        ),
        "color_corr_pct": (
            "Textura: Cor HSV (↑ %)",
            "Correlação de distribuição de cores dentro do objeto.",
        ),
    }

    @staticmethod
    def _masked_ssim(img1: np.ndarray, img2: np.ndarray, mask: np.ndarray) -> float:
        """Calcula o índice SSIM médio restrito aos pixels ativos da máscara.

        Args:
            img1: Imagem de referência em BGR.
            img2: Imagem renderizada em BGR.
            mask: Máscara binária da interseção válida (0 ou 255).

        Returns:
            Similaridade estrutural média em porcentagem (0 a 100).
        """
        g1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY).astype(np.float64)
        g2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY).astype(np.float64)

        c1 = (0.01 * 255) ** 2
        c2 = (0.03 * 255) ** 2

        mu1 = cv2.GaussianBlur(g1, (11, 11), 1.5)
        mu2 = cv2.GaussianBlur(g2, (11, 11), 1.5)

        mu1_sq = mu1 * mu1
        mu2_sq = mu2 * mu2
        mu1_mu2 = mu1 * mu2

        sigma1_sq = cv2.GaussianBlur(g1 * g1, (11, 11), 1.5) - mu1_sq
        sigma2_sq = cv2.GaussianBlur(g2 * g2, (11, 11), 1.5) - mu2_sq
        sigma12 = cv2.GaussianBlur(g1 * g2, (11, 11), 1.5) - mu1_mu2

        ssim_map = ((2 * mu1_mu2 + c1) * (2 * sigma12 + c2)) / (
            (mu1_sq + mu2_sq + c1) * (sigma1_sq + sigma2_sq + c2)
        )

        valid = mask > 127
        if not valid.any():
            return 0.0
        return float(np.mean(ssim_map[valid])) * 100.0

    def compute(self, ctx: EvaluationContext) -> dict[str, float]:
        """Calcula SSIM mascarado e correlação de histograma HSV na interseção.

        Args:
            ctx: Contexto da vista contendo imagens e máscaras.

        Returns:
            Dicionário com ``masked_ssim_pct`` e ``color_corr_pct``.
        """
        inter_mask = ((ctx.mask_gt > 127) & (ctx.mask_pred > 127)).astype(np.uint8) * 255
        if (inter_mask > 127).sum() < 20:
            return {"masked_ssim_pct": 0.0, "color_corr_pct": 0.0}

        ssim_score = self._masked_ssim(ctx.real_bgr, ctx.render_bgr, inter_mask)

        hsv_gt = cv2.cvtColor(ctx.real_bgr, cv2.COLOR_BGR2HSV)
        hsv_pred = cv2.cvtColor(ctx.render_bgr, cv2.COLOR_BGR2HSV)
        hist_gt = cv2.calcHist([hsv_gt], [0, 1], inter_mask, [32, 32], [0, 180, 0, 256])
        hist_pred = cv2.calcHist(
            [hsv_pred], [0, 1], inter_mask, [32, 32], [0, 180, 0, 256]
        )
        cv2.normalize(hist_gt, hist_gt)
        cv2.normalize(hist_pred, hist_pred)

        corr = cv2.compareHist(hist_gt, hist_pred, cv2.HISTCMP_CORREL)
        color_score = float(np.clip((corr + 1.0) / 2.0, 0.0, 1.0)) * 100.0

        return {
            "masked_ssim_pct": ssim_score,
            "color_corr_pct": color_score,
        }