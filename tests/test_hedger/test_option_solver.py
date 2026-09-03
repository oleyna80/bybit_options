import unittest
from datetime import datetime
from bybit_options.services.hedger.option_solver import OptionSolver

class TestOptionSolver(unittest.TestCase):
    
    def test_get_target_expiry_basic(self):
        """Test basic expiry selection - picks nearest future expiry."""
        current_year = datetime.now().year
        next_year = current_year + 1
        future_year = str(next_year)[-2:]
        
        exp1 = f"10JAN{future_year}"
        exp2 = f"15JAN{future_year}"
        
        selected = OptionSolver.get_target_expiry([exp1, exp2], min_days=2)
        self.assertEqual(selected, exp1)
        
    def test_get_target_expiry_empty_list(self):
        """Test with empty expiry list - should return None."""
        self.assertIsNone(OptionSolver.get_target_expiry([]))
        
    def test_get_target_expiry_all_past(self):
        """Test when all expiries are in the past - should return None."""
        past_expiries = ["10JAN20", "15FEB21", "20MAR22"]
        self.assertIsNone(OptionSolver.get_target_expiry(past_expiries, min_days=2))
        
    def test_get_target_expiry_invalid_format(self):
        """Test with invalid format strings - should skip them gracefully."""
        current_year = datetime.now().year
        next_year = current_year + 1
        future_year = str(next_year)[-2:]
        
        valid = f"10JAN{future_year}"
        invalid_expiries = ["INVALID", "2024-01-10", "XXXYY99", valid]
        
        # Should still find the valid one
        selected = OptionSolver.get_target_expiry(invalid_expiries, min_days=2)
        self.assertEqual(selected, valid)
        
    def test_get_atm_strike(self):
        """Test ATM strike calculation."""
        self.assertEqual(OptionSolver.get_atm_strike(40000), 40000)
        self.assertEqual(OptionSolver.get_atm_strike(40249), 40000)
        self.assertEqual(OptionSolver.get_atm_strike(40250), 40000)  # Banker's rounding
        self.assertEqual(OptionSolver.get_atm_strike(40251), 40500)
        
    def test_get_atm_strike_custom_step(self):
        """Test ATM strike with custom step size."""
        self.assertEqual(OptionSolver.get_atm_strike(40000, step=1000), 40000)
        self.assertEqual(OptionSolver.get_atm_strike(40600, step=1000), 41000)
        
    def test_format_symbol(self):
        """Test option symbol formatting."""
        sym = OptionSolver.format_symbol("BTC", "29DEC23", 40000, "C")
        self.assertEqual(sym, "BTC-29DEC23-40000-C")
        
        sym_put = OptionSolver.format_symbol("ETH", "15JAN24", 2500, "P")
        self.assertEqual(sym_put, "ETH-15JAN24-2500-P")

if __name__ == "__main__":
    unittest.main()

