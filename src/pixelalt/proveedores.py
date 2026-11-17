"""Proveedores de visión: Ollama (local), Claude (opcional) y uno falso para tests."""

from __future__ import annotations

import base64
import os
from typing import Protocol

import httpx

PROMPT = (
    "Describe esta imagen en español para usarla como texto alt de accesibilidad. "
    "Una sola frase breve (máximo 125 caracteres), sin empezar por 'imagen de'."
)


class ErrorProveedor(RuntimeError):
    """Fallo al obtener la descripción de un proveedor."""


class ProveedorVision(Protocol):
    nombre: str

    def describir(self, imagen: bytes, tipo_mime: str) -> str: ...


class ProveedorOllama:
    nombre = "ollama"

    def __init__(
        self,
        modelo: str = "moondream",
        host: str = "http://localhost:11434",
        cliente: httpx.Client | None = None,
    ) -> None:
        self.modelo = modelo
        self.host = host.rstrip("/")
        self.cliente = cliente or httpx.Client(timeout=120)

    def describir(self, imagen: bytes, tipo_mime: str) -> str:
        try:
            r = self.cliente.post(
                f"{self.host}/api/generate",
                json={
                    "model": self.modelo,
                    "prompt": PROMPT,
                    "images": [base64.b64encode(imagen).decode()],
                    "stream": False,
                },
            )
            r.raise_for_status()
        except httpx.HTTPError as e:
            raise ErrorProveedor(f"Ollama no responde en {self.host}: {e}") from e
        return str(r.json().get("response", "")).strip()


class ProveedorClaude:
    nombre = "claude"

    def __init__(
        self,
        api_key: str,
        modelo: str = "claude-haiku-5-5",
        cliente: httpx.Client | None = None,
    ) -> None:
        self.api_key = api_key
        self.modelo = modelo
        self.cliente = cliente or httpx.Client(timeout=60)

    def describir(self, imagen: bytes, tipo_mime: str) -> str:
        try:
            r = self.cliente.post(
                "https://api.anthropic.com/v1/messages",
                headers={"x-api-key": self.api_key, "anthropic-version": "2023-06-01"},
                json={
                    "model": self.modelo,
                    "max_tokens": 200,
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "image",
                                    "source": {
                                        "type": "base64",
                                        "media_type": tipo_mime,
                                        "data": base64.b64encode(imagen).decode(),
                                    },
                                },
                                {"type": "text", "text": PROMPT},
                            ],
                        }
                    ],
                },
            )
            r.raise_for_status()
        except httpx.HTTPError as e:
            raise ErrorProveedor(f"Error al llamar a la API de Claude: {e}") from e
        return "".join(b.get("text", "") for b in r.json().get("content", [])).strip()


class ProveedorFalso:
    """Devuelve un texto fijo; para tests y pruebas sin modelo."""

    nombre = "falso"

    def __init__(self, texto: str = "Descripción de prueba") -> None:
        self.texto = texto

    def describir(self, imagen: bytes, tipo_mime: str) -> str:
        return self.texto


def crear_proveedor(nombre: str, modelo: str | None = None) -> ProveedorVision:
    """`auto` usa Claude si hay ANTHROPIC_API_KEY y Ollama en otro caso."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if nombre == "auto":
        nombre = "claude" if api_key else "ollama"
    if nombre == "claude":
        if not api_key:
            raise ErrorProveedor("Falta ANTHROPIC_API_KEY para usar Claude.")
        return ProveedorClaude(api_key, modelo or "claude-haiku-5-5")
    if nombre == "ollama":
        return ProveedorOllama(
            modelo or "moondream", os.environ.get("OLLAMA_HOST", "http://localhost:11434")
        )
    if nombre == "falso":
        return ProveedorFalso()
    raise ErrorProveedor(f"Proveedor desconocido: {nombre}")
