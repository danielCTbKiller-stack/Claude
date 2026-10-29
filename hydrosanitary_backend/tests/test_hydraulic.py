import unittest

from core.entities import Pipe
from engine.hydraulic_calculator import HydraulicCalculator
from engine.validator import HydraulicValidator
from services.budget_calculator import BudgetCalculator
from services.project_manager import ProjectManager


class TestHydraulicEngine(unittest.TestCase):

    def test_probable_flow_calculation(self):
        flow = HydraulicCalculator.calculate_probable_flow(4.0)
        self.assertAlmostEqual(flow, 0.6)

    def test_velocity_calculation(self):
        velocity = HydraulicCalculator.calculate_velocity(0.2, 20.0)
        self.assertAlmostEqual(velocity, 0.6366, places=3)

    def test_head_loss_fair_whipple_hsiao(self):
        pipe = Pipe("P1", "N1", "N2", length_m=10.0, diameter_mm=25.0)
        hf = HydraulicCalculator.calculate_head_loss(pipe, 0.3)
        # J ≈ 0.0242 m/m para Q=0.3 L/s e D=25 mm
        self.assertAlmostEqual(hf, 0.242, places=3)

    def test_validator_high_velocity(self):
        result = HydraulicValidator.validate_pipe_limits("P1", velocity=3.5, max_allowable_velocity=3.0)
        self.assertEqual(result["level"], "ALERTA")

    def test_validator_ok(self):
        result = HydraulicValidator.validate_pipe_limits("P1", velocity=1.0)
        self.assertEqual(result["code"], "APPROVED")


class TestServices(unittest.TestCase):

    def test_project_summary(self):
        pm = ProjectManager()
        pm.add_pipe(Pipe("P1", "N1", "N2", 5.0, 20.0))
        self.assertEqual(pm.get_project_summary(), {"total_nodes": 0, "total_pipes": 1})

    def test_budget_uses_price_table_for_float_diameters(self):
        pipes = [Pipe("P1", "A", "B", 3.0, 20.0), Pipe("P2", "B", "C", 2.0, 20.0)]
        items = BudgetCalculator.calculate_materials_cost(pipes)
        self.assertEqual(items[0]["material"], "Tubo PVC Soldável 20mm")
        self.assertEqual(items[0]["total_price"], 60.0)


if __name__ == "__main__":
    unittest.main()
