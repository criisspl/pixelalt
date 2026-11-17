"""Descarga de páginas e imágenes y extracción de etiquetas <img>."""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup


@dataclass(frozen=True)
class Imagen:
    """Imagen encontrada en una página."""

    url: str
    alt: str | None  # None = atributo ausente
    decorativa: bool = False  # role=presentation/none o aria-hidden


def descargar_html(url: str, cliente: httpx.Client) -> str:
    respuesta = cliente.get(url, follow_redirects=True)
    respuesta.raise_for_status()
    return respuesta.text


def extraer_imagenes(html: str, url_base: str) -> list[Imagen]:
    """Devuelve las imágenes únicas del HTML con URL absoluta."""
    sopa = BeautifulSoup(html, "html.parser")
    vistas: set[str] = set()
    imagenes: list[Imagen] = []
    for etiqueta in sopa.find_all("img"):
        src = etiqueta.get("src")
        if not src or str(src).startswith("data:"):
            continue
        url = urljoin(url_base, str(src))
        if url in vistas:
            continue
        vistas.add(url)
        alt = etiqueta.get("alt")
        decorativa = (
            str(etiqueta.get("role", "")).lower() in {"presentation", "none"}
            or str(etiqueta.get("aria-hidden", "")).lower() == "true"
        )
        imagenes.append(
            Imagen(url=url, alt=None if alt is None else str(alt), decorativa=decorativa)
        )
    return imagenes


def descargar_imagen(url: str, cliente: httpx.Client) -> tuple[bytes, str]:
    """Descarga una imagen y devuelve (bytes, tipo MIME)."""
    respuesta = cliente.get(url, follow_redirects=True)
    respuesta.raise_for_status()
    tipo = respuesta.headers.get("content-type", "image/jpeg").split(";")[0].strip()
    return respuesta.content, tipo
