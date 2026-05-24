# Spec: Impositor PDF A5 — `impositor-a5`

## Resumen

Aplicación de escritorio Windows 11 para imponer un PDF en formato A4 como booklet A5 listo para impresión a doble cara y encuadernación en gusanillo. Genera un nuevo PDF con dos páginas A5 (escaladas al 71%) por hoja A4 apaisada, en orden "saddle-stitch" (gusanillo): primera con última, segunda con penúltima, y así sucesivamente para que el documento quede correcto al doblar y encuadernar.

---

## Stack tecnológico

| Componente | Tecnología |
|---|---|
| Lenguaje | Python 3.12 |
| UI | PyQt6 |
| Manipulación PDF | PyMuPDF (`fitz`) |
| Empaquetado | PyInstaller (modo `--onefile`, portable, sin instalador) |
| Target OS | Windows 11 (64 bits) |

### Dependencias principales
```
PyQt6>=6.7
PyMuPDF>=1.24
pyinstaller>=6.0
```

---

## Lógica de imposición

### Concepto
Cada hoja A4 apaisada del PDF resultante contiene **dos páginas del original escaladas al 71%** (A4 → A5), colocadas lado a lado. El orden de imposición será **saddle-stitch (gusanillo)** — es decir, las páginas se emparejan para que al doblar y encuadernar queden en orden de lectura:

- Primera con última
- Segunda con penúltima
- Tercera con antepenúltima
- ...

Ejemplo (8 páginas originales):

```
Hoja 1 — Cara A (frente):   [pág. 8] [pág. 1]
Hoja 1 — Cara B (dorso):    [pág. 2] [pág. 7]
Hoja 2 — Cara A (frente):   [pág. 6] [pág. 3]
Hoja 2 — Cara B (dorso):    [pág. 4] [pág. 5]
```

El PDF resultante está listo para **impresión dúplex en borde largo** (flip on long edge). Al imprimir y doblar las hojas en el centro, las páginas quedarán en la secuencia correcta para lectura y encuadernación en gusanillo.

### Escala y dimensiones
- A4: 210 × 297 mm → A5: 148 × 210 mm
- Factor de escala lineal: **70.7% ≈ 71%**
- Hoja de salida: A4 apaisada → 297 × 210 mm
- Cada página ocupa exactamente la mitad de la hoja de salida: 148.5 × 210 mm
- No hay margen interior entre páginas (corte limpio para gusanillo)

### Relleno de páginas
Si el número de páginas del PDF original **no es múltiplo de 4**, se añaden páginas en blanco al final automáticamente hasta completar el múltiplo. No se pregunta al usuario; se hace de forma transparente y se indica en el log de la UI.

### Orientación de páginas pares (dorso)
Para que el dorso quede correctamente orientado al dar la vuelta la hoja en borde largo, **las páginas de las caras B no se rotan** — la disposición izquierda/derecha se mantiene igual. El usuario imprimirá con la opción "voltear en borde largo" de su impresora.

---

## Nomenclatura del archivo de salida

```
{nombre_original}_A5.pdf
```

Se guarda en **la misma carpeta que el archivo original**.

Ejemplo: `informe_anual.pdf` → `informe_anual_A5.pdf`

Si el archivo de salida ya existe, se **sobreescribe sin aviso** (la operación es idempotente y el nombre es determinista).

---

## Interfaz de usuario

### Ventana principal
- **Título:** `Impositor A5`
- **Tamaño fijo:** 480 × 380 px (no redimensionable)
- **Tema:** Sistema (respeta el modo claro/oscuro de Windows)
- **Idioma:** Español
- **Barra de menú:** contiene las entradas `Ayuda` y `Acerca de`

### Elementos de la UI (de arriba a abajo)

#### 1. Área de selección de archivo
```
[ Campo de texto (ruta del PDF, solo lectura) ] [ Examinar... ]
```
- El campo muestra la ruta completa del archivo seleccionado.
- El botón `Examinar...` abre un `QFileDialog` filtrado a `*.pdf`.
- También se acepta **arrastrar y soltar** un archivo PDF directamente sobre la ventana.

#### 2. Panel de información (visible tras seleccionar archivo)
Texto informativo en gris, actualizando dinámicamente:
```
Páginas en el original:     12
Páginas tras relleno:       12   (múltiplo de 4 ✓)
Hojas de salida:            6
Archivo de salida:          /ruta/al/archivo_A5.pdf
```
Si se añaden páginas en blanco:
```
Páginas en el original:     10
Páginas tras relleno:       12   (+2 páginas en blanco añadidas)
Hojas de salida:            6
Archivo de salida:          /ruta/al/archivo_A5.pdf
```

#### 3. Botón de acción
```
[ Procesar PDF ]
```
- Deshabilitado hasta que haya un archivo seleccionado.
- Durante el procesado: deshabilitado, texto cambia a `Procesando…`

#### 4. Barra de progreso
- Oculta por defecto.
- Visible durante el procesado, valor determinista (avanza página a página).

#### 5. Área de estado / log
Línea de texto en la parte inferior. Estados posibles:

| Situación | Mensaje |
|---|---|
| Inicial | *(vacío)* |
| Archivo seleccionado y válido | `Archivo cargado correctamente.` |
| Archivo inválido (no PDF, corrupto…) | `⚠ El archivo no es un PDF válido o está corrupto.` |
| Páginas no son A4 | `⚠ La página {N} no es A4 (encontrado: {W} × {H} mm).` |
| Páginas en apaisado | `⚠ El PDF contiene páginas en orientación apaisada.` |
| PDF protegido | `⚠ El PDF está protegido con contraseña.` |
| Procesando | `Procesando página X de Y…` |
| Completado | `✓ PDF generado: informe_anual_A5.pdf` |
| Error de escritura | `✗ Error al guardar el archivo. Comprueba que no está abierto en otro programa.` |
| Error inesperado | `✗ Error inesperado: {mensaje}` |

#### 6. Barra de menú

Situada en la parte superior de la ventana, con dos entradas:

**`Ayuda` → Cómo usar esta aplicación**
Abre un `QDialog` modal, no redimensionable, con el siguiente contenido:

---
**Cómo usar Impositor A5**

Impositor A5 convierte un PDF en formato A4 vertical en un documento listo para imprimir como cuadernillo A5 encuadernado en gusanillo.

**Pasos:**

1. Selecciona un archivo PDF pulsando **Examinar…** o arrástralo directamente sobre la ventana.
2. Comprueba la información del documento (páginas, hojas de salida, archivo generado).
3. Pulsa **Procesar PDF**. El archivo resultante se guardará automáticamente en la misma carpeta que el original, con el sufijo `_A5`.

**Requisitos del PDF de entrada:**
- Todas las páginas deben ser tamaño A4 (210 × 297 mm) en orientación vertical.
- El PDF no debe estar protegido con contraseña.
- Si el número de páginas no es múltiplo de 4, se añadirán páginas en blanco al final de forma automática.

**Cómo imprimir:**
- Imprime el PDF resultante en **doble cara**, con la opción **"voltear en borde largo"** activada en tu impresora.
- Imprime a tamaño real (100%), sin ajuste de escala.
- Cada hoja impresa contiene dos páginas A5. Tras imprimir, corta o dobla las hojas y encuadernarlas en el orden en que salen.

---

**`Acerca de` → Información de la aplicación**
Abre un `QDialog` modal con el siguiente contenido:

---
**Impositor A5** — versión 1.0.0

Herramienta de imposición tipográfica para cuadernillos A5 encuadernados en gusanillo.

© 2025 Kimo. Todos los derechos reservados.

Desarrollado con Python, PyMuPDF y PyQt6.
PyMuPDF está sujeto a la licencia GNU AGPL 3.0.
PyQt6 está sujeto a la licencia GNU GPL 3.0.

---

> **Nota de implementación:** el número de versión (`1.0.0`) se define como constante en `main.py` y se reutiliza en el diálogo Acerca de y en el título del ejecutable generado por PyInstaller.

---

## Flujo de usuario

```
1. El usuario abre la app (impositor-a5.exe)
2. Selecciona un PDF (botón Examinar o drag & drop)
   → La UI muestra la información del documento
3. Pulsa "Procesar PDF"
   → La barra de progreso aparece y avanza
   → El botón queda deshabilitado
4. Al terminar:
   → Mensaje de confirmación con el nombre del archivo generado
   → Botón vuelve a estar habilitado
   → El usuario puede procesar otro archivo
```

---

## Comportamiento del ejecutable

- **Portable:** un único `.exe` sin dependencias externas ni instalador.
- **Sin consola:** compilado con `--windowed` (no aparece ventana de terminal).
- **Icono:** se define un icono `.ico` en el empaquetado (a proveer).
- **Arranque:** doble clic directo desde cualquier carpeta, incluido USB.
- **Sin configuración:** no escribe nada en el registro de Windows ni en `AppData`.

---

## Estructura del proyecto (desarrollo)

```
impositor-a5/
├── main.py               # Entry point, instancia QApplication
├── ui/
│   └── main_window.py    # Clase MainWindow (PyQt6)
├── core/
│   └── impositor.py      # Lógica de imposición (pura, sin UI)
├── assets/
│   └── icon.ico          # Icono de la aplicación
├── requirements.txt
├── impositor-a5.spec     # Spec de PyInstaller (generado)
└── spec.md               # Este documento
```

### Separación de responsabilidades
- `core/impositor.py` no importa nada de PyQt6. Recibe una ruta, devuelve la ruta de salida o lanza una excepción. Es testeable de forma independiente.
- `ui/main_window.py` llama a `core/impositor.py` en un **QThread** separado para no bloquear la UI durante el procesado.

---

## Validación defensiva

Toda validación ocurre en `core/impositor.py` y se propaga a la UI como excepción tipada. La UI nunca asume que un archivo es válido hasta que el validador lo confirme.

### Validaciones al seleccionar archivo (antes de procesar)

Se ejecutan en el momento en que el usuario selecciona o suelta un archivo, antes de mostrar el panel de información.

| Check | Condición de error | Mensaje en UI |
|---|---|---|
| Extensión | El archivo no termina en `.pdf` | `⚠ El archivo no tiene extensión .pdf.` |
| Legibilidad | No se puede abrir con PyMuPDF | `⚠ El archivo no es un PDF válido o está corrupto.` |
| Contraseña | El PDF requiere contraseña para abrirse | `⚠ El PDF está protegido con contraseña y no puede procesarse.` |
| Páginas vacías | El PDF tiene 0 páginas | `⚠ El PDF no contiene páginas.` |
| Formato de página | Al menos una página no tiene dimensiones A4 (tolerancia ±2 mm) | `⚠ El PDF contiene páginas que no son A4. Todas las páginas deben ser 210 × 297 mm.` |
| Orientación | Al menos una página está en apaisado (A4 landscape) | `⚠ El PDF contiene páginas en orientación apaisada. Se esperan páginas en vertical (portrait).` |

> **Tolerancia de tamaño:** Se acepta un margen de ±2 mm en cada dimensión para absorber variaciones de exportación (e.g. 209.9 × 296.8 mm se considera A4 válido).

> **Comprobación de formato:** Se verifica **cada página** individualmente. Si una sola página no cumple, se rechaza el documento completo con indicación del número de página problemática cuando sea posible: `⚠ La página 3 no es A4 (encontrado: 148 × 210 mm).`

### Validaciones al procesar

Se ejecutan al pulsar "Procesar PDF", como segunda línea de defensa.

| Check | Condición de error | Mensaje en UI |
|---|---|---|
| Archivo sigue disponible | El archivo fue movido o eliminado tras seleccionarlo | `✗ No se encuentra el archivo original. ¿Ha sido movido o eliminado?` |
| Permisos de escritura | No se puede escribir en la carpeta de destino | `✗ Sin permisos de escritura en la carpeta de destino.` |
| Archivo de salida bloqueado | El `_A5.pdf` existe y está abierto en otro proceso | `✗ El archivo de salida está abierto en otro programa. Ciérralo e inténtalo de nuevo.` |
| Espacio en disco | Espacio disponible < tamaño estimado del output (×3 del original como heurística) | `✗ Espacio en disco insuficiente para generar el archivo.` |
| Error durante imposición | Excepción inesperada de PyMuPDF | `✗ Error al procesar el PDF: {mensaje de excepción}.` |

### Jerarquía de excepciones en `core/impositor.py`

```python
class ImpositorError(Exception): pass          # Base
class ArchivoInvalidoError(ImpositorError): pass
class FormatoNoCorrecto(ImpositorError): pass   # No es A4, orientación incorrecta, etc.
class ArchivoProtegidoError(ImpositorError): pass
class ErrorEscrituraError(ImpositorError): pass
class ErrorProcesamientoError(ImpositorError): pass
```

La UI captura cada tipo y muestra el mensaje apropiado. Los errores inesperados (excepción base `Exception`) se muestran con su mensaje crudo precedido de `✗ Error inesperado:`.

---

## Casos límite

| Caso | Comportamiento |
|---|---|
| PDF de 1 página A4 | Validación pasa; se rellena a 4 páginas con 3 en blanco |
| PDF con mezcla de tamaños | Rechazado en validación; mensaje indica la primera página problemática |
| PDF en A5, A3 u otro formato | Rechazado en validación con dimensiones encontradas |
| PDF apaisado (landscape) | Rechazado en validación con indicación de orientación |
| PDF protegido con contraseña | Rechazado en validación |
| PDF corrupto o truncado | Rechazado en validación |
| Ruta de salida sin permisos | Error en fase de procesado |
| Archivo de salida abierto en otro programa | Error en fase de procesado con instrucción de cierre |
| Espacio en disco insuficiente | Error en fase de procesado antes de iniciar la escritura |

---

## Fuera de alcance (v1)

- Preview de la imposición
- Selección de rango de páginas
- Configuración de márgenes o sangrado
- Soporte de otros tamaños (A3→A4, etc.)
- macOS / Linux
- Múltiples archivos en lote (batch)
- Metadatos del PDF de salida (título, autor, etc.)
