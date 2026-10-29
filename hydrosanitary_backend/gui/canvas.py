import math
from typing import Optional

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QBrush, QColor, QPainter, QPen, QPolygonF
from PySide6.QtWidgets import QGraphicsScene, QGraphicsView

from services.project_manager import ProjectManager

COLORS = {"OK": "#2e7d32", "INFO": "#1565c0", "ALERTA": "#c62828", "IDLE": "#b0bec5", "NONE": "#607d8b"}
ROOM_TINTS = ["#90caf9", "#ffcc80", "#a5d6a7", "#ce93d8", "#fff59d", "#80cbc4"]
SCALE = 60.0  # pixels por metro


class NetworkCanvas(QGraphicsView):
    """
    Vista isométrica (ou em planta) do projeto: pisos dos cômodos, paredes translúcidas
    e a tubulação desenhada por cima, colorida pela velocidade; nós com a pressão calculada.
    """

    def __init__(self):
        super().__init__()
        self.setScene(QGraphicsScene(self))
        self.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setBackgroundBrush(QColor("#fafafa"))
        self.mode = "iso"      # "iso" | "plan"
        self.rotation = 0      # múltiplos de 90°
        self._data = None

    # ---- interação -------------------------------------------------
    def wheelEvent(self, event):
        factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
        self.scale(factor, factor)

    def set_mode(self, mode: str):
        self.mode = mode
        self._redraw()

    def rotate_view(self):
        self.rotation = (self.rotation + 1) % 4
        self._redraw()

    def fit(self):
        rect = self.scene().itemsBoundingRect().adjusted(-40, -40, 40, 40)
        self.fitInView(rect, Qt.KeepAspectRatio)

    def show_project(self, project: ProjectManager, source_id: Optional[str], result: Optional[dict] = None):
        self._data = (project, source_id, result)
        self._redraw()

    # ---- projeção --------------------------------------------------
    def _center(self, project):
        xs = [n.x_m for n in project.nodes.values()]
        ys = [n.y_m for n in project.nodes.values()]
        for w in project.walls:
            xs += [w.x0_m, w.x1_m]; ys += [w.y0_m, w.y1_m]
        for r in project.rooms.values():
            xs += [p[0] for p in r.polygon]; ys += [p[1] for p in r.polygon]
        return ((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2) if xs else (0.0, 0.0)

    def _proj(self, x, y, z):
        cx, cy = self._c
        dx, dy = x - cx, y - cy
        for _ in range(self.rotation):
            dx, dy = -dy, dx
        if self.mode == "plan":
            return QPointF(dx * SCALE, -dy * SCALE)
        # isométrica: eixos x e y a 30° da horizontal, z para cima
        return QPointF((dx - dy) * math.cos(math.radians(30)) * SCALE,
                       (dx + dy) * math.sin(math.radians(30)) * SCALE - z * SCALE)

    def _depth(self, x, y):
        cx, cy = self._c
        dx, dy = x - cx, y - cy
        for _ in range(self.rotation):
            dx, dy = -dy, dx
        return dx + dy  # maior = mais perto do observador

    # ---- desenho ---------------------------------------------------
    def _redraw(self):
        if self._data is None:
            return
        project, source_id, result = self._data
        scene = self.scene()
        scene.clear()
        if not project.nodes:
            return
        self._c = self._center(project)
        P = self._proj

        for i, room in enumerate(project.rooms.values()):
            poly = QPolygonF([P(x, y, room.z_floor_m) for x, y in room.polygon])
            tint = QColor(ROOM_TINTS[i % len(ROOM_TINTS)]); tint.setAlpha(110)
            item = scene.addPolygon(poly, QPen(QColor("#90a4ae"), 1), QBrush(tint))
            item.setZValue(0)
            cx = sum(p[0] for p in room.polygon) / len(room.polygon)
            cy = sum(p[1] for p in room.polygon) / len(room.polygon)
            label = scene.addSimpleText(room.name)
            label.setBrush(QColor("#455a64"))
            label.setPos(P(cx, cy, room.z_floor_m) - QPointF(label.boundingRect().width() / 2, 6))
            label.setZValue(1)

        for w in sorted(project.walls, key=lambda w: self._depth((w.x0_m + w.x1_m) / 2, (w.y0_m + w.y1_m) / 2)):
            top = w.z_base_m + w.height_m
            if self.mode == "plan":
                a, b = P(w.x0_m, w.y0_m, 0), P(w.x1_m, w.y1_m, 0)
                scene.addLine(a.x(), a.y(), b.x(), b.y(), QPen(QColor("#78909c"), 5)).setZValue(1)
                continue
            quad = QPolygonF([P(w.x0_m, w.y0_m, w.z_base_m), P(w.x1_m, w.y1_m, w.z_base_m),
                              P(w.x1_m, w.y1_m, top), P(w.x0_m, w.y0_m, top)])
            scene.addPolygon(quad, QPen(QColor("#90a4ae"), 1), QBrush(QColor(176, 190, 197, 70))).setZValue(2)

        max_v = result.get("max_velocity", 3.0) if result else 3.0
        for pipe in project.pipes.values():
            level, tip = "NONE", f"{pipe.id}: {pipe.length_m:.2f} m, DN {pipe.diameter_mm:g} mm"
            if result and pipe.id in result["pipes"]:
                r = result["pipes"][pipe.id]
                v = r["velocity_ms"]
                level = "IDLE" if r["flow_lps"] <= 0 else ("ALERTA" if v > max_v else ("INFO" if v < 0.3 else "OK"))
                tip += f"\nQ = {r['flow_lps']:.3f} L/s\nv = {v:.2f} m/s\nhf = {r['head_loss_mca']:.3f} mca"
            n0, n1 = project.nodes[pipe.start_node_id], project.nodes[pipe.end_node_id]
            a, b = P(n0.x_m, n0.y_m, n0.elevation_m), P(n1.x_m, n1.y_m, n1.elevation_m)
            pen = QPen(QColor(COLORS[level]), max(3.0, pipe.diameter_mm / 7.0))
            pen.setCapStyle(Qt.RoundCap)
            line = scene.addLine(a.x(), a.y(), b.x(), b.y(), pen)
            line.setToolTip(tip)
            line.setZValue(10)

        for nid, node in project.nodes.items():
            p = P(node.x_m, node.y_m, node.elevation_m)
            r = result["nodes"].get(nid) if result else None
            active = bool(r and r["required_mca"] > 0)
            tip = f"{nid}: cota {node.elevation_m:.2f} m" + (f" – {node.room}" if node.room else "")
            if r:
                tip += f"\nPressão = {r['pressure_mca']:.2f} mca (mín. {r['required_mca']:.2f})"
            if nid == source_id:
                color, size = QColor("#f9a825"), 9
            elif node.fixtures:
                color, size = QColor("#c62828" if (r and not r["ok"]) else ("#0277bd" if active or not r else "#90a4ae")), 7
            else:
                color, size = QColor("#37474f"), 4
            dot = scene.addEllipse(p.x() - size, p.y() - size, 2 * size, 2 * size, QPen(Qt.white, 1.5), QBrush(color))
            dot.setToolTip(tip)
            dot.setZValue(11)
            if nid == source_id or node.fixtures:
                text = "FONTE" if nid == source_id else ", ".join(f.name.replace("_", " ") for f in node.fixtures)
                if r and (nid == source_id or active):
                    text += f"\n{r['pressure_mca']:.2f} mca"
                label = scene.addSimpleText(text)
                label.setScale(0.85)
                label.setPos(p + QPointF(size + 3, -size - 14))
                label.setZValue(12)
        self.fit()
