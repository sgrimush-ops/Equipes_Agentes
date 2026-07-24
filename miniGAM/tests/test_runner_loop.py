import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.runner import MiniGamRunner


class TestRunnerLoop(unittest.TestCase):
    def test_atingiu_valor_total_com_tolerancia(self):
        runner = MiniGamRunner(excel_manager=object(), screen_reader=object())

        self.assertTrue(runner._atingiu_valor_total(100.00, 100.00))
        self.assertTrue(runner._atingiu_valor_total(99.99, 100.00, tolerancia=0.02))
        self.assertFalse(runner._atingiu_valor_total(99.00, 100.00, tolerancia=0.01))


if __name__ == '__main__':
    unittest.main()
