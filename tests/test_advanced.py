from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import analyze_gold_drivers as tool

HEADER='series,observation_date,available_at,value,unit\n'
def panel(start=(2000,25,100,2),end=(2100,28,101,2.1)):
    rows=[]
    for day,values in [('2024-01-08',start),('2024-01-09',end)]:
        for (name,unit),value in zip(tool.UNITS.items(),values):
            rows.append(f'{name},{day},{day}T00:00:00Z,{value},{unit}')
    return (HEADER+'\n'.join(rows)+'\n').encode()

class AdvancedTests(unittest.TestCase):
    def check(self,raw):
        return tool.analyze(raw,'2024-01-09T12:00:00Z','synthetic')

    def test_returns_yield_basis_points_and_ratio_have_correct_units(self):
        result=self.check(panel())
        self.assertAlmostEqual(result['returns']['XAUUSD'],.05)
        self.assertAlmostEqual(result['real_yield_change_bp'],10)
        self.assertEqual(result['gold_silver_ratio_end'],75)
        self.assertTrue(result['co_movement']['gold_up_with_dollar_and_yield_up'])
        result=self.check(panel(start=(2000,25,100,-1),end=(2100,28,101,-.9)))
        self.assertAlmostEqual(result['real_yield_change_bp'],10)

    def test_future_publication_values_cannot_change_comparison(self):
        results=[self.check(panel()+f'XAUUSD,2024-01-09,2024-01-10T00:00:00Z,{value},USD_per_troy_ounce\n'.encode()) for value in (1,99999)]
        self.assertEqual(results[0]['returns'],results[1]['returns'])
        self.assertEqual(results[0]['excluded_unavailable_rows'],1)

    def test_incomplete_date_does_not_forward_fill(self):
        raw=panel()+b'XAUUSD,2024-01-09,2024-01-09T06:00:00Z,2110,USD_per_troy_ounce\n'
        with self.assertRaises(ValueError):
            self.check(raw)
        raw=panel().replace(b'DXY,2024-01-09,2024-01-09T00:00:00Z,101,index_points\n',b'')
        with self.assertRaises(ValueError):
            self.check(raw)

    def test_wrong_units_zero_price_and_nominal_yield_are_rejected(self):
        for old,new in [(b'USD_per_troy_ounce',b'CNY_per_gram'),(b',2100,',b',0,'),(b'US10Y_REAL',b'US10Y_NOMINAL')]:
            with self.subTest(new=new),self.assertRaises(ValueError):
                self.check(panel().replace(old,new))
