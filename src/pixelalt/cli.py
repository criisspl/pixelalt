"""CLI de pixelalt."""

from __future__ import annotations

from typing import Annotated

import httpx
import typer
from rich.console import Console
from rich.table import Table

from pixelalt.auditoria import MENSAJES, Hallazgo, auditar
from pixelalt.proveedores import ErrorProveedor, ProveedorVision, crear_proveedor
from pixelalt.scraper import Imagen, descargar_html, descargar_imagen, extraer_imagenes

app = typer.Typer(help="Genera texto alt y audita la accesibilidad de las imágenes de una web.")
consola = Console()

ProveedorOpt = Annotated[
    str, typer.Option("--proveedor", "-p", help="ollama, claude, falso o auto.")
]
ModeloOpt = Annotated[str | None, typer.Option("--modelo", "-m", help="Modelo de visión.")]


def crear_cliente() -> httpx.Client:
    return httpx.Client(timeout=30, headers={"User-Agent": "pixelalt/0.1"})


def _obtener_imagenes(url: str, cliente: httpx.Client) -> list[Imagen]:
    try:
        html = descargar_html(url, cliente)
    except httpx.HTTPError as e:
        consola.print(f"[red]No se pudo descargar {url}: {e}[/red]")
        raise typer.Exit(2) from e
    return extraer_imagenes(html, url)


def _describir(imagen: Imagen, proveedor: ProveedorVision, cliente: httpx.Client) -> str | None:
    try:
        datos, tipo = descargar_imagen(imagen.url, cliente)
        return proveedor.describir(datos, tipo)
    except (httpx.HTTPError, ErrorProveedor) as e:
        consola.print(f"[yellow]Sin descripción para {imagen.url}: {e}[/yellow]")
        return None


def _proveedor(nombre: str, modelo: str | None) -> ProveedorVision:
    try:
        return crear_proveedor(nombre, modelo)
    except ErrorProveedor as e:
        consola.print(f"[red]{e}[/red]")
        raise typer.Exit(2) from e


@app.command()
def generar(url: str, proveedor: ProveedorOpt = "auto", modelo: ModeloOpt = None) -> None:
    """Genera un texto alt para cada imagen de la URL."""
    prov = _proveedor(proveedor, modelo)
    with crear_cliente() as cliente:
        imagenes = _obtener_imagenes(url, cliente)
        tabla = Table("Imagen", "Alt sugerido")
        for imagen in imagenes:
            tabla.add_row(imagen.url, _describir(imagen, prov, cliente) or "—")
    consola.print(tabla)


@app.command("auditar")
def auditar_cmd(
    url: str,
    sugerir: Annotated[
        bool, typer.Option("--sugerir", help="Sugiere alt para las imágenes con problemas.")
    ] = False,
    proveedor: ProveedorOpt = "auto",
    modelo: ModeloOpt = None,
) -> None:
    """Audita las imágenes de la URL. Sale con código 1 si hay problemas."""
    prov = _proveedor(proveedor, modelo) if sugerir else None
    with crear_cliente() as cliente:
        imagenes = _obtener_imagenes(url, cliente)
        hallazgos: list[Hallazgo] = auditar(imagenes)
        tabla = Table("Problema", "Imagen", "Alt sugerido")
        for h in hallazgos:
            sugerido = _describir(h.imagen, prov, cliente) if prov else None
            tabla.add_row(MENSAJES[h.tipo], h.imagen.url, sugerido or "")
    consola.print(f"{len(imagenes)} imágenes, {len(hallazgos)} con problemas.")
    if hallazgos:
        consola.print(tabla)
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
