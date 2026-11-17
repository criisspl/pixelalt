"""Reglas de auditoría de accesibilidad para el texto alt."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum

from pixelalt.scraper import Imagen


class Tipo(StrEnum):
    SIN_ALT = "sin-alt"
    ALT_VACIO = "alt-vacio"
    ALT_GENERICO = "alt-generico"


@dataclass(frozen=True)
class Hallazgo:
    tipo: Tipo
    imagen: Imagen


MENSAJES = {
    Tipo.SIN_ALT: "Falta el atributo alt",
    Tipo.ALT_VACIO: "alt vacío en una imagen que no es decorativa",
    Tipo.ALT_GENERICO: "alt genérico que no describe la imagen",
}

_GENERICOS = {
    "image", "img", "imagen", "foto", "fotografia", "fotografía", "photo", "picture",
    "pic", "grafico", "gráfico", "icon", "icono", "logo", "banner", "untitled",
    "sin titulo", "sin título", "placeholder",
}  # fmt: skip
_NOMBRE_FICHERO = re.compile(r"^[\w\-. ]+\.(jpe?g|png|gif|webp|svg|avif|bmp)$", re.IGNORECASE)
_GENERICO_NUMERADO = re.compile(
    r"^(image|img|imagen|foto|photo|picture)[\s_\-]*\d*$", re.IGNORECASE
)


def es_generico(alt: str) -> bool:
    texto = alt.strip().lower()
    return (
        texto in _GENERICOS
        or bool(_NOMBRE_FICHERO.match(texto))
        or bool(_GENERICO_NUMERADO.match(texto))
    )


def auditar(imagenes: list[Imagen]) -> list[Hallazgo]:
    hallazgos: list[Hallazgo] = []
    for imagen in imagenes:
        if imagen.alt is None:
            hallazgos.append(Hallazgo(Tipo.SIN_ALT, imagen))
        elif imagen.alt.strip() == "":
            if not imagen.decorativa:
                hallazgos.append(Hallazgo(Tipo.ALT_VACIO, imagen))
        elif es_generico(imagen.alt):
            hallazgos.append(Hallazgo(Tipo.ALT_GENERICO, imagen))
    return hallazgos
