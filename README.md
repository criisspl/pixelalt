# pixelalt

CLI en Python que, dada una URL, descarga las imágenes de la página, **audita su accesibilidad**
(sin `alt`, `alt` vacío indebido, `alt` genérico) y **genera texto alt** con un modelo de visión
local vía [Ollama](https://ollama.com) (`moondream` o `llava`). Claude es un proveedor opcional si
tienes API key. No hay dependencias de pago obligatorias.

## Instalación

Requiere Python 3.11+ y [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/criisspl/pixelalt.git
cd pixelalt
uv sync
```

Para generar descripciones con un modelo local:

```bash
ollama pull moondream   # o llava
```

## Uso

```bash
# Auditar (código de salida 1 si hay problemas)
uv run pixelalt auditar https://criisspl.github.io/portfolio/

# Auditar y sugerir alt para las imágenes con problemas
uv run pixelalt auditar https://criisspl.github.io/portfolio/ --sugerir

# Generar alt para todas las imágenes
uv run pixelalt generar https://criisspl.github.io/portfolio/ -p ollama -m llava
```

Opciones comunes:

| Opción | Descripción |
| --- | --- |
| `-p, --proveedor` | `ollama`, `claude`, `falso` o `auto` (por defecto: Claude si existe `ANTHROPIC_API_KEY`, si no Ollama) |
| `-m, --modelo` | Modelo de visión (por defecto `moondream` en Ollama, `claude-haiku-5-5` en Claude) |

Variables de entorno: `OLLAMA_HOST` (por defecto `http://localhost:11434`) y `ANTHROPIC_API_KEY`
(solo para Claude; nunca la guardes en ficheros del repo).

## Reglas de auditoría

- **sin-alt**: la imagen no tiene atributo `alt`.
- **alt-vacio**: `alt=""` en una imagen que no es decorativa (sin `role="presentation"`, `role="none"` ni `aria-hidden="true"`).
- **alt-generico**: `imagen`, `foto`, `logo`, `IMG_2041.jpg`, etc.

## Desarrollo

```bash
uv run ruff check
uv run ruff format --check
uv run pytest      # usa un proveedor falso: sin red ni Ollama
```

Ramas `feature/<nombre>`, Conventional Commits y una PR por cambio.
