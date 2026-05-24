"""
ui/main_window.py
Ventana principal de Impositor A5 — PyQt6.
"""

import os

from PyQt6.QtCore import (
    Qt,
    QThread,
    pyqtSignal,
)
from PyQt6.QtGui import QDragEnterEvent, QDropEvent
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenuBar,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from core.impositor import (
    ArchivoInvalidoError,
    ArchivoProtegidoError,
    ErrorEscrituraError,
    ErrorProcesamientoError,
    FormatoNoCorrecto,
    ImpositorError,
    imponer,
    validar_pdf,
)


# ---------------------------------------------------------------------------
# Hilo de trabajo
# ---------------------------------------------------------------------------

class ImpositorWorker(QThread):
    """Ejecuta la imposición en un hilo separado."""

    progreso = pyqtSignal(int, int)   # (pagina_actual, total)
    terminado = pyqtSignal(str)        # ruta del archivo generado
    error = pyqtSignal(str)            # mensaje de error

    def __init__(self, ruta: str, parent=None):
        super().__init__(parent)
        self._ruta = ruta

    def run(self):
        try:
            def on_progreso(actual: int, total: int):
                self.progreso.emit(actual, total)

            ruta_out = imponer(self._ruta, callback_progreso=on_progreso)
            self.terminado.emit(ruta_out)
        except ArchivoInvalidoError as exc:
            self.error.emit(f"✗ {exc}")
        except ArchivoProtegidoError as exc:
            self.error.emit(f"⚠ {exc}")
        except FormatoNoCorrecto as exc:
            self.error.emit(f"⚠ {exc}")
        except ErrorEscrituraError as exc:
            self.error.emit(f"✗ {exc}")
        except ErrorProcesamientoError as exc:
            self.error.emit(f"✗ {exc}")
        except ImpositorError as exc:
            self.error.emit(f"✗ {exc}")
        except Exception as exc:
            self.error.emit(f"✗ Error inesperado: {exc}")


# ---------------------------------------------------------------------------
# Ventana principal
# ---------------------------------------------------------------------------

class MainWindow(QMainWindow):
    """Ventana principal 480×380, no redimensionable."""

    def __init__(self, app_version: str, parent=None):
        super().__init__(parent)
        self._version = app_version
        self._ruta_pdf: str = ""
        self._worker: ImpositorWorker | None = None

        self.setWindowTitle("Impositor A5")
        self.setFixedSize(480, 380)
        self.setAcceptDrops(True)

        self._construir_ui()
        self._construir_menu()

    # ------------------------------------------------------------------
    # Construcción de la UI
    # ------------------------------------------------------------------

    def _construir_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(10)
        # --- Encabezado: título + info ---
        header = QHBoxLayout()
        self._titulo = QLabel("Imposición de PDF en A5 a dos caras")
        self._titulo.setStyleSheet("font-size:16px; font-weight:bold;")
        self._titulo.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        self._btn_info = QPushButton("ⓘ")
        self._btn_info.setToolTip("Cómo usar esta aplicación")
        self._btn_info.setFixedSize(28, 28)
        self._btn_info.clicked.connect(self._mostrar_ayuda)

        header.addWidget(self._titulo)
        header.addStretch()
        header.addWidget(self._btn_info)
        layout.addLayout(header)

        # --- Selección de archivo ---
        fila_archivo = QHBoxLayout()
        self._campo_ruta = QLineEdit()
        self._campo_ruta.setPlaceholderText("Selecciona un archivo PDF…")
        self._campo_ruta.setReadOnly(True)
        self._campo_ruta.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self._btn_examinar = QPushButton("Examinar…")
        self._btn_examinar.setFixedWidth(90)
        self._btn_examinar.clicked.connect(self._on_examinar)

        fila_archivo.addWidget(self._campo_ruta)
        fila_archivo.addWidget(self._btn_examinar)
        layout.addLayout(fila_archivo)

        # --- Panel de información ---
        self._panel_info = QLabel()
        self._panel_info.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self._panel_info.setStyleSheet("color: gray;")
        self._panel_info.setWordWrap(True)
        self._panel_info.setTextFormat(Qt.TextFormat.PlainText)
        self._panel_info.setFixedHeight(80)
        self._panel_info.hide()
        layout.addWidget(self._panel_info)

        # --- Botón Procesar ---
        self._btn_procesar = QPushButton("Procesar PDF")
        self._btn_procesar.setEnabled(False)
        self._btn_procesar.setFixedHeight(36)
        self._btn_procesar.clicked.connect(self._on_procesar)
        layout.addWidget(self._btn_procesar)

        # --- Barra de progreso ---
        self._progreso = QProgressBar()
        self._progreso.setMinimum(0)
        self._progreso.setValue(0)
        self._progreso.hide()
        layout.addWidget(self._progreso)

        # --- Área de estado ---
        self._estado = QLabel("")
        self._estado.setWordWrap(True)
        self._estado.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(self._estado)

        layout.addStretch()

        # --- Texto legal al pie ---
        self._legal = QLabel("Kimográfico, Mayo 2026, todos los derechos reservados")
        self._legal.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._legal.setStyleSheet("color: gray; font-size:10px;")
        layout.addWidget(self._legal)

    def _construir_menu(self):
        barra = QMenuBar(self)
        self.setMenuBar(barra)

        menu_ayuda = barra.addMenu("Ayuda")
        act_como = menu_ayuda.addAction("Cómo usar esta aplicación")
        act_como.triggered.connect(self._mostrar_ayuda)

        menu_acerca = barra.addMenu("Acerca de")
        act_acerca = menu_acerca.addAction("Información de la aplicación")
        act_acerca.triggered.connect(self._mostrar_acerca_de)

    # ------------------------------------------------------------------
    # Drag & Drop
    # ------------------------------------------------------------------

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if len(urls) == 1 and urls[0].isLocalFile():
                event.acceptProposedAction()
                return
        event.ignore()

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        if urls:
            ruta = urls[0].toLocalFile()
            self._cargar_pdf(ruta)

    # ------------------------------------------------------------------
    # Slots de botones
    # ------------------------------------------------------------------

    def _on_examinar(self):
        ruta, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar PDF",
            "",
            "Archivos PDF (*.pdf)",
        )
        if ruta:
            self._cargar_pdf(ruta)

    def _on_procesar(self):
        if not self._ruta_pdf:
            return
        self._iniciar_procesado()

    # ------------------------------------------------------------------
    # Carga y validación del PDF
    # ------------------------------------------------------------------

    def _cargar_pdf(self, ruta: str):
        self._ruta_pdf = ""
        self._panel_info.hide()
        self._btn_procesar.setEnabled(False)
        self._campo_ruta.setText(ruta)
        self._set_estado("")

        try:
            info = validar_pdf(ruta)
        except ArchivoInvalidoError as exc:
            self._set_estado(f"⚠ {exc}")
            return
        except ArchivoProtegidoError as exc:
            self._set_estado(f"⚠ {exc}")
            return
        except FormatoNoCorrecto as exc:
            self._set_estado(f"⚠ {exc}")
            return
        except ImpositorError as exc:
            self._set_estado(f"⚠ {exc}")
            return

        self._ruta_pdf = ruta
        self._mostrar_info(info)
        self._set_estado("Archivo cargado correctamente.")
        self._btn_procesar.setEnabled(True)

    def _mostrar_info(self, info: dict):
        num = info["num_paginas"]
        tras = info["paginas_tras_relleno"]
        hojas = info["hojas_salida"]
        salida = info["ruta_salida"]

        if tras == num:
            linea_relleno = f"Páginas tras relleno:       {tras}   (múltiplo de 4 ✓)"
        else:
            anadidas = tras - num
            linea_relleno = f"Páginas tras relleno:       {tras}   (+{anadidas} página{'s' if anadidas > 1 else ''} en blanco añadida{'s' if anadidas > 1 else ''})"

        texto = (
            f"Páginas en el original:     {num}\n"
            f"{linea_relleno}\n"
            f"Hojas de salida:            {hojas}\n"
            f"Archivo de salida:          {salida}"
        )
        self._panel_info.setText(texto)
        self._panel_info.show()

    # ------------------------------------------------------------------
    # Procesado (hilo)
    # ------------------------------------------------------------------

    def _iniciar_procesado(self):
        self._btn_procesar.setEnabled(False)
        self._btn_procesar.setText("Procesando…")
        self._progreso.setValue(0)
        self._progreso.show()
        self._set_estado("Iniciando procesado…")

        self._worker = ImpositorWorker(self._ruta_pdf, parent=self)
        self._worker.progreso.connect(self._on_progreso)
        self._worker.terminado.connect(self._on_terminado)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _on_progreso(self, actual: int, total: int):
        self._progreso.setMaximum(total)
        self._progreso.setValue(actual)
        self._set_estado(f"Procesando página {actual} de {total}…")

    def _on_terminado(self, ruta_out: str):
        nombre = os.path.basename(ruta_out)
        self._set_estado(f"✓ PDF generado: {nombre}")
        self._btn_procesar.setText("Procesar PDF")
        self._btn_procesar.setEnabled(True)
        self._progreso.hide()

    def _on_error(self, mensaje: str):
        self._set_estado(mensaje)
        self._btn_procesar.setText("Procesar PDF")
        self._btn_procesar.setEnabled(bool(self._ruta_pdf))
        self._progreso.hide()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _set_estado(self, texto: str):
        self._estado.setText(texto)

    # ------------------------------------------------------------------
    # Diálogos
    # ------------------------------------------------------------------

    def _mostrar_ayuda(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Cómo usar esta aplicación")
        dlg.setFixedSize(440, 400)
        dlg.setModal(True)

        layout = QVBoxLayout(dlg)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(10)

        contenido = QTextBrowser()
        contenido.setOpenExternalLinks(False)
        contenido.setHtml(
            """
            <h3>Cómo usar Impositor A5</h3>
            <p>Impositor A5 convierte un PDF en formato A4 vertical en un documento
            listo para imprimir como cuadernillo A5 encuadernado en gusanillo.</p>

            <b>Pasos:</b>
            <ol>
              <li>Selecciona un archivo PDF pulsando <b>Examinar…</b> o arrástralo
                  directamente sobre la ventana.</li>
              <li>Comprueba la información del documento (páginas, hojas de salida,
                  archivo generado).</li>
              <li>Pulsa <b>Procesar PDF</b>. El archivo resultante se guardará
                  automáticamente en la misma carpeta que el original,
                  con el sufijo <code>_A5</code>.</li>
            </ol>

            <b>Requisitos del PDF de entrada:</b>
            <ul>
              <li>Todas las páginas deben ser tamaño A4 (210 × 297 mm) en orientación vertical.</li>
              <li>El PDF no debe estar protegido con contraseña.</li>
              <li>Si el número de páginas no es múltiplo de 4, se añadirán páginas en blanco
                  al final de forma automática.</li>
            </ul>

            <b>Cómo imprimir:</b>
            <ul>
              <li>Imprime el PDF resultante en <b>doble cara</b>, con la opción
                  <b>"voltear en borde largo"</b> activada en tu impresora.</li>
              <li>Imprime a tamaño real (100%), sin ajuste de escala.</li>
              <li>Cada hoja impresa contiene dos páginas A5. Encuadérnalas en el
                  orden en que salen.</li>
            </ul>
            """
        )
        layout.addWidget(contenido)

        botones = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        botones.rejected.connect(dlg.reject)
        layout.addWidget(botones)

        dlg.exec()

    def _mostrar_acerca_de(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Acerca de")
        dlg.setFixedSize(360, 240)
        dlg.setModal(True)

        layout = QVBoxLayout(dlg)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(10)

        contenido = QTextBrowser()
        contenido.setOpenExternalLinks(False)
        contenido.setHtml(
            f"""
            <h3>Impositor A5</h3>
            <p><b>Versión:</b> {self._version}</p>
            <p>Herramienta de imposición tipográfica para cuadernillos A5
            encuadernados en gusanillo.</p>
            <p>© 2025 Kimo. Todos los derechos reservados.</p>
            <p>Desarrollado con Python, PyMuPDF y PyQt6.<br>
            PyMuPDF está sujeto a la licencia GNU AGPL 3.0.<br>
            PyQt6 está sujeto a la licencia GNU GPL 3.0.</p>
            """
        )
        layout.addWidget(contenido)

        botones = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        botones.rejected.connect(dlg.reject)
        layout.addWidget(botones)

        dlg.exec()
