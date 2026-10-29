import os
import tempfile
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from gui.main_window import MainWindow
from tests.test_importers import make_dxf


class TestMainWindow(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_load_and_calculate(self):
        w = MainWindow()
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "p.dxf")
            make_dxf(path)
            w.load_file(path)
        self.assertEqual(w.source_label.text(), "N1")
        self.assertEqual(w.pipe_table.rowCount(), 0)
        w.auto_size.setChecked(True)
        w.run_analysis()
        self.assertEqual(w.pipe_table.rowCount(), 4)
        self.assertEqual(w.node_table.rowCount(), 5)
        self.assertEqual(w.budget_table.item(w.budget_table.rowCount() - 1, 0).text(), "TOTAL")

    def test_low_pressure_shown(self):
        w = MainWindow()
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "p.dxf")
            make_dxf(path)
            w.load_file(path)
        w.pressure.setValue(-10.0)
        w.run_analysis()
        texts = [w.alerts.item(i).text() for i in range(w.alerts.count())]
        self.assertTrue(any("LOW_PRESSURE" in t or "pressão" in t for t in texts))


if __name__ == "__main__":
    unittest.main()
