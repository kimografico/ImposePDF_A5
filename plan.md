# Plan de desarrollo — Impositor A5

## Objetivo

Aplicación de escritorio portable (Windows 11) que convierte un PDF A4 en un PDF de imposición A5 listo para impresión a doble cara y encuadernación en gusanillo.

---

## Arquitectura elegida

```
main.py                 ← Entry point (QApplication + MainWindow)
ui/main_window.py       ← Toda la interfaz PyQt6
core/impositor.py       ← Lógica pura de imposición (sin UI)
assets/icon.ico         ← Icono de la aplicación
requirements.txt        ← Dependencias
impositor-a5.spec       ← Spec de PyInstaller (generado al empaquetar)
```

## Principios de diseño

- **Separación de responsabilidades**: `core/` nunca importa PyQt6. Sólo opera con rutas y ficheros.
- **Procesado en hilo separado**: la imposición ocurre en un `QThread` para que la UI nunca se bloquee.
- **Sin configuración persistente**: la app no toca el registro ni AppData; todo es portátil.
- **Validación defensiva**: primero se valida al seleccionar el archivo; luego al procesar.

---

## Módulos y responsabilidades

### `core/impositor.py`

- Jerarquía de excepciones propias (`ImpositorError`, subclases)
- `validar_pdf(ruta)` → lanza excepción o devuelve info del PDF
- `imponer(ruta, callback_progreso)` → genera `*_A5.pdf`, devuelve ruta de salida

### `ui/main_window.py`

- `MainWindow(QMainWindow)`: ventana principal 480×380, no redimensionable
- Zona de selección + drag & drop
- Panel de información dinámica
- Botón Procesar + barra de progreso + área de log
- `ImpositorWorker(QThread)`: ejecuta `imponer()` en background y emite señales de progreso/fin/error
- Diálogos: Ayuda y Acerca de

### `main.py`

- Define `APP_VERSION = "1.0.0"`
- Instancia `QApplication` y `MainWindow`, arranca el loop de eventos

---

## Flujo de datos

```
Usuario selecciona PDF
  → validar_pdf() → muestra info o error en UI
Usuario pulsa Procesar
  → ImpositorWorker.start()
    → imponer() → emite progreso
  → señal progreso → actualiza barra
  → señal finish   → mensaje OK + ruta output
  → señal error    → mensaje de error tipado
```

---

## Empaquetado

```
pyinstaller --onefile --windowed --icon=assets/icon.ico \
            --name=impositor-a5 main.py
```

Output: `dist/impositor-a5.exe` (portable, sin instalador)
