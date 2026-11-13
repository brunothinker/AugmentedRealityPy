"""Registro dinâmico (Registry) das estratégias de avaliação em ``metrics/``."""

import importlib
import inspect
import pkgutil
from pathlib import Path

from .base import BaseMetric, EvaluationContext

METRIC_REGISTRY: dict[str, type[BaseMetric]] = {}


def discover_metrics() -> dict[str, type[BaseMetric]]:
    """Descobre e registra automaticamente todas as subclasses de ``BaseMetric``.

    Varre todos os módulos terminados em ``_metric.py`` dentro deste pacote
    e indexa suas classes pelo atributo ``name``.

    Returns:
        Dicionário ``{nome_estrategia: ClasseMetrica}``.
    """
    if METRIC_REGISTRY:
        return METRIC_REGISTRY

    pkg_dir = Path(__file__).resolve().parent
    for _, module_name, _ in pkgutil.iter_modules([str(pkg_dir)]):
        if not module_name.endswith("_metric"):
            continue
        module = importlib.import_module(f"{__package__}.{module_name}")
        for _, obj in inspect.getmembers(module, inspect.isclass):
            if issubclass(obj, BaseMetric) and obj is not BaseMetric:
                METRIC_REGISTRY[obj.name] = obj

    return METRIC_REGISTRY


__all__ = ["METRIC_REGISTRY", "BaseMetric", "EvaluationContext", "discover_metrics"]