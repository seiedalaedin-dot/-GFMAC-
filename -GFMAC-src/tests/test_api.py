#!/usr/bin/env python3
"""
API Test Module
Unit tests for API endpoints and handlers
Developer: Seyed Aladdin Mousavi Jashni
"""

import unittest
import asyncio
import sys
import os
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
import json

# اضافه کردن مسیر src به sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.api.routes import api_router
from src.api.handlers import MarketDataHandler, SignalHandler, PortfolioHandler
from fastapi import FastAPI

class TestAPIEndpoints(unittest.TestCase):
    """تست endpointهای API"""
    
    def setUp(self):
        """آماده‌سازی قبل از هر تست"""
        # ایجاد اپلیکیشن FastAPI برای تست
        self.app = FastAPI()
        self.app.include_router(api_router)
        self.client = TestClient(self.app)
        
        self.market_handler = MarketDataHandler()
        self.signal_handler = SignalHandler()
        self.portfolio_handler = PortfolioHandler()
        
        # توکن تست
        self.test_token = "test_jwt_token"
        self.test_session_id = "test_session_123"
        
        # داده‌های نمونه
        self.sample_market_data = {
            'timestamp': '2024-01-01T00:00:00Z',
            'forex': {'EUR/USD': {'price': 1.0850}},
            'crypto': {'BTC/USD': {'price': 68500}},
            'indices': {'SPX': {'price': 5200}},
            'metals': {'XAU/USD': {'price': 2350}}
        }
    
    def test_health_endpoint(self):
        """تست endpoint سلامت سیستم"""
        response = self.client.get("/api/system/health")
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('status', data)
        self.assertIn('timestamp', data)
        self.assertIn('version', data)
    
    @patch('src.security.auth_manager.auth_manager.verify_token')
    @patch('src.security.session_manager.session_manager.validate_session')
    @patch('src.api.handlers.market_data_handler.get_market_overview')
    async def test_market_overview_endpoint(self, mock_overview, mock_validate, mock_verify):
        """تست endpoint نمای کلی بازار"""
        # شبیه‌سازی احراز هویت
        mock_verify.return_value = (True, {'user_id': 'test_user'})
        mock_validate.return_value = (True, {})
        
        # شبیه‌سازی داده‌های بازار
        mock_overview.return_value = {
            'status': 'success',
            'market_condition': 'NORMAL',
            'crisis_score': 0.15,
            'active_instruments': {
                'forex': 8, 'crypto': 8, 'indices': 10, 'metals': 4
            }
        }
        
        # در اینجا باید از TestClient با async استفاده کنیم
        # برای سادگی، مستقیماً handler را تست می‌کنیم
        result = await self.market_handler.get_market_overview('test_user')
        
        self.assertEqual(result['status'], 'success')
        self.assertIn('market_condition', result)
        self.assertIn('crisis_score', result)
        self.assertIn('active_instruments', result)
    
    @patch('src.api.handlers.market_data_handler.get_instrument_data')
    async def test_instrument_data_endpoint(self, mock_instrument):
        """تست endpoint داده‌های نماد"""
        # شبیه‌سازی داده‌های نماد
        mock_instrument.return_value = {
            'status': 'success',
            'symbol': 'EUR/USD',
            'current_data': {'price': 1.0850, 'change_percent': 0.09},
            'market_type': 'forex'
        }
        
        result = await self.market_handler.get_instrument_data('EUR/USD', 'test_user')
        
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['symbol'], 'EUR/USD')
        self.assertIn('current_data', result)
        self.assertIn('market_type', result)
    
    @patch('src.api.handlers.signal_handler.get_trading_signals')
    async def test_trading_signals_endpoint(self, mock_signals):
        """تست endpoint سیگنال‌های معاملاتی"""
        # شبیه‌سازی سیگنال‌ها
        mock_signals.return_value = {
            'status': 'success',
            'total_signals': 2,
            'signals': [
                {
                    'symbol': 'EUR/USD',
                    'type': 'BUY_LIMIT',
                    'confidence': 0.82
                },
                {
                    'symbol': 'XAU/USD', 
                    'type': 'SELL_STOP',
                    'confidence': 0.76
                }
            ]
        }
        
        filters = {'min_confidence': 0.7}
        result = await self.signal_handler.get_trading_signals('test_user', filters)
        
        self.assertEqual(result['status'], 'success')
        self.assertIn('total_signals', result)
        self.assertIn('signals', result)
        self.assertIsInstance(result['signals'], list)
        
        # بررسی فیلتر اطمینان
        for signal in result['signals']:
            self.assertGreaterEqual(signal['confidence'], 0.7)
    
    @patch('src.api.handlers.portfolio_handler.analyze_portfolio')
    async def test_portfolio_analysis_endpoint(self, mock_analysis):
        """تست endpoint تحلیل پرتفولیو"""
        # شبیه‌سازی تحلیل پرتفولیو
        mock_analysis.return_value = {
            'status': 'success',
            'risk_metrics': {
                'var_95': -0.045,
                'max_drawdown': -0.12
            },
            'crisis_impact': 0.15,
            'recommendations': [
                {
                    'type': 'RISK_MANAGEMENT',
                    'action': 'Reduce portfolio risk'
                }
            ]
        }
        
        portfolio_data = {
            'forex': {'EUR/USD': {'weight': 0.3}},
            'crypto': {'BTC/USD': {'weight': 0.2}}
        }
        
        result = await self.portfolio_handler.analyze_portfolio(portfolio_data, 'test_user')
        
        self.assertEqual(result['status'], 'success')
        self.assertIn('risk_metrics', result)
        self.assertIn('crisis_impact', result)
        self.assertIn('recommendations', result)
        self.assertIsInstance(result['recommendations'], list)
    
    @patch('src.api.handlers.portfolio_handler.get_optimal_allocation')
    async def test_optimal_allocation_endpoint(self, mock_allocation):
        """تست endpoint تخصیص بهینه"""
        # شبیه‌سازی تخصیص بهینه
        mock_allocation.return_value = {
            'status': 'success',
            'risk_tolerance': 'MODERATE',
            'optimal_allocation': {
                'stocks': 0.5, 'bonds': 0.3, 'cash': 0.1, 'gold': 0.1
            },
            'expected_return': 0.062,
            'risk_estimate': 0.085
        }
        
        user_preferences = {
            'risk_tolerance': 'MODERATE',
            'investment_horizon': 'MEDIUM'
        }
        
        result = await self.portfolio_handler.get_optimal_allocation(user_preferences, 'test_user')
        
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['risk_tolerance'], 'MODERATE')
        self.assertIn('optimal_allocation', result)
        self.assertIn('expected_return', result)
        self.assertIn('risk_estimate', result)
        
        # بررسی مجموع وزن‌ها
        total_allocation = sum(result['optimal_allocation'].values())
        self.assertAlmostEqual(total_allocation, 1.0, places=2)

class TestAPIErrorHandling(unittest.TestCase):
    """تست مدیریت خطا در API"""
    
    def setUp(self):
        self.market_handler = MarketDataHandler()
        self.signal_handler = SignalHandler()
    
    @patch('src.api.handlers.market_data_handler.get_market_overview')
    async def test_market_overview_error(self, mock_overview):
        """تست خطا در endpoint نمای کلی بازار"""
        # شبیه‌سازی خطا
        mock_overview.side_effect = Exception("Database connection failed")
        
        with self.assertRaises(Exception):
            await self.market_handler.get_market_overview('test_user')
    
    async def test_instrument_data_invalid_symbol(self):
        """تست endpoint داده‌های نماد با نماد نامعتبر"""
        with self.assertRaises(Exception):
            await self.market_handler.get_instrument_data('INVALID_SYMBOL_123', 'test_user')
    
    @patch('src.api.handlers.signal_handler.get_trading_signals')
    async def test_signals_generation_error(self, mock_signals):
        """تست خطا در تولید سیگنال"""
        # شبیه‌سازی خطا
        mock_signals.side_effect = Exception("Signal generation failed")
        
        with self.assertRaises(Exception):
            await self.signal_handler.get_trading_signals('test_user')

class TestAPIValidation(unittest.TestCase):
    """تست اعتبارسنجی در API"""
    
    def setUp(self):
        self.portfolio_handler = PortfolioHandler()
    
    async def test_portfolio_analysis_validation(self):
        """تست اعتبارسنجی داده‌های پرتفولیو"""
        invalid_portfolio_data = "invalid_data_string"
        
        with self.assertRaises(Exception):
            await self.portfolio_handler.analyze_portfolio(invalid_portfolio_data, 'test_user')
    
    async def test_optimal_allocation_validation(self):
        """تست اعتبارسنجی ترجیحات کاربر"""
        invalid_preferences = {
            'risk_tolerance': 'INVALID_RISK_LEVEL',
            'investment_horizon': 'INVALID_HORIZON'
        }
        
        # باید خطا مدیریت شود
        result = await self.portfolio_handler.get_optimal_allocation(invalid_preferences, 'test_user')
        self.assertEqual(result['status'], 'success')  # باید fallback به MODERATE کند

class TestAPIPerformance(unittest.TestCase):
    """تست عملکرد API"""
    
    def setUp(self):
        self.market_handler = MarketDataHandler()
    
    @patch('src.api.handlers.market_data_handler.get_market_overview')
    async def test_market_overview_performance(self, mock_overview):
        """تست عملکرد endpoint نمای کلی بازار"""
        import time
        
        # شبیه‌سازی پاسخ سریع
        mock_overview.return_value = {
            'status': 'success',
            'market_condition': 'NORMAL'
        }
        
        start_time = time.time()
        await self.market_handler.get_market_overview('test_user')
        execution_time = time.time() - start_time
        
        # باید در کمتر از ۲ ثانیه پاسخ دهد
        self.assertLess(execution_time, 2.0)

class TestAPIResponseFormat(unittest.TestCase):
    """تست فرمت پاسخ‌های API"""
    
    def setUp(self):
        self.signal_handler = SignalHandler()
    
    @patch('src.api.handlers.signal_handler.get_trading_signals')
    async def test_signals_response_format(self, mock_signals):
        """تست فرمت پاسخ سیگنال‌ها"""
        # شبیه‌سازی پاسخ
        mock_signals.return_value = {
            'status': 'success',
            'total_signals': 1,
            'generated_at': '2024-01-01T00:00:00Z',
            'signals': [
                {
                    'symbol': 'EUR/USD',
                    'type': 'BUY_LIMIT',
                    'entry': 1.0850,
                    'stop_loss': 1.0820,
                    'take_profits': [1.0870, 1.0890, 1.0910],
                    'confidence': 0.82,
                    'timeframe': '15m'
                }
            ]
        }
        
        result = await self.signal_handler.get_trading_signals('test_user')
        
        # بررسی ساختار پاسخ
        self.assertEqual(result['status'], 'success')
        self.assertIn('total_signals', result)
        self.assertIn('generated_at', result)
        self.assertIn('signals', result)
        
        # بررسی ساختار سیگنال
        if result['signals']:
            signal = result['signals'][0]
            required_fields = ['symbol', 'type', 'entry', 'stop_loss', 'take_profits', 'confidence', 'timeframe']
            for field in required_fields:
                self.assertIn(field, signal)

def run_api_tests():
    """اجرای تمام تست‌های API"""
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestAPIEndpoints)
    suite.addTests(loader.loadTestsFromTestCase(TestAPIErrorHandling))
    suite.addTests(loader.loadTestsFromTestCase(TestAPIValidation))
    suite.addTests(loader.loadTestsFromTestCase(TestAPIPerformance))
    suite.addTests(loader.loadTestsFromTestCase(TestAPIResponseFormat))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

if __name__ == '__main__':
    # اجرای تست‌های API
    success = run_api_tests()
    sys.exit(0 if success else 1)
