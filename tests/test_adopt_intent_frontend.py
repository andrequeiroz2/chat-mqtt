"""Espelha regras de services/frontend/src/chat/adopt/intent.ts (via documentação)."""

from __future__ import annotations

import re

PRODUCT_TELEMETRY_CONTEXT = re.compile(
    r"\b(gr[aá]fico|historico|hist[oó]rico|telemetria|temperatura|umidade|leitura|"
    r"ultim[oa]s?\s+(dia|dias|semana))\b",
    re.I,
)
ADOPT_INTENT = re.compile(
    r"\b(adotar|adote|adota|instalar|instale|instala|parear|pareie)\b",
    re.I,
)


def is_adoption_intent(text: str) -> bool:
    trimmed = text.strip()
    if not trimmed:
        return False
    if PRODUCT_TELEMETRY_CONTEXT.search(trimmed):
        return bool(ADOPT_INTENT.search(trimmed))
    return bool(ADOPT_INTENT.search(trimmed))


def test_chart_with_registros_not_adoption() -> None:
    msg = "mostra um gráfico da temperatura do último dia em que existem registros"
    assert not is_adoption_intent(msg)


def test_install_sensor_still_adoption() -> None:
    assert is_adoption_intent("comprei um sensor e quero instalar")
