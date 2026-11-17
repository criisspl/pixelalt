import pytest

from pixelalt.auditoria import Tipo, auditar, es_generico
from pixelalt.scraper import Imagen


def img(alt, decorativa=False):
    return Imagen(url="https://x.test/a.png", alt=alt, decorativa=decorativa)


def test_sin_alt():
    assert [h.tipo for h in auditar([img(None)])] == [Tipo.SIN_ALT]


def test_alt_vacio_indebido():
    assert [h.tipo for h in auditar([img("  ")])] == [Tipo.ALT_VACIO]


def test_alt_vacio_decorativa_es_valido():
    assert auditar([img("", decorativa=True)]) == []


@pytest.mark.parametrize("alt", ["imagen", "Foto 3", "IMG_2041.jpg", "logo", "image"])
def test_alt_generico(alt):
    assert es_generico(alt)
    assert [h.tipo for h in auditar([img(alt)])] == [Tipo.ALT_GENERICO]


def test_alt_correcto():
    assert auditar([img("Gato durmiendo sobre un sofá azul")]) == []
