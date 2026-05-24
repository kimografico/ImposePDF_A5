# Task list — Impositor A5

Estado: `[ ]` pendiente · `[x]` completado · `[-]` en curso

---

## Fase 1 — Infraestructura

- [x] Crear estructura de carpetas (`core/`, `ui/`, `assets/`)
- [x] Crear `requirements.txt`
- [x] Crear `__init__.py` en `core/` y `ui/` (paquetes Python vacíos)

## Fase 2 — Lógica de imposición (`core/impositor.py`)

- [x] Definir jerarquía de excepciones
- [x] Implementar `validar_pdf()`: extensión, legibilidad, contraseña, páginas vacías, formato A4, orientación
- [x] Implementar `_rellenar_paginas()`: añade páginas en blanco hasta múltiplo de 4
- [x] Implementar `imponer()`: genera PDF A4 apaisado con dos páginas A5 por hoja
- [x] Implementar validaciones pre-proceso (archivo disponible, permisos, espacio en disco, archivo de salida bloqueado)

## Fase 3 — Interfaz de usuario (`ui/main_window.py`)

- [x] Clase `MainWindow`: ventana 480×380 no redimensionable, título, tema sistema
- [x] Zona de selección de archivo (campo + botón Examinar)
- [x] Soporte drag & drop sobre la ventana
- [x] Panel de información dinámica (páginas, relleno, hojas, ruta de salida)
- [x] Botón `Procesar PDF` (deshabilitado por defecto)
- [x] Barra de progreso (oculta por defecto)
- [x] Área de log / estado
- [x] Clase `ImpositorWorker(QThread)`: ejecuta imposición en background
- [x] Señales: `progreso(int, int)`, `terminado(str)`, `error(str)`
- [x] Diálogo `Ayuda`
- [x] Diálogo `Acerca de`
- [x] Barra de menú con entradas `Ayuda` y `Acerca de`

## Fase 4 — Entry point (`main.py`)

- [x] Constante `APP_VERSION`
- [x] Instancia `QApplication` + `MainWindow`

## Fase 5 — Empaquetado

- [x] Crear `assets/` con icono placeholder `.ico`
- [x] Documentar comando PyInstaller
- [x] Crear/revisar `impositor-a5.spec`

## Fase 6 — Documentación

- [x] `plan.md` — arquitectura y decisiones de diseño
- [x] `task.md` — este fichero
- [x] `proceso.md` — guía paso a paso para usuario sin experiencia en Python
