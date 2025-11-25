#!/usr/bin/env python3
"""
API Handlers Module
Request Handlers and Business Logic
Developer: Seyed Aladdin Mousavi Jashni
"""

import logging
from typing import Dict, List, Optional
from fastapi import HTTPException, status
import asyncio

from src.core.crisis_analyzer import crisis_analyzer
from src.core.monte_carlo import monte_carlo_engine
from src.core.signal_generator import signal_generator
from src.data.market_data import market_data_manager
from src.security.auth_manager import auth_manager
from src.security.session_manager import session_manager
from src.utils.validator import data_validator

class MarketDataHandler:
    """Handler برای مدیریت داده‌های بازار"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def get_market_overview(self, user_id: str) -> Dict:
        """دریافت نمای کلی بازار"""
        try:
            self.logger.info(f"📊 Fetching market overview for user {user_id}")
            
            # دریافت داده‌های بازار
            market_data = await market_data_manager.get_all_market_data()
            
            # تحلیل بحران
            crisis_report = await crisis_analyzer.analyze(market_data)
            
            # تحلیل ریسک
            risk_assessment = await monte_carlo_engine.analyze_portfolio_risk(market_data)
            
            return {
                'status': 'success',
                'timestamp': market_data['timestamp'],
                'market_condition': crisis_report.get('market_condition', 'UNKNOWN'),
                'crisis_score': crisis_report.get('crisis_score', 0),
                'risk_level': risk_assessment.get('risk_metrics', {}).get('var_95', 0),
                'active_instruments': {
                    'forex': len(market_data.get('forex', {})),
                    'crypto': len(market_data.get('crypto', {})),
                    'indices': len(market_data.get('indices', {})),
                    'metals': len(market_data.get('metals', {}))
                },
                'alerts': self._generate_market_alerts(crisis_report, risk_assessment)
            }
            
        except Exception as e:
            self.logger.error(f"❌ Market overview failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch market overview"
            )
    
    async def get_instrument_data(self, symbol: str, user_id: str) -> Dict:
        """دریافت داده‌های یک نماد خاص"""
        try:
            self.logger.info(f"📈 Fetching data for {symbol} for user {user_id}")
            
            # اعتبارسنجی نماد
            if not data_validator._validate_symbol(symbol, 'any'):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid symbol format"
                )
            
            # دریافت داده‌های بازار
            market_data = await market_data_manager.get_all_market_data()
            
            # پیدا کردن نماد در داده‌های بازار
            instrument_data = None
            for market_type in ['forex', 'crypto', 'indices', 'metals']:
                if symbol in market_data.get(market_type, {}):
                    instrument_data = market_data[market_type][symbol]
                    instrument_data['market_type'] = market_type
                    break
            
            if not instrument_data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Instrument {symbol} not found"
                )
            
            # تحلیل تکنیکال
            historical_data = await market_data_manager.get_historical_data(symbol, "1mo")
            
            return {
                'status': 'success',
                'symbol': symbol,
                'current_data': instrument_data,
                'market_type': instrument_data.get('market_type'),
                'historical_summary': self._summarize_historical_data(historical_data)
            }
            
        except HTTPException:
            raise
        except Exception as e:
            self.logger.error(f"❌ Instrument data fetch failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch instrument data"
            )
    
    async def get_economic_calendar(self, user_id: str, days: int = 7) -> Dict:
        """دریافت تقویم اقتصادی"""
        try:
            self.logger.info(f"📅 Fetching economic calendar for {days} days for user {user_id}")
            
            events = await market_data_manager.get_economic_calendar()
            
            # فیلتر کردن رویدادهای آینده
            import datetime
            future_events = [
                event for event in events 
                if event.get('timestamp') and 
                datetime.datetime.fromisoformat(event['timestamp'].replace('Z', '+00:00')) > datetime.datetime.now()
            ]
            
            return {
                'status': 'success',
                'days': days,
                'total_events': len(future_events),
                'events': future_events[:days*10]  # حداکثر ۱۰ رویداد در روز
            }
            
        except Exception as e:
            self.logger.error(f"❌ Economic calendar fetch failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch economic calendar"
            )
    
    def _generate_market_alerts(self, crisis_report: Dict, risk_assessment: Dict) -> List[Dict]:
        """تولید هشدارهای بازار"""
        alerts = []
        
        # هشدارهای بحران
        crisis_score = crisis_report.get('crisis_score', 0)
        if crisis_score > 0.7:
            alerts.append({
                'level': 'HIGH',
                'type': 'CRISIS',
                'message': 'High crisis probability detected',
                'score': crisis_score
            })
        elif crisis_score > 0.4:
            alerts.append({
                'level': 'MEDIUM', 
                'type': 'RISK',
                'message': 'Elevated market risk',
                'score': crisis_score
            })
        
        # هشدارهای ریسک
        var_95 = risk_assessment.get('risk_metrics', {}).get('var_95', 0)
        if var_95 < -0.1:
            alerts.append({
                'level': 'HIGH',
                'type': 'RISK',
                'message': 'High portfolio risk detected',
                'var_95': var_95
            })
        
        return alerts
    
    def _summarize_historical_data(self, historical_data) -> Dict:
        """خلاصه‌سازی داده‌های تاریخی"""
        if historical_data.empty:
            return {}
        
        return {
            'period_days': len(historical_data),
            'price_change': historical_data['Close'].iloc[-1] - historical_data['Close'].iloc[0],
            'price_change_percent': ((historical_data['Close'].iloc[-1] - historical_data['Close'].iloc[0]) / historical_data['Close'].iloc[0]) * 100,
            'volatility': historical_data['Close'].std(),
            'average_volume': historical_data['Volume'].mean()
        }

class SignalHandler:
    """Handler برای مدیریت سیگنال‌های معاملاتی"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def get_trading_signals(self, user_id: str, filters: Dict = None) -> Dict:
        """دریافت سیگنال‌های معاملاتی"""
        try:
            self.logger.info(f"📈 Generating trading signals for user {user_id}")
            
            # دریافت داده‌های بازار
            market_data = await market_data_manager.get_all_market_data()
            
            # تولید سیگنال‌ها
            signals = await signal_generator.generate_signals(market_data)
            
            # اعمال فیلترها
            if filters:
                signals = self._apply_signal_filters(signals, filters)
            
            return {
                'status': 'success',
                'total_signals': len(signals),
                'generated_at': market_data['timestamp'],
                'signals': signals[:20]  # محدود کردن تعداد سیگنال‌ها
            }
            
        except Exception as e:
            self.logger.error(f"❌ Signal generation failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate trading signals"
            )
    
    async def get_signal_analysis(self, symbol: str, user_id: str) -> Dict:
        """دریافت تحلیل دقیق برای یک نماد"""
        try:
            self.logger.info(f"🔍 Analyzing signals for {symbol} for user {user_id}")
            
            # اعتبارسنجی نماد
            if not data_validator._validate_symbol(symbol, 'any'):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid symbol format"
                )
            
            # دریافت داده‌های بازار
            market_data = await market_data_manager.get_all_market_data()
            
            # تولید سیگنال‌های خاص برای این نماد
            symbol_data = None
            for market_type in ['forex', 'crypto', 'indices', 'metals']:
                if symbol in market_data.get(market_type, {}):
                    symbol_data = {symbol: market_data[market_type][symbol]}
                    break
            
            if not symbol_data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Instrument {symbol} not found"
                )
            
            # تحلیل بحران برای این نماد
            crisis_report = await crisis_analyzer.analyze(market_data)
            
            # تحلیل ریسک
            risk_assessment = await monte_carlo_engine.analyze_portfolio_risk(
                {**market_data, **symbol_data}
            )
            
            return {
                'status': 'success',
                'symbol': symbol,
                'current_price': symbol_data[symbol].get('price'),
                'crisis_impact': self._get_crisis_impact(symbol, crisis_report),
                'risk_assessment': risk_assessment.get('risk_metrics', {}),
                'recommendation': self._generate_recommendation(symbol_data[symbol], risk_assessment)
            }
            
        except HTTPException:
            raise
        except Exception as e:
            self.logger.error(f"❌ Signal analysis failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to analyze signals"
            )
    
    def _apply_signal_filters(self, signals: List[Dict], filters: Dict) -> List[Dict]:
        """اعمال فیلترها روی سیگنال‌ها"""
        filtered_signals = signals
        
        # فیلتر بر اساس اطمینان
        if 'min_confidence' in filters:
            filtered_signals = [
                s for s in filtered_signals 
                if s.get('confidence', 0) >= filters['min_confidence']
            ]
        
        # فیلتر بر اساس نوع دارایی
        if 'asset_types' in filters:
            filtered_signals = [
                s for s in filtered_signals 
                if s.get('asset_type') in filters['asset_types']
            ]
        
        # فیلتر بر اساس تایم‌فریم
        if 'timeframes' in filters:
            filtered_signals = [
                s for s in filtered_signals 
                if s.get('timeframe') in filters['timeframes']
            ]
        
        return filtered_signals
    
    def _get_crisis_impact(self, symbol: str, crisis_report: Dict) -> Dict:
        """دریافت تأثیر بحران روی نماد"""
        # این تحلیل باید بر اساس نوع نماد و سناریوهای بحران باشد
        return {
            'impact_level': 'MEDIUM',
            'scenarios_affected': ['
