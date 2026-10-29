from typing import Optional

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QBrush, QColor, QPainter, QPen
from PySide6.QtWidgets import QGraphicsScene, QGraphicsView

from services.project_manager import ProjectManager

COLORS = {"OK": "#2e7d32", "INFO": "#1565c0", "ALERTA": "#c62828", "NONE": "#607d8b"}


class NetworkCanvas(QGraphicsView):
    """Vista em planta da rede: tubos coloridos pela situação, nós com a pressão calculada."""

    def __init__(self):
        super().__init__()
        self.setScene(QGraphicsScene(self))
        self.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)

    def wheelEvent(self, event):
        factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
        self.scale(factor, factor)

    def fit(self):
        rect = self.scene().itemsBoundingRect().adjusted(-40, -40, 40, 40)
        self.fitInView(rect, Qt.KeepAspectRatio)

    def show_project(self, project: ProjectManager, source_id: Optional[str], result: Optional[dict] = None):
        scene = self.scene()
        scene.clear()
        if not project.nodes:
            return
        s = 60.0  # pixels por metro; y invertido (planta com Y para cima)

        def pos(nid):
            n = project.nodes[nid]
            return QPointF(n.x_m * s, -n.y_m * s)

        for pipe in project.pipes.values():
            level = "NONE"
            tip = f"{pipe.id}: {pipe.length_m:.2f} m, DN {pipe.diameter_mm:g} mm"
            if result and pipe.id in result["pipes"]:
                r = result["pipes"][pipe.id]
                v = r["velocity_ms"]
                level = "ALERTA" if v > self._max_v(result) else ("INFO" if v < 0.3 else "OK")
                tip += f"\nQ = {r['flow_lps']:.3f} L/s\nv = {v:.2f} m/s\nhf = {r['head_loss_mca']:.3f} mca"
            a, b = pos(pipe.start_node_id), pos(pipe.end_node_id)
            pen = QPen(QColor(COLORS[level]), 4)
            pen.setCapStyle(Qt.RoundCap)
            line = scene.addLine(a.x(), a.y(), b.x(), b.y(), pen)
            line.setToolTip(tip)
            mid = (a + b) / 2
            label = scene.addSimpleText(f"{pipe.id}  DN{pipe.diameter_mm:g}")
            label.setPos(mid + QPointF(4, 4))
            label.setScale(0.9)

        stacked = {}  # nós com mesma posição em planta (prumadas) empilham os rótulos
        for nid, node in project.nodes.items():
            p = pos(nid)
            k = stacked.setdefault((round(p.x()), round(p.y())), [])
            k.append(nid)
            slot = len(k) - 1
            ok = True
            tip = f"{nid}: cota {node.elevation_m:.2f} m"
            if result and nid in result["nodes"]:
                r = result["nodes"][nid]
                ok = r["ok"]
                tip += f"\nPressão = {r['pressure_mca']:.2f} mca (mín. {r['required_mca']:.2f})"
            color = QColor("#f9a825") if nid == source_id else QColor("#c62828" if not ok else "#37474f")
            dot = scene.addEllipse(p.x() - 7, p.y() - 7, 14, 14, QPen(Qt.white, 1.5), QBrush(color))
            dot.setToolTip(tip)
            dot.setZValue(2)
            text = nid + (" (fonte)" if nid == source_id else "")
            if node.fixtures:
                text += "\n" + ", ".join(f.name for f in node.fixtures)
            if result and nid in result["nodes"]:
                text += f"\n{result['nodes'][nid]['pressure_mca']:.2f} mca"
            label = scene.addSimpleText(text)
            label.setPos(p + QPointF(10 + 110 * slot, -34))
            label.setZValue(3)
        self.fit()

    @staticmethod
    def _max_v(result):
        return result.get("max_velocity", 3.0)
