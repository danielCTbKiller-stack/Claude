import os
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QCheckBox, QDockWidget, QDoubleSpinBox, QFileDialog, QFormLayout, QLabel, QListWidget,
    QComboBox, QListWidgetItem, QMainWindow, QMessageBox, QPushButton, QSplitter, QTableWidget,
    QTableWidgetItem, QTabWidget, QVBoxLayout, QWidget,
)

from gui.canvas import NetworkCanvas
from importers import import_project
from importers.config import ImportConfig
from services.budget_calculator import BudgetCalculator
from services.network_analyzer import NetworkAnalyzer
from services.report_generator import generate_memorial

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config", "import_config.json")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Hidrossanitário – Água fria")
        self.resize(1280, 780)
        self.import_result = None
        self.project_name = "Projeto"
        self.last_result: Optional[dict] = None

        self.canvas = NetworkCanvas()
        self.pipe_table = self._table(["Trecho", "Q (L/s)", "DN (mm)", "v (m/s)", "hf (mca)"])
        self.node_table = self._table(["Nó", "Cota (m)", "Pressão (mca)", "Mínima (mca)", "Situação"])
        self.budget_table = self._table(["Material", "Qtd (m)", "Preço un.", "Total"])
        self.alerts = QListWidget()
        tabs = QTabWidget()
        for widget, title in ((self.pipe_table, "Trechos"), (self.node_table, "Nós"),
                              (self.budget_table, "Orçamento"), (self.alerts, "Alertas")):
            tabs.addTab(widget, title)
        splitter = QSplitter(Qt.Vertical)
        splitter.addWidget(self.canvas)
        splitter.addWidget(tabs)
        splitter.setSizes([480, 260])
        self.setCentralWidget(splitter)

        self._build_params_dock()
        self._build_menu()
        self.statusBar().showMessage("Abra um projeto DXF ou IFC (Ctrl+O).")

    @staticmethod
    def _table(headers):
        t = QTableWidget(0, len(headers))
        t.setHorizontalHeaderLabels(headers)
        t.setEditTriggers(QTableWidget.NoEditTriggers)
        t.horizontalHeader().setStretchLastSection(True)
        return t

    def _build_params_dock(self):
        form_widget = QWidget()
        form = QFormLayout(form_widget)
        self.pressure = QDoubleSpinBox(); self.pressure.setRange(-50, 200); self.pressure.setValue(5.0)
        self.pressure.setSuffix(" mca")
        self.max_velocity = QDoubleSpinBox(); self.max_velocity.setRange(0.5, 10); self.max_velocity.setValue(3.0)
        self.max_velocity.setSingleStep(0.1); self.max_velocity.setSuffix(" m/s")
        self.auto_size = QCheckBox("Dimensionar diâmetros automaticamente")
        self.source_label = QLabel("–")
        self.rooms_list = QListWidget()
        self.rooms_list.setMaximumHeight(130)
        self.rooms_list.itemChanged.connect(lambda _: self.run_analysis(quiet=True))
        self.view_mode = QComboBox(); self.view_mode.addItems(["Isométrica", "Planta"])
        self.view_mode.currentIndexChanged.connect(lambda i: self.canvas.set_mode("iso" if i == 0 else "plan"))
        rotate = QPushButton("Girar vista 90°"); rotate.clicked.connect(self.canvas.rotate_view)
        run = QPushButton("Calcular"); run.clicked.connect(self.run_analysis)
        form.addRow("Pressão na fonte", self.pressure)
        form.addRow("Velocidade máxima", self.max_velocity)
        form.addRow(self.auto_size)
        form.addRow("Fonte", self.source_label)
        form.addRow("Cômodos consumindo", self.rooms_list)
        form.addRow(run)
        form.addRow("Vista", self.view_mode)
        form.addRow(rotate)
        holder = QWidget()
        column = QVBoxLayout(holder)
        column.addWidget(form_widget)
        column.addStretch(1)
        dock = QDockWidget("Parâmetros", self)
        dock.setWidget(holder)
        self.addDockWidget(Qt.RightDockWidgetArea, dock)

    def _build_menu(self):
        menu = self.menuBar().addMenu("&Arquivo")
        open_act = QAction("&Abrir projeto…", self, shortcut="Ctrl+O", triggered=self.open_file)
        calc_act = QAction("&Calcular", self, shortcut="F5", triggered=self.run_analysis)
        quit_act = QAction("&Sair", self, shortcut="Ctrl+Q", triggered=self.close)
        export_act = QAction("&Exportar memorial de cálculo…", self, shortcut="Ctrl+E", triggered=self.export_report)
        menu.addActions([open_act, calc_act, export_act]); menu.addSeparator(); menu.addAction(quit_act)

    def open_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Abrir projeto", "", "Projetos (*.dxf *.ifc)")
        if path:
            self.load_file(path)

    def load_file(self, path: str):
        try:
            self.import_result = import_project(path, ImportConfig.from_json(CONFIG_PATH))
        except Exception as exc:  # erro de arquivo/formato vai para o usuário, não derruba o app
            QMessageBox.critical(self, "Erro ao abrir", str(exc))
            return
        r = self.import_result
        self.project_name = os.path.splitext(os.path.basename(path))[0]
        self.source_label.setText(r.source_id or "não identificada")
        self.last_result = None
        self.alerts.clear()
        for w in r.warnings:
            self.alerts.addItem(QListWidgetItem(f"Importação: {w}"))
        self.rooms_list.blockSignals(True)
        self.rooms_list.clear()
        for name in r.project.rooms:
            if any(n.room == name for n in r.project.nodes.values()):  # só cômodos com aparelhos
                item = QListWidgetItem(name)
                item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
                item.setCheckState(Qt.Checked)
                self.rooms_list.addItem(item)
        self.rooms_list.blockSignals(False)
        self.canvas.show_project(r.project, r.source_id)
        self._fill_budget()
        self.statusBar().showMessage(
            f"{os.path.basename(path)}: {len(r.project.nodes)} nós, {len(r.project.pipes)} trechos.")

    def report_html(self) -> str:
        from PySide6.QtCore import QBuffer, QByteArray, QIODevice
        data = QByteArray()  # precisa continuar referenciado enquanto o QBuffer o usa
        buf = QBuffer(data)
        buf.open(QIODevice.WriteOnly)
        self.canvas.grab().save(buf, "PNG")
        buf.close()
        r = self.import_result
        return generate_memorial(
            r.project, self.last_result, source_id=r.source_id, source_pressure_mca=self.pressure.value(),
            max_velocity=self.max_velocity.value(), auto_size=self.auto_size.isChecked(),
            active_rooms=self.active_rooms(), project_name=self.project_name, image_png=bytes(data.data()))

    def export_report(self, path: Optional[str] = None):
        if self.last_result is None:
            QMessageBox.information(self, "Exportar", "Calcule o projeto antes de exportar o memorial.")
            return
        if not path:
            path, _ = QFileDialog.getSaveFileName(self, "Exportar memorial", "memorial_de_calculo.pdf",
                                                  "PDF (*.pdf);;HTML (*.html)")
        if not path:
            return
        html = self.report_html()
        if path.lower().endswith(".html"):
            with open(path, "w", encoding="utf-8") as f:
                f.write(html)
        else:
            from PySide6.QtGui import QPageSize, QPdfWriter, QTextDocument
            writer = QPdfWriter(path)
            writer.setPageSize(QPageSize(QPageSize.A4))
            doc = QTextDocument()
            doc.setHtml(html)
            doc.print_(writer)
        self.statusBar().showMessage(f"Memorial exportado: {path}")

    def active_rooms(self):
        if self.rooms_list.count() == 0:
            return None
        return [self.rooms_list.item(i).text() for i in range(self.rooms_list.count())
                if self.rooms_list.item(i).checkState() == Qt.Checked]

    def run_analysis(self, quiet: bool = False):
        r = self.import_result
        if r is None:
            if quiet:
                return
            QMessageBox.information(self, "Calcular", "Abra um projeto primeiro.")
            return
        if r.source_id is None:
            QMessageBox.warning(self, "Calcular", "Nenhuma fonte de água identificada no projeto.")
            return
        try:
            result = NetworkAnalyzer(r.project).analyze(
                r.source_id, self.pressure.value(), self.auto_size.isChecked(), self.max_velocity.value(),
                active_rooms=self.active_rooms())
        except ValueError as exc:
            QMessageBox.warning(self, "Calcular", str(exc))
            return
        result["max_velocity"] = self.max_velocity.value()
        self.last_result = result
        self._fill_results(result)
        self.canvas.show_project(r.project, r.source_id, result)
        n = len(result["alerts"])
        self.statusBar().showMessage("Cálculo concluído – " + (f"{n} alerta(s)." if n else "sem alertas."))

    def _fill_results(self, result):
        project = self.import_result.project
        self._fill(self.pipe_table, [
            (pid, f"{p['flow_lps']:.3f}", f"{p['diameter_mm']:g}", f"{p['velocity_ms']:.2f}", f"{p['head_loss_mca']:.3f}")
            for pid, p in result["pipes"].items()])
        self._fill(self.node_table, [
            (nid, f"{project.nodes[nid].elevation_m:.2f}", f"{n['pressure_mca']:.2f}",
             f"{n['required_mca']:.2f}", "OK" if n["ok"] else "PRESSÃO BAIXA")
            for nid, n in result["nodes"].items()])
        self.alerts.clear()
        for w in self.import_result.warnings:
            self.alerts.addItem(QListWidgetItem(f"Importação: {w}"))
        for a in result["alerts"]:
            self.alerts.addItem(QListWidgetItem(f"[{a['level']}] {a['message']}"))
        self._fill_budget()

    def _fill_budget(self):
        items = BudgetCalculator.calculate_materials_cost(list(self.import_result.project.pipes.values()))
        rows = [(i["material"], f"{i['quantity']:.2f}", f"R$ {i['unit_price']:.2f}", f"R$ {i['total_price']:.2f}")
                for i in items]
        total = sum(i["total_price"] for i in items)
        rows.append(("TOTAL", "", "", f"R$ {total:.2f}"))
        self._fill(self.budget_table, rows)

    @staticmethod
    def _fill(table, rows):
        table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            for c, value in enumerate(row):
                table.setItem(r, c, QTableWidgetItem(value))
        table.resizeColumnsToContents()
