from pixelalt.scraper import extraer_imagenes

HTML = """
<img src="/a.png" alt="Uno">
<img src="b.png">
<img src="/a.png" alt="Duplicada">
<img src="data:image/png;base64,AAAA" alt="inline">
<img src="https://cdn.test/c.png" alt="" role="presentation">
<img alt="sin src">
"""


def test_extrae_urls_absolutas_sin_duplicados_ni_data():
    imagenes = extraer_imagenes(HTML, "https://ejemplo.test/dir/")
    assert [i.url for i in imagenes] == [
        "https://ejemplo.test/a.png",
        "https://ejemplo.test/dir/b.png",
        "https://cdn.test/c.png",
    ]


def test_alt_y_decorativa():
    a, b, c = extraer_imagenes(HTML, "https://ejemplo.test/dir/")
    assert a.alt == "Uno"
    assert b.alt is None
    assert c.alt == "" and c.decorativa
