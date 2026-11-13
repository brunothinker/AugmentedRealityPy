"""Orquestrador modular de avaliação quantitativa para reconstruções 3D projetadas em 2D.

Carrega os modelos YOLO e SAM uma única vez, monta o contexto compartilhado
por vista e despacha o cálculo para todas as estratégias registradas em ``metrics/``.
"""

import argparse
import csv
import os
from collections import defaultdict
from contextlib import contextmanager
from pathlib import Path

import cv2
import numpy as np
from core.extractor import MaskExtractor
from metrics import BaseMetric, EvaluationContext, discover_metrics
from tqdm import tqdm


@contextmanager
def suppress_c_stderr():
    """Redireciona temporariamente o descritor ``stderr`` (fd 2) para ``/dev/null``."""
    stderr_fd = os.dup(2)
    devnull = os.open(os.devnull, os.O_WRONLY)
    os.dup2(devnull, 2)
    os.close(devnull)
    try:
        yield
    finally:
        os.dup2(stderr_fd, 2)
        os.close(stderr_fd)


def imread_quiet(path: Path, flags: int = cv2.IMREAD_COLOR) -> np.ndarray | None:
    """Lê uma imagem com OpenCV suprimindo avisos de metadados JPEG no terminal."""
    with suppress_c_stderr():
        return cv2.imread(str(path), flags)


def run_benchmark(
    real_dir: Path,
    gt_masks_dir: Path,
    models_map: dict[str, Path],
    selected_metrics: list[BaseMetric],
    extractor: MaskExtractor,
    csv_out: Path,
    solid_object: bool = False,
) -> None:
    """Executa todas as estratégias selecionadas nos modelos 3D e imprime as tabelas."""
    gt_files = sorted(gt_masks_dir.rglob("*.png"))
    if not gt_files:
        raise FileNotFoundError(f"Nenhuma máscara GT encontrada em: {gt_masks_dir}")

    real_index: dict[str, Path] = {}
    for ext in ("*.jpg", "*.jpeg", "*.png", "*.JPG", "*.PNG"):
        for p in real_dir.rglob(ext):
            real_index[p.stem] = p

    labels_map: dict[str, str] = {}
    legend_entries: list[tuple[str, str]] = []
    for metric in selected_metrics:
        for sub_key, (label, desc) in metric.descriptions.items():
            full_key = f"{metric.name}.{sub_key}"
            labels_map[full_key] = label
            legend_entries.append((label, desc))

    all_rows: list[dict[str, str | float]] = []

    for model_name, renders_dir in models_map.items():
        if not renders_dir.exists():
            continue

        render_index: dict[str, Path] = {}
        for ext in ("*.jpg", "*.jpeg", "*.png", "*.JPG", "*.PNG"):
            for p in renders_dir.rglob(ext):
                render_index[p.stem.removeprefix("synth_")] = p

        agg_all: dict[str, list[float]] = defaultdict(list)
        agg_1x: dict[str, list[float]] = defaultdict(list)
        agg_uw: dict[str, list[float]] = defaultdict(list)

        progress = tqdm(
            gt_files,
            desc=f"Avaliando {model_name.upper():<5}",
            unit="vista",
            leave=False,
        )

        for gt_path in progress:
            stem = gt_path.stem
            real_path = real_index.get(stem)
            render_path = render_index.get(stem)
            if real_path is None or render_path is None:
                continue

            mask_gt = imread_quiet(gt_path, cv2.IMREAD_GRAYSCALE)
            real_bgr = imread_quiet(real_path)
            render_bgr = imread_quiet(render_path)
            if mask_gt is None or real_bgr is None or render_bgr is None:
                continue

            if render_bgr.shape[:2] != mask_gt.shape:
                render_bgr = cv2.resize(
                    render_bgr, (mask_gt.shape[1], mask_gt.shape[0])
                )
            if real_bgr.shape[:2] != mask_gt.shape:
                real_bgr = cv2.resize(real_bgr, (mask_gt.shape[1], mask_gt.shape[0]))

            ys, xs = np.where(mask_gt > 127)
            gt_bbox = (
                [float(xs.min()), float(ys.min()), float(xs.max()), float(ys.max())]
                if len(xs) > 0
                else None
            )

            hole_pts = (
                None
                if solid_object
                else extractor.find_hole_centroids(mask_gt, min_area=500)
            )
            mask_pred, pred_bbox, yolo_conf = extractor.extract_mask(
                render_bgr, fallback_bbox=gt_bbox, negative_points=hole_pts
            )
            if mask_pred is None:
                mask_pred = np.zeros_like(mask_gt)

            cam_type = "1x" if ("_1x" in stem or "direita" in str(gt_path)) else "uw"

            ctx = EvaluationContext(
                view_name=stem,
                camera_type=cam_type,
                real_bgr=real_bgr,
                render_bgr=render_bgr,
                mask_gt=mask_gt,
                mask_pred=mask_pred,
                bbox_gt=gt_bbox,
                bbox_pred=pred_bbox,
                yolo_conf=yolo_conf,
            )

            row: dict[str, str | float] = {
                "model": model_name,
                "view": stem,
                "camera": cam_type,
                "yolo_conf_pct": round(yolo_conf * 100.0, 2),
            }

            for metric in selected_metrics:
                scores = metric.compute(ctx)
                for k, v in scores.items():
                    col_name = f"{metric.name}.{k}"
                    agg_all[col_name].append(v)
                    if cam_type == "1x":
                        agg_1x[col_name].append(v)
                    else:
                        agg_uw[col_name].append(v)
                    row[col_name] = round(v, 4)

            all_rows.append(row)

        n_views = len(next(iter(agg_all.values()), []))
        print(f"\n=== MODELO: {model_name.upper()} ({n_views} vistas) ===")
        print(
            f"{'Métrica (↑ maior melhor | ↓ menor melhor)':<42} | {'GERAL':>8} | {'Câm 1x':>8} | {'Câm UW':>8}"
        )
        print("-" * 76)
        for col_name, vals in agg_all.items():
            display_name = labels_map.get(col_name, col_name)
            m_all = float(np.mean(vals))
            m_1x = float(np.mean(agg_1x[col_name])) if agg_1x[col_name] else 0.0
            m_uw = float(np.mean(agg_uw[col_name])) if agg_uw[col_name] else 0.0
            print(
                f"{display_name:<42} | {m_all:>8.2f} | {m_1x:>8.2f} | {m_uw:>8.2f}"
            )

    if legend_entries:
        print("\n=== LEGENDA DAS MÉTRICAS ===")
        for label, desc in legend_entries:
            print(f"• {label:<32} -> {desc}")

    if all_rows:
        csv_out.parent.mkdir(parents=True, exist_ok=True)
        fieldnames = list(all_rows[0].keys())
        with csv_out.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_rows)


if __name__ == "__main__":
    registry = discover_metrics()
    base_dir = Path(__file__).resolve().parent

    parser = argparse.ArgumentParser(
        description="Orquestrador Modular de Métricas 3D -> 2D."
    )
    parser.add_argument(
        "--real-dir", type=Path, required=True, help="Pasta com as fotos originais."
    )
    parser.add_argument(
        "--proj-root",
        type=Path,
        default=None,
        help="Pasta raiz das projeções (projection_ruim, projection_medio, projection_bom).",
    )
    parser.add_argument(
        "--generate-gt",
        action="store_true",
        help="Gera as máscaras Ground Truth a partir de --real-dir antes de avaliar.",
    )
    parser.add_argument("--gt-masks", type=Path, default=base_dir / "sam_gt" / "masks")
    parser.add_argument(
        "--weights",
        type=Path,
        default=base_dir / "runs" / "caixa_model" / "weights" / "best.pt",
    )
    parser.add_argument("--sam-model", type=str, default="sam2.1_b.pt")
    parser.add_argument(
        "--csv-out", type=Path, default=base_dir / "results_metrics.csv"
    )
    parser.add_argument(
        "--solid-object",
        action="store_true",
        help="Desativa busca por buracos internos (ideal para objetos maciços).",
    )
    parser.add_argument(
        "--only", nargs="+", choices=list(registry.keys()), default=None
    )
    args = parser.parse_args()

    extractor = MaskExtractor(
        yolo_weights_path=args.weights.resolve(), sam_weights=args.sam_model
    )

    if args.generate_gt:
        extractor.generate_ground_truth(
            real_dir=args.real_dir.resolve(),
            out_masks_dir=args.gt_masks.resolve(),
            imread_fn=imread_quiet,
        )

    if args.proj_root is not None:
        selected_names = args.only if args.only else list(registry.keys())
        selected_instances = [registry[name]() for name in selected_names]

        proj_root = args.proj_root.resolve()
        models = {
            "ruim": proj_root / "projection_ruim",
            "medio": proj_root / "projection_medio",
            "bom": proj_root / "projection_bom",
        }

        run_benchmark(
            real_dir=args.real_dir.resolve(),
            gt_masks_dir=args.gt_masks.resolve(),
            models_map=models,
            selected_metrics=selected_instances,
            extractor=extractor,
            csv_out=args.csv_out.resolve(),
            solid_object=args.solid_object,
        )