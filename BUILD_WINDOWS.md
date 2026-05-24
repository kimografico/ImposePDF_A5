# Generar el ejecutable Windows (.exe) — Impositor A5

Esta guía paso a paso explica cómo crear un `.exe` de Windows (64-bit) desde el código fuente del proyecto `impositor-a5`.

Requisitos previos (en el equipo Windows donde compilarás):

- Windows 10/11 (64-bit)
- Conexión a Internet
- Python 3.12 de 64-bit instalado (instalador: "Install for me only" si no tienes permisos de admin)
- Git (opcional, para clonar el repo)

Si prefieres no compilar localmente, usa la Action de GitHub incluida (ver README/CI). Esta guía es para compilación manual.

---

1. Preparar el entorno

- Abre PowerShell (recomendado) o CMD como usuario normal.
- Navega a la carpeta del proyecto (o clónalo primero):

```powershell
# Si no has clonado el repo en este equipo:
git clone https://github.com/kimografico/ImposePDF_A5.git
cd ImposePDF_A5/impositor-a5

# Si ya tienes el código en una carpeta, sitúate en ella:
# cd C:\ruta\a\ImposePDF\impositor-a5
```

2. Crear y activar un entorno virtual (recomendado)

```powershell
# Crear venv
python -m venv .venv

# Activar en PowerShell
.\.venv\Scripts\Activate.ps1

# Si usas cmd.exe
.venv\Scripts\activate.bat
```

Verifica que en el prompt aparece `(.venv)`.

3. Actualizar pip e instalar dependencias

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Asegúrate de que se han instalado `PyQt6`, `PyMuPDF` y `pyinstaller`.

4. Verificar ejecución en modo desarrollo

Antes de empaquetar, confirma que la app arranca correctamente:

```powershell
python main.py
```

Si la ventana se abre y puedes seleccionar un PDF de prueba, continúa.

5. Preparar icono (opcional)

Si quieres incluir un icono personalizado, colócalo en `assets\icon.ico`. Si no existe, omite la opción `--icon` en PyInstaller o usa un icono temporal.

6. Ejecutar PyInstaller para generar el `.exe`

Usa PyInstaller con `--onefile` y `--windowed` para un único ejecutable sin consola.

```powershell
# Activar venv si no está activo
.\.venv\Scripts\Activate.ps1

pyinstaller --onefile --windowed --icon=assets\icon.ico --name=impositor-a5 main.py
```

Explicación flags:

- `--onefile`: empaqueta todo en un único `.exe` en `dist\`.
- `--windowed`: no abre ventana de consola (GUI only).
- `--icon`: archivo `.ico` para el ejecutable (opcional).
- `--name`: nombre final del ejecutable.

7. Resultado

Tras completar, encontrarás el ejecutable en `dist\impositor-a5.exe`.
Prueba abrirlo en el equipo Windows donde quieras usarlo.

8. Problemas comunes y soluciones

- Error: "No module named ..." durante ejecución del `.exe` → Asegúrate de que `pyinstaller` se ejecutó en el mismo venv donde instalaste dependencias; revisa `pip list`.

- Icono no incluido o fallo con PyQt6 → Intenta ejecutar PyInstaller sin `--icon` y revisa la salida; a veces PyInstaller necesita hooks para PyQt6, pero en la mayoría de instalaciones recientes funciona automáticamente.

- El `.exe` se bloquea al iniciarse → Ejecuta el `.exe` desde PowerShell para ver errores en consola (si fue creado sin `--windowed`) o habilita temporalmente `--console` para debug:

```powershell
# para debug rápido
pyinstaller --onefile --console main.py
```

- Problemas de dependencias nativas (PyMuPDF): PyMuPDF incluye binarios; asegúrate de usar la versión de Python correcta (64-bit). Si ves errores al importar `fitz`, reinstala PyMuPDF:

```powershell
pip install --force-reinstall PyMuPDF
```

- Espacio en disco o antivirus que elimina el ejecutable al crear/distribuir: comprueba que hay suficiente espacio y que Windows Defender/antivirus no está bloqueando `dist\impositor-a5.exe`.

9. Firma digital (opcional, recomendado para distribución)

Si vas a distribuir el `.exe`, firma el binario con un certificado válido (EV code signing). El proceso requiere herramientas de Microsoft (`signtool`) y un certificado de firma.

10. Crear un instalador (opcional)

PyInstaller produce un `.exe` portable. Si necesitas instalador (MSI/Setup), usa herramientas como Inno Setup o NSIS tras generar el `.exe`.

11. Reproducibilidad y CI (opcional)

Si prefieres no compilar localmente, añade un workflow de GitHub Actions que ejecute PyInstaller en `windows-latest` y suba el `.exe` como artefacto. Ejemplo de workflow está en la conversación previa; puedo proporcionarlo listo para copiar si quieres.

---

Notas finales

- PyInstaller debe ejecutarse en Windows para generar ejecutables Windows fiables.
- Mantén el entorno virtual limpio y usa siempre el venv para instalar dependencias antes de ejecutar PyInstaller.
- Si encuentras errores concretos, copia las líneas de error y te ayudo a solucionarlos.
