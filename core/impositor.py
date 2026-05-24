"""
core/impositor.py
Lógica pura de imposición PDF A4 → A5.
Sin dependencias de PyQt6. Testeable de forma independiente.
"""

import math
import os
import shutil
from typing import Callable, Optional

import fitz  # PyMuPDF


# ---------------------------------------------------------------------------
# Jerarquía de excepciones
# ---------------------------------------------------------------------------

class ImpositorError(Exception):
    """Base para todos los errores del impositor."""


class ArchivoInvalidoError(ImpositorError):
    """El archivo no existe, no es un PDF legible o tiene 0 páginas."""


class FormatoNoCorrecto(ImpositorError):
    """Alguna página no tiene dimensiones A4 portrait (±2 mm)."""


class ArchivoProtegidoError(ImpositorError):
    """El PDF está protegido con contraseña."""


class ErrorEscrituraError(ImpositorError):
    """No se puede escribir el archivo de salida."""


class ErrorProcesamientoError(ImpositorError):
    """Error inesperado durante la imposición."""


# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------

# A4 portrait en milímetros (tolerancia ±2 mm)
_A4_W_MM = 210.0
_A4_H_MM = 297.0
_TOL_MM = 2.0

# Puntos PDF por milímetro (1 pt = 1/72 in; 1 in = 25.4 mm)
_MM_PER_PT = 25.4 / 72.0


def _pt_to_mm(pts: float) -> float:
    return pts * _MM_PER_PT


def _mm_to_pt(mm: float) -> float:
    return mm / _MM_PER_PT


# ---------------------------------------------------------------------------
# API pública
# ---------------------------------------------------------------------------

def validar_pdf(ruta: str) -> dict:
    """
    Valida el PDF en *ruta* y devuelve un dict con información:
      {
        "num_paginas": int,
        "paginas_tras_relleno": int,
        "hojas_salida": int,
        "ruta_salida": str,
      }
    Lanza una subclase de ImpositorError si la validación falla.
    """
    # 1. Extensión
    if not ruta.lower().endswith(".pdf"):
        raise ArchivoInvalidoError("El archivo no tiene extensión .pdf.")

    # 2. Legibilidad
    try:
        doc = fitz.open(ruta)
    except Exception:
        raise ArchivoInvalidoError(
            "El archivo no es un PDF válido o está corrupto."
        )

    try:
        # 3. Contraseña
        if doc.needs_pass:
            raise ArchivoProtegidoError(
                "El PDF está protegido con contraseña y no puede procesarse."
            )

        # 4. Páginas vacías
        if doc.page_count == 0:
            raise ArchivoInvalidoError("El PDF no contiene páginas.")

        # 5. Formato y orientación de cada página
        num_paginas = doc.page_count
        for i in range(num_paginas):
            page = doc[i]
            rect = page.rect
            w_mm = _pt_to_mm(rect.width)
            h_mm = _pt_to_mm(rect.height)

            # Orientación apaisada (landscape): alto < ancho
            if h_mm < w_mm:
                raise FormatoNoCorrecto(
                    "El PDF contiene páginas en orientación apaisada. "
                    "Se esperan páginas en vertical (portrait)."
                )

            # Tamaño diferente a A4
            if not (
                abs(w_mm - _A4_W_MM) <= _TOL_MM
                and abs(h_mm - _A4_H_MM) <= _TOL_MM
            ):
                raise FormatoNoCorrecto(
                    f"La página {i + 1} no es A4 "
                    f"(encontrado: {w_mm:.0f} × {h_mm:.0f} mm)."
                )

    finally:
        doc.close()

    # Cálculo de información (num_paginas fue guardado antes de cerrar el doc)
    paginas_tras_relleno = _paginas_con_relleno(num_paginas)
    hojas_salida = paginas_tras_relleno // 2
    ruta_salida = _ruta_salida(ruta)

    return {
        "num_paginas": num_paginas,
        "paginas_tras_relleno": paginas_tras_relleno,
        "hojas_salida": hojas_salida,
        "ruta_salida": ruta_salida,
    }


def imponer(
    ruta: str,
    callback_progreso: Optional[Callable[[int, int], None]] = None,
) -> str:
    """
    Genera el PDF de imposición A5 a partir de *ruta*.
    Devuelve la ruta del archivo generado.
    *callback_progreso(pagina_actual, total_paginas)* se llama con cada página procesada.
    Lanza subclases de ImpositorError ante cualquier problema.
    """
    # --- Validaciones pre-proceso ---
    _validar_pre_proceso(ruta)

    # --- Re-validar el PDF (segunda línea de defensa) ---
    info = validar_pdf(ruta)
    ruta_salida = info["ruta_salida"]

    try:
        src = fitz.open(ruta)
    except Exception as exc:
        raise ErrorProcesamientoError(f"Error al abrir el PDF: {exc}") from exc

    try:
        num_orig = src.page_count
        num_total = info["paginas_tras_relleno"]

        # Dimensiones de la hoja de salida: A4 apaisado en puntos
        # A4 apaisado: 297 mm × 210 mm
        out_w = _mm_to_pt(297.0)
        out_h = _mm_to_pt(210.0)

        # Cada mitad ocupa 148.5 mm de ancho × 210 mm de alto
        half_w = out_w / 2.0

        # Factor de escala A4 portrait → A5: sqrt(0.5) ≈ 0.7071
        scale = math.sqrt(0.5)

        dst = fitz.open()

        # Orden booklet: pág 1 con última, pág 2 con penúltima, etc.
        # Para N páginas totales (0-indexed) la secuencia de pares es:
        #   física 0 (frente hoja 1): [N-1, 0]
        #   física 1 (dorso  hoja 1): [1, N-2]
        #   física 2 (frente hoja 2): [N-3, 2]
        #   física 3 (dorso  hoja 2): [3, N-4]
        #   ...
        N = num_total
        pares = []
        for i in range(N // 2):
            if i % 2 == 0:   # cara A (frente): exterior → izq=última, der=primera
                pares.append((N - 1 - i, i))
            else:            # cara B (dorso):  izq=segunda, der=penúltima
                pares.append((i, N - 1 - i))

        total_fisicas = len(pares)

        for hoja_idx, (izq, der) in enumerate(pares):
            hoja = dst.new_page(width=out_w, height=out_h)

            for slot, pag_idx in enumerate([izq, der]):
                x0 = slot * half_w
                dest_rect = fitz.Rect(x0, 0, x0 + half_w, out_h)

                if pag_idx < num_orig:
                    hoja.show_pdf_page(dest_rect, src, pag_idx)
                # pag_idx >= num_orig → página en blanco (fondo blanco por defecto)

            if callback_progreso is not None:
                callback_progreso(hoja_idx + 1, total_fisicas)

        # Guardar
        try:
            dst.save(ruta_salida, garbage=4, deflate=True)
        except Exception as exc:
            raise ErrorEscrituraError(
                "Error al guardar el archivo. Comprueba que no está abierto en otro programa."
            ) from exc

    except ImpositorError:
        raise
    except Exception as exc:
        raise ErrorProcesamientoError(f"Error al procesar el PDF: {exc}") from exc
    finally:
        src.close()
        try:
            dst.close()
        except Exception:
            pass

    return ruta_salida


# ---------------------------------------------------------------------------
# Funciones auxiliares privadas
# ---------------------------------------------------------------------------

def _paginas_con_relleno(num_paginas: int) -> int:
    """Devuelve el número de páginas redondeado al siguiente múltiplo de 4."""
    resto = num_paginas % 4
    if resto == 0:
        return num_paginas
    return num_paginas + (4 - resto)


def _ruta_salida(ruta: str) -> str:
    """Devuelve la ruta del archivo de salida con sufijo _A5."""
    base, _ = os.path.splitext(ruta)
    return base + "_A5.pdf"


def _validar_pre_proceso(ruta: str) -> None:
    """Validaciones que se ejecutan justo antes de iniciar la imposición."""
    # 1. El archivo sigue disponible
    if not os.path.isfile(ruta):
        raise ArchivoInvalidoError(
            "No se encuentra el archivo original. ¿Ha sido movido o eliminado?"
        )

    # 2. Permisos de escritura en la carpeta de destino
    carpeta = os.path.dirname(os.path.abspath(ruta))
    if not os.access(carpeta, os.W_OK):
        raise ErrorEscrituraError(
            "Sin permisos de escritura en la carpeta de destino."
        )

    # 3. Archivo de salida bloqueado
    ruta_out = _ruta_salida(ruta)
    if os.path.isfile(ruta_out):
        try:
            with open(ruta_out, "a"):
                pass
        except OSError:
            raise ErrorEscrituraError(
                "El archivo de salida está abierto en otro programa. "
                "Ciérralo e inténtalo de nuevo."
            )

    # 4. Espacio en disco (heurística: 3× el tamaño del original)
    tam_original = os.path.getsize(ruta)
    espacio_necesario = tam_original * 3
    espacio_disponible = shutil.disk_usage(carpeta).free
    if espacio_disponible < espacio_necesario:
        raise ErrorEscrituraError(
            "Espacio en disco insuficiente para generar el archivo."
        )
