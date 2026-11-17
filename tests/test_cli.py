import httpx
from typer.testing import CliRunner

from pixelalt import cli
from pixelalt.proveedores import ProveedorFalso, ProveedorOllama

HTML = '<img src="/a.png" alt="Gato en un sofá"><img src="/b.png"><img src="/c.png" alt="foto">'


def manejador(request: httpx.Request) -> httpx.Response:
    if request.url.path == "/":
        return httpx.Response(200, text=HTML)
    return httpx.Response(200, content=b"png", headers={"content-type": "image/png"})


def parchear(monkeypatch):
    monkeypatch.setattr(
        cli, "crear_cliente", lambda: httpx.Client(transport=httpx.MockTransport(manejador))
    )
    monkeypatch.setattr(
        cli, "crear_proveedor", lambda nombre, modelo=None: ProveedorFalso("Alt falso")
    )


def test_auditar_detecta_problemas(monkeypatch):
    parchear(monkeypatch)
    r = CliRunner().invoke(cli.app, ["auditar", "https://ejemplo.test/"])
    assert r.exit_code == 1
    assert "3 imágenes, 2 con problemas" in r.output


def test_auditar_con_sugerencias(monkeypatch):
    parchear(monkeypatch)
    r = CliRunner().invoke(
        cli.app, ["auditar", "https://ejemplo.test/", "--sugerir", "-p", "falso"]
    )
    assert "Alt falso" in r.output


def test_generar(monkeypatch):
    parchear(monkeypatch)
    r = CliRunner().invoke(cli.app, ["generar", "https://ejemplo.test/", "-p", "falso"])
    assert r.exit_code == 0
    assert "Alt falso" in r.output


def test_ollama_usa_api_generate():
    visto = {}

    def h(request: httpx.Request) -> httpx.Response:
        visto["path"] = request.url.path
        return httpx.Response(200, json={"response": " Un gato "})

    prov = ProveedorOllama(cliente=httpx.Client(transport=httpx.MockTransport(h)))
    assert prov.describir(b"x", "image/png") == "Un gato"
    assert visto["path"] == "/api/generate"
