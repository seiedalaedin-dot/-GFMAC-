#!/usr/bin/env python3
"""
Core Components Test Module
Unit tests for core financial analysis components
Developer: Seyed Aladdin Mousavi Jashni
"""

import unittest
import asyncio
import logging
from unittest.mock import Mock, patch, AsyncMock
import sys
import os

# اضافه کردن مسیر src به sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.core.crisis_analyzer import CrisisAnalyzer
from src.core.monte_carlo import MonteCarloEngine
from src.core.signal_generator import SignalGenerator
from src.data.market_data import MarketDataManager

class TestCoreComponents(unittest.TestCase):
    """تست کامپوننت‌های اصلی سیستم"""
    
    def setUp(self):
        """آماده‌سازی قبل از هر تست"""
        self.crisis_analyzer = CrisisAnalyzer()
        self.monte_carlo = MonteCarloEngine()
        self.signal_generator = SignalGenerator()
        self.market_data = MarketDataManager()
        
        # داده‌های نمونه برای تست
        self.sample_market_data = {
            'timestamp': '2024-01-01T00:00:00Z',
            'forex': {
                'EUR/USD': {'price': 1.0850, 'change': 0.0010, 'change_percent': 0.09},
                'GBP/USD': {'price': 1.2650, 'change': -0.0020, 'change_percent': -0.16}
            },
            'crypto': {
                'BTC/USD': {'price': 68500, 'change': 1500, 'change_percent': 2.24},
                'ETH/USD': {'price': 3500, 'change': -50, 'change_percent': -1.41}
            },
            'indices': {
                'SPX': {'price': 5200, 'change': 25, 'change_percent': 0.48},
                'DAX': {'price': 18000, 'change': -100, 'change_percent': -0.55}
            },
            'metals': {
                'XAU/USD': {'price': 2350, 'change': 15, 'change_percent': 0.64}
            }
        }
    
    async def async_setup(self):
        """آماده‌سازی async"""
        await self.crisis_analyzer.initialize()
        await self.monte_carlo.initialize()
        await self.signal_generator.initialize()
        await self.market_data.initialize()
    
    def test_crisis_analyzer_initialization(self):
        """تست مقداردهی اولیه تحلیلگر بحران"""
        analyzer = CrisisAnalyzer()
        self.assertIsNotNone(analyzer)
        self.assertIsInstance(analyzer.scenarios, dict)
        self.assertIsInstance(analyzer.indicators, dict)
    
    @patch('src.core.crisis_analyzer.CrisisAnalyzer.analyze')
    async def test_crisis_analysis(self, mock_analyze):
        """تست تحلیل بحران"""
        # شبیه‌سازی نتیجه تحلیل
        mock_analyze.return_value = {
            'crisis_score': 0.15,
            'alert_level': 'LOW',
            'dominant_scenario': 'NORMAL',
            'recommendations': ['MONITOR_MARKETS']
        }
        
        result = await self.crisis_analyzer.analyze(self.sample_market_data)
        
        self.assertIn('crisis_score', result)
        self.assertIn('alert_level', result)
        self.assertIn('recommendations', result)
        self.assertIsInstance(result['recommendations'], list)
    
    @patch('src.core.monte_carlo.MonteCarloEngine.analyze_portfolio_risk')
    async def test_monte_carlo_analysis(self, mock_analyze):
        """تست تحلیل مونت کارلو"""
        # شبیه‌سازی نتیجه تحلیل ریسک
        mock_analyze.return_value = {
            'risk_metrics': {
                'var_95': -0.045,
                'var_99': -0.078,
                'max_drawdown': -0.12
            },
            'crisis_scenarios': {
                'mild_crisis': {'probability': 0.25, 'description': 'کاهش متوسط بازار'}
            }
        }
        
        result = await self.monte_carlo.analyze_portfolio_risk(self.sample_market_data)
        
        self.assertIn('risk_metrics', result)
        self.assertIn('crisis_scenarios', result)
        self.assertIsInstance(result['risk_metrics'], dict)
        self.assertIsInstance(result['crisis_scenarios'], dict)
    
    @patch('src.core.signal_generator.SignalGenerator.generate_signals')
    async def test_signal_generation(self, mock_generate):
        """تست تولید سیگنال"""
        # شبیه‌سازی سیگنال‌ها
        mock_generate.return_value = [
            {
                'symbol': 'EUR/USD',
                'type': 'BUY_LIMIT',
                'entry': 1.0850,
                'stop_loss': 1.0820,
                'take_profits': [1.0870, 1.0890, 1.0910],
                'confidence': 0.82
            }
        ]
        
        signals = await self.signal_generator.generate_signals(self.sample_market_data)
        
        self.assertIsInstance(signals, list)
        if signals:  # اگر سیگنالی تولید شده
            signal = signals[0]
            self.assertIn('symbol', signal)
            self.assertIn('type', signal)
            self.assertIn('confidence', signal)
            self.assertGreaterEqual(signal['confidence'], 0)
            self.assertLessEqual(signal['confidence'], 1)
    
    def test_market_data_structure(self):
        """تست ساختار داده‌های بازار"""
        # بررسی ساختار پایه
        self.assertIn('timestamp', self.sample_market_data)
        self.assertIn('forex', self.sample_market_data)
        self.assertIn('crypto', self.sample_market_data)
        self.assertIn('indices', self.sample_market_data)
        self.assertIn('metals', self.sample_market_data)
        
        # بررسی ساختار داده‌های فارکس
        for symbol, data in self.sample_market_data['forex'].items():
            self.assertIn('price', data)
            self.assertIn('change', data)
            self.assertIn('change_percent', data)
            self.assertIsInstance(data['price'], (int, float))
            self.assertIsInstance(data['change_percent'], (int, float))
    
    @patch('src.data.market_data.MarketDataManager.get_all_market_data')
    async def test_market_data_fetch(self, mock_fetch):
        """تست دریافت داده‌های بازار"""
        mock_fetch.return_value = self.sample_market_data
        
        market_data = await self.market_data.get_all_market_data()
        
        self.assertEqual(market_data, self.sample_market_data)
        mock_fetch.assert_called_once()
    
    def test_crisis_scenario_weights(self):
        """تست وزن سناریوهای بحران"""
        # بررسی اینکه مجموع وزن سناریوها برابر ۱ است
        total_weight = sum(scenario['weight'] for scenario in self.crisis_analyzer.scenarios.values())
        self.assertAlmostEqual(total_weight, 1.0, places=2)
    
    def test_monte_carlo_parameters(self):
        """تست پارامترهای مونت کارلو"""
        self.assertGreater(self.monte_carlo.simulation_count, 0)
        self.assertGreater(self.monte_carlo.time_horizon, 0)
        self.assertIsInstance(self.monte_carlo.confidence_levels, list)
        
        # بررسی سطوح اطمینان
        for confidence in self.monte_carlo.confidence_levels:
            self.assertGreater(confidence, 0)
            self.assertLess(confidence, 1)
    
    async def test_signal_confidence_calculation(self):
        """تست محاسبه اطمینان سیگنال"""
        # داده‌های نمونه برای تحلیل تکنیکال
        tech_analysis = {
            'rsi': 65,
            'trend': 'BULLISH',
            'momentum': 0.8
        }
        
        fundamental_analysis = {
            'news_sentiment': 0.7,
            'volatility_index': 15
        }
        
        # تست اطمینان intraday
        confidence = await self.signal_generator._calculate_intraday_confidence(
            tech_analysis, fundamental_analysis
        )
        
        self.assertGreaterEqual(confidence, 0)
        self.assertLessEqual(confidence, 1)
        
        # تست اطمینان swing
        swing_confidence = await self.signal_generator._calculate_swing_confidence(
            tech_analysis, fundamental_analysis
        )
        
        self.assertGreaterEqual(swing_confidence, 0)
        self.assertLessEqual(swing_confidence, 1)

class TestPerformance(unittest.TestCase):
    """تست‌های عملکرد"""
    
    def setUp(self):
        self.crisis_analyzer = CrisisAnalyzer()
    
    @patch('src.core.crisis_analyzer.CrisisAnalyzer.analyze')
    async def test_crisis_analysis_performance(self, mock_analyze):
        """تست عملکرد تحلیل بحران"""
        import time
        
        mock_analyze.return_value = {'crisis_score': 0.1, 'alert_level': 'LOW'}
        
        start_time = time.time()
        await self.crisis_analyzer.analyze({})
        execution_time = time.time() - start_time
        
        # تحلیل بحران باید در کمتر از ۵ ثانیه انجام شود
        self.assertLess(execution_time, 5.0)

class TestErrorHandling(unittest.TestCase):
    """تست مدیریت خطا"""
    
    def setUp(self):
        self.crisis_analyzer = CrisisAnalyzer()
    
    async def test_crisis_analyzer_with_invalid_data(self):
        """تست تحلیلگر بحران با داده‌های نامعتبر"""
        invalid_data = "invalid_data_string"
        
        # باید خطا مدیریت شود و گزارش خطا برگردانده شود
        result = await self.crisis_analyzer.analyze(invalid_data)
        
        self.assertIn('error', result)
        self.assertIn('alert_level', result)
        self.assertEqual(result['alert_level'], 'UNKNOWN')

def run_tests():
    """اجرای تمام تست‌ها"""
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestCoreComponents)
    suite.addTests(loader.loadTestsFromTestCase(TestPerformance))
    suite.addTests(loader.loadTestsFromTestCase(TestErrorHandling))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

if __name__ == '__main__':
    # اجرای تست‌ها
    success = run_tests()
    sys.exit(0 if success else 1)
