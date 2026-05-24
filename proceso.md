# Proceso: cómo desarrollar, probar y compilar Impositor A5

> Esta guía está pensada para alguien que **nunca ha usado Python ni ha hecho una app de escritorio**. Cada paso está explicado desde cero.

---

## ¿Qué es lo que vamos a hacer?

Vamos a crear una aplicación de escritorio con Python. Python es un lenguaje de programación muy popular que se puede instalar en cualquier ordenador. Usaremos tres herramientas clave:

| Herramienta     | Para qué sirve                                               |
| --------------- | ------------------------------------------------------------ |
| **Python 3.12** | El lenguaje con el que está escrito el programa              |
| **PyQt6**       | La librería que crea las ventanas, botones, etc.             |
| **PyMuPDF**     | La librería que lee y manipula PDFs                          |
| **PyInstaller** | La herramienta que convierte el código en un `.exe` portable |

---

## Paso 1 — Instalar Python (solo la primera vez)

1. Ve a [https://www.python.org/downloads/](https://www.python.org/downloads/) y descarga **Python 3.12** (o superior).
2. Durante la instalación, **marca la casilla "Add Python to PATH"** — es fundamental.
3. Haz clic en _Install Now_.

Para comprobar que se instaló bien, abre el **Terminal** (en macOS: busca "Terminal" en Spotlight; en Windows: busca "PowerShell" o "cmd") y ejecuta:

```bash
python --version
```

Debería aparecer algo como `Python 3.12.x`. Si dice `command not found`, reinicia el ordenador e inténtalo de nuevo.

---

## Paso 2 — Crear un entorno virtual (solo la primera vez)

Un **entorno virtual** es una carpeta aislada donde se instalan las librerías del proyecto sin afectar al resto del sistema. Es una buena práctica siempre usarlo.

Abre el Terminal, navega hasta la carpeta del proyecto y ejecuta:

```bash
# Navegar a la carpeta del proyecto
cd /ruta/a/ImponerPDF/impositor-a5

# Crear el entorno virtual (se crea una carpeta llamada .venv)
python -m venv .venv
```

### Activar el entorno virtual

Cada vez que abras una nueva ventana del Terminal y quieras trabajar en el proyecto, activa el entorno:

- **macOS / Linux:**
  ```bash
  source .venv/bin/activate
  ```
- **Windows (PowerShell):**
  ```powershell
  .venv\Scripts\Activate.ps1
  ```
- **Windows (cmd):**
  ```cmd
  .venv\Scripts\activate.bat
  ```

Sabrás que está activo porque el prompt del terminal mostrará `(.venv)` al principio.

> **Importante:** Activa siempre el entorno virtual antes de instalar librerías o ejecutar el programa.

---

## Paso 3 — Instalar las dependencias

Con el entorno virtual **activo**, instala todas las librerías necesarias con un solo comando:

```bash
pip install -r requirements.txt
```

`pip` es el gestor de paquetes de Python, y `requirements.txt` es el fichero que lista todo lo que necesita este proyecto. Tardará un minuto mientras descarga e instala las librerías.

Para verificar que se instalaron:

```bash
pip list
```

Deberías ver en la lista: `PyQt6`, `PyMuPDF`, `pyinstaller`.

---

## Paso 4 — Ejecutar la aplicación en modo desarrollo

Con el entorno virtual activo y estando en la carpeta `impositor-a5/`:

```bash
python main.py
```

Se abrirá la ventana de la aplicación. Puedes usarla directamente. Cuando hagas cambios en el código, basta con cerrar la ventana y volver a ejecutar `python main.py` para ver los cambios.

> **Nota macOS:** En macOS la app funciona para desarrollar y probar la lógica, pero la versión final (el `.exe` portable) se compila en Windows. Ver Paso 6.

---

## Paso 5 — Estructura del código

```
impositor-a5/
├── main.py               ← Punto de entrada: arranca la app
├── ui/
│   └── main_window.py    ← Toda la ventana, botones y diálogos
├── core/
│   └── impositor.py      ← Lógica de manipulación PDF (sin UI)
├── assets/
│   └── icon.ico          ← Icono de la aplicación
├── requirements.txt      ← Lista de librerías necesarias
├── plan.md               ← Arquitectura y decisiones de diseño
├── task.md               ← Lista de tareas del proyecto
└── proceso.md            ← Este fichero
```

**¿Por qué dos carpetas (`ui/` y `core/`)?**

Es una buena práctica separar la interfaz visual de la lógica del programa. Así puedes probar la lógica de imposición PDF de forma independiente, sin necesidad de abrir ninguna ventana.

---

## Paso 6 — Compilar el ejecutable `.exe` para Windows

> Esta parte se hace **desde un ordenador con Windows** (o una máquina virtual Windows). PyInstaller genera ejecutables nativos del sistema operativo en el que se ejecuta.

### En Windows, con el entorno virtual activo:

```powershell
pyinstaller --onefile --windowed --icon=assets\icon.ico --name=impositor-a5 main.py
```

Explicación de los flags:

- `--onefile`: empaqueta todo en un único `.exe` (sin carpetas adicionales)
- `--windowed`: la app no muestra una ventana de consola al ejecutarse
- `--icon`: asigna el icono al ejecutable
- `--name`: nombre del fichero de salida

Tras ejecutarlo, encontrarás el resultado en:

```
dist/impositor-a5.exe
```

Este fichero es **completamente portable**: puedes copiarlo a cualquier ordenador Windows 11 (64-bit) sin instalar nada. Funciona desde USB, escritorio o cualquier carpeta.

### Fichero `.spec` reutilizable

PyInstaller genera un fichero `impositor-a5.spec` la primera vez. En compilaciones posteriores puedes usarlo directamente:

```powershell
pyinstaller impositor-a5.spec
```

---

## Paso 7 — Solución a problemas comunes

### "python no se reconoce como comando"

- Asegúrate de haber marcado "Add Python to PATH" al instalar.
- Reinicia el terminal (o el ordenador).
- En algunos sistemas puede llamarse `python3` en vez de `python`.

### "No module named PyQt6" o "No module named fitz"

- El entorno virtual no está activo. Actívalo con `source .venv/bin/activate` (macOS/Linux) o `.venv\Scripts\activate` (Windows) y vuelve a intentarlo.

### La ventana no aparece en macOS

- En macOS puede ser necesario conceder permisos en _Preferencias del sistema → Privacidad → Accesibilidad_.
- También puede ayudar ejecutar: `export QT_MAC_DISABLE_FOREGROUND_APP_TRANSFORM=1`

### El PDF de salida está en blanco o tiene errores

- Asegúrate de que el PDF de entrada tiene páginas A4 verticales (210×297 mm).
- Si el PDF está protegido con contraseña, la app lo rechazará antes de procesar.

### El `.exe` compilado tarda en arrancar la primera vez

- Es normal: PyInstaller descomprime el ejecutable en una carpeta temporal al primer uso. Los arranques siguientes son más rápidos.

---

## Resumen de comandos rápidos

```bash
# Solo una vez: crear entorno virtual
python -m venv .venv

# Cada vez que abres el terminal:
source .venv/bin/activate          # macOS/Linux
# o
.venv\Scripts\Activate.ps1         # Windows PowerShell

# Solo una vez: instalar dependencias
pip install -r requirements.txt

# Ejecutar en modo desarrollo
python main.py

# Compilar a .exe (desde Windows)
pyinstaller --onefile --windowed --icon=assets\icon.ico --name=impositor-a5 main.py
```
