#!/usr/bin/env python3
"""
Signal Generator Core Module
Advanced Trading Signal Generation
Developer: Seyed Aladdin Mousavi Jashni
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from enum import Enum

from config import config

class SignalType(Enum):
    """انواع سیگنال‌های معاملاتی"""
    BUY_LIMIT = "BUY_LIMIT"
    SELL_LIMIT = "SELL_LIMIT" 
    BUY_STOP = "BUY_STOP"
    SELL_STOP = "SELL_STOP"
    BUY_MARKET = "BUY_MARKET"
    SELL_MARKET = "SELL_MARKET"

class TimeFrame(Enum):
    """تایم‌فریم‌های معاملاتی"""
    M15 = "15m"
    H1 = "1h"
    H4 = "4h"
    D1 = "1d"
    W1 = "1w"

class SignalGenerator:
    """تولیدکننده سیگنال‌های معاملاتی پیشرفته"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.signals_generated = 0
        self.performance_history = []
        
        # تنظیمات سیگنال‌دهی
        self.signal_config = {
            'min_confidence': config.SIGNAL_SETTINGS['MIN_CONFIDENCE'],
            'max_signals_per_day': 20,
            'risk_reward_ratio': 1.5,
            'position_sizing': 0.02  # 2% از سرمایه per trade
        }
    
    async def initialize(self):
        """مقداردهی اولیه تولیدکننده سیگنال"""
        self.logger.info("📈 Initializing Signal Generator...")
        self.logger.info(f"🎯 Minimum confidence: {self.signal_config['min_confidence']}")
        self.logger.info(f"📊 Supported timeframes: {[tf.value for tf in TimeFrame]}")
        self.logger.info(f"💰 Position sizing: {self.signal_config['position_sizing']*100}%")
    
    async def generate_signals(self, market_data: Dict) -> List[Dict]:
        """
        تولید سیگنال‌های معاملاتی بر اساس تحلیل بازار
        
        Args:
            market_data: داده‌های بازار
            
        Returns:
            List[Dict]: لیست سیگنال‌های تولید شده
        """
        try:
            self.logger.info("🔍 Generating trading signals...")
            
            all_signals = []
            
            # تولید سیگنال برای فارکس
            forex_signals = await self._generate_forex_signals(market_data.get('forex', {}))
            all_signals.extend(forex_signals)
            
            # تولید سیگنال برای کریپتو
            crypto_signals = await self._generate_crypto_signals(market_data.get('crypto', {}))
            all_signals.extend(crypto_signals)
            
            # تولید سیگنال برای فلزات گرانبها
            metals_signals = await self._generate_metals_signals(market_data.get('metals', {}))
            all_signals.extend(metals_signals)
            
            # تولید سیگنال برای شاخص‌ها
            indices_signals = await self._generate_indices_signals(market_data.get('indices', {}))
            all_signals.extend(indices_signals)
            
            # فیلتر کردن سیگنال‌های با اطمینان پایین
            filtered_signals = self._filter_signals_by_confidence(all_signals)
            
            # محدود کردن تعداد سیگنال‌ها
            final_signals = filtered_signals[:self.signal_config['max_signals_per_day']]
            
            self.signals_generated += len(final_signals)
            self.logger.info(f"✅ Generated {len(final_signals)} trading signals")
            
            return final_signals
            
        except Exception as e:
            self.logger.error(f"❌ Signal generation failed: {e}")
            return []
    
    async def _generate_forex_signals(self, forex_data: Dict) -> List[Dict]:
        """تولید سیگنال برای جفت ارزهای فارکس"""
        signals = []
        
        for symbol, data in forex_data.items():
            try:
                current_price = data.get('price')
                if current_price is None:
                    continue
                
                # تحلیل تکنیکال
                tech_analysis = await self._technical_analysis(symbol, current_price, 'forex')
                
                # تحلیل بنیادی (اخبار اقتصادی)
                fundamental_analysis = await self._fundamental_analysis(symbol, 'forex')
                
                # تولید سیگنال‌های مختلف
                intraday_signal = await self._generate_intraday_signal(
                    symbol, current_price, tech_analysis, fundamental_analysis, 'forex'
                )
                if intraday_signal:
                    signals.append(intraday_signal)
                
                swing_signal = await self._generate_swing_signal(
                    symbol, current_price, tech_analysis, fundamental_analysis, 'forex'
                )
                if swing_signal:
                    signals.append(swing_signal)
                    
            except Exception as e:
                self.logger.error(f"Error generating signal for {symbol}: {e}")
                continue
        
        return signals
    
    async def _generate_crypto_signals(self, crypto_data: Dict) -> List[Dict]:
        """تولید سیگنال برای ارزهای دیجیتال"""
        signals = []
        
        for symbol, data in crypto_data.items():
            try:
                current_price = data.get('price')
                if current_price is None:
                    continue
                
                # تحلیل تکنیکال
                tech_analysis = await self._technical_analysis(symbol, current_price, 'crypto')
                
                # تحلیل روی‌زنجیره (on-chain)
                onchain_analysis = await self._onchain_analysis(symbol)
                
                # تولید سیگنال
                crypto_signal = await self._generate_crypto_specific_signal(
                    symbol, current_price, tech_analysis, onchain_analysis
                )
                if crypto_signal:
                    signals.append(crypto_signal)
                    
            except Exception as e:
                self.logger.error(f"Error generating signal for {symbol}: {e}")
                continue
        
        return signals
    
    async def _generate_metals_signals(self, metals_data: Dict) -> List[Dict]:
        """تولید سیگنال برای فلزات گرانبها"""
        signals = []
        
        for symbol, data in metals_data.items():
            try:
                current_price = data.get('price')
                if current_price is None:
                    continue
                
                # تحلیل تکنیکال
                tech_analysis = await self._technical_analysis(symbol, current_price, 'metals')
                
                # تحلیل بنیادی (عرضه و تقاضا)
                fundamental_analysis = await self._metals_fundamental_analysis(symbol)
                
                # تولید سیگنال
                metal_signal = await self._generate_metal_specific_signal(
                    symbol, current_price, tech_analysis, fundamental_analysis
                )
                if metal_signal:
                    signals.append(metal_signal)
                    
            except Exception as e:
                self.logger.error(f"Error generating signal for {symbol}: {e}")
                continue
        
        return signals
    
    async def _generate_indices_signals(self, indices_data: Dict) -> List[Dict]:
        """تولید سیگنال برای شاخص‌های سهام"""
        signals = []
        
        for symbol, data in indices_data.items():
            try:
                current_price = data.get('price')
                if current_price is None:
                    continue
                
                # تحلیل تکنیکال
                tech_analysis = await self._technical_analysis(symbol, current_price, 'indices')
                
                # تحلیل اقتصادی کلان
                macroeconomic_analysis = await self._macroeconomic_analysis(symbol)
                
                # تولید سیگنال
                index_signal = await self._generate_index_specific_signal(
                    symbol, current_price, tech_analysis, macroeconomic_analysis
                )
                if index_signal:
                    signals.append(index_signal)
                    
            except Exception as e:
                self.logger.error(f"Error generating signal for {symbol}: {e}")
                continue
        
        return signals
    
    async def _generate_intraday_signal(self, symbol: str, current_price: float,
                                      tech_analysis: Dict, fundamental_analysis: Dict,
                                      asset_type: str) -> Optional[Dict]:
        """تولید سیگنال معاملاتی Intraday (15 دقیقه)"""
        try:
            # تحلیل ترکیبی برای سیگنال کوتاه‌مدت
            confidence = await self._calculate_intraday_confidence(
                tech_analysis, fundamental_analysis
            )
            
            if confidence < self.signal_config['min_confidence']:
                return None
            
            # تعیین نوع و پارامترهای سیگنال
            signal_type, entry, stop_loss, take_profits = await self._calculate_intraday_parameters(
                symbol, current_price, tech_analysis, confidence
            )
            
            signal = {
                'symbol': symbol,
                'asset_type': asset_type,
                'type': signal_type.value,
                'entry': entry,
                'stop_loss': stop_loss,
                'take_profits': take_profits,
                'timeframe': TimeFrame.M15.value,
                'confidence': confidence,
                'signal_strength': self._get_signal_strength(confidence),
                'timestamp': datetime.now().isoformat(),
                'expiry': (datetime.now() + timedelta(hours=4)).isoformat(),  # 4 hours expiry
                'risk_reward_ratio': self._calculate_risk_reward(entry, stop_loss, take_profits),
                'position_size': self.signal_config['position_sizing'],
                'analysis': {
                    'technical': tech_analysis,
                    'fundamental': fundamental_analysis
                }
            }
            
            return signal
            
        except Exception as e:
            self.logger.error(f"Error generating intraday signal for {symbol}: {e}")
            return None
    
    async def _generate_swing_signal(self, symbol: str, current_price: float,
                                   tech_analysis: Dict, fundamental_analysis: Dict,
                                   asset_type: str) -> Optional[Dict]:
        """تولید سیگنال معاملاتی Swing (4 ساعت)"""
        try:
            # تحلیل ترکیبی برای سیگنال میان‌مدت
            confidence = await self._calculate_swing_confidence(
                tech_analysis, fundamental_analysis
            )
            
            if confidence < self.signal_config['min_confidence']:
                return None
            
            # تعیین نوع و پارامترهای سیگنال
            signal_type, entry, stop_loss, take_profits = await self._calculate_swing_parameters(
                symbol, current_price, tech_analysis, confidence
            )
            
            signal = {
                'symbol': symbol,
                'asset_type': asset_type,
                'type': signal_type.value,
                'entry': entry,
                'stop_loss': stop_loss,
                'take_profits': take_profits,
                'timeframe': TimeFrame.H4.value,
                'confidence': confidence,
                'signal_strength': self._get_signal_strength(confidence),
                'timestamp': datetime.now().isoformat(),
                'expiry': (datetime.now() + timedelta(days=3)).isoformat(),  # 3 days expiry
                'risk_reward_ratio': self._calculate_risk_reward(entry, stop_loss, take_profits),
                'position_size': self.signal_config['position_sizing'],
                'analysis': {
                    'technical': tech_analysis,
                    'fundamental': fundamental_analysis
                }
            }
            
            return signal
            
        except Exception as e:
            self.logger.error(f"Error generating swing signal for {symbol}: {e}")
            return None
    
    async def _technical_analysis(self, symbol: str, current_price: float, 
                                asset_type: str) -> Dict:
        """انجام تحلیل تکنیکال"""
        # اینجا باید اندیکاتورهای واقعی محاسبه شوند
        # برای نمونه از مقادیر شبیه‌سازی استفاده می‌کنیم
        
        return {
            'rsi': np.random.uniform(30, 70),
            'macd': np.random.uniform(-0.01, 0.01),
            'bollinger_bands': {
                'upper': current_price * 1.02,
                'lower': current_price * 0.98,
                'middle': current_price
            },
            'support_levels': [current_price * 0.98, current_price * 0.96],
            'resistance_levels': [current_price * 1.02, current_price * 1.04],
            'trend': 'BULLISH' if np.random.random() > 0.5 else 'BEARISH',
            'momentum': np.random.uniform(-1, 1)
        }
    
    async def _fundamental_analysis(self, symbol: str, asset_type: str) -> Dict:
        """انجام تحلیل بنیادی"""
        return {
            'economic_calendar': [],
            'news_sentiment': np.random.uniform(-1, 1),
            'volatility_index': np.random.uniform(10, 30),
            'market_regime': 'NORMAL'
        }
    
    async def _onchain_analysis(self, symbol: str) -> Dict:
        """تحلیل روی‌زنجیره برای ارزهای دیجیتال"""
        return {
            'network_activity': np.random.uniform(0, 1),
            'exchange_flows': np.random.uniform(-1, 1),
            'holder_sentiment': np.random.uniform(0, 1),
            'mining_activity': np.random.uniform(0, 1)
        }
    
    async def _calculate_intraday_confidence(self, tech_analysis: Dict, 
                                           fundamental_analysis: Dict) -> float:
        """محاسبه اطمینان برای سیگنال Intraday"""
        # ترکیب عوامل مختلف برای محاسبه اطمینان
        tech_score = self._calculate_technical_score(tech_analysis)
        fundamental_score = self._calculate_fundamental_score(fundamental_analysis)
        
        # وزن بیشتر به تحلیل تکنیکال در تایم‌فریم کوتاه
        confidence = (tech_score * 0.7 + fundamental_score * 0.3)
        return max(0.0, min(1.0, confidence))
    
    async def _calculate_swing_confidence(self, tech_analysis: Dict, 
                                        fundamental_analysis: Dict) -> float:
        """محاسبه اطمینان برای سیگنال Swing"""
        # ترکیب عوامل مختلف برای محاسبه اطمینان
        tech_score = self._calculate_technical_score(tech_analysis)
        fundamental_score = self._calculate_fundamental_score(fundamental_analysis)
        
        # وزن متعادل برای تایم‌فریم میان‌مدت
        confidence = (tech_score * 0.5 + fundamental_score * 0.5)
        return max(0.0, min(1.0, confidence))
    
    def _calculate_technical_score(self, tech_analysis: Dict) -> float:
        """محاسبه امتیاز تحلیل تکنیکال"""
        # ترکیب اندیکاتورهای مختلف
        rsi_score = 1 - abs(tech_analysis.get('rsi', 50) - 50) / 50
        trend_score = 1.0 if tech_analysis.get('trend') == 'BULLISH' else 0.0
        momentum_score = (tech_analysis.get('momentum', 0) + 1) / 2
        
        return (rsi_score + trend_score + momentum_score) / 3
    
    def _calculate_fundamental_score(self, fundamental_analysis: Dict) -> float:
        """محاسبه امتیاز تحلیل بنیادی"""
        sentiment = (fundamental_analysis.get('news_sentiment', 0) + 1) / 2
        volatility = 1 - (fundamental_analysis.get('volatility_index', 20) - 10) / 20
        
        return (sentiment + volatility) / 2
    
    async def _calculate_intraday_parameters(self, symbol: str, current_price: float,
                                           tech_analysis: Dict, confidence: float) -> Tuple:
        """محاسبه پارامترهای سیگنال Intraday"""
        # تعیین جهت معامله بر اساس تحلیل
        if tech_analysis.get('trend') == 'BULLISH':
            signal_type = SignalType.BUY_LIMIT
            entry = current_price * 0.995  # 0.5% below current
            stop_loss = current_price * 0.985  # 1.5% below entry
            take_profits = [
                current_price * 1.005,  # 0.5% profit
                current_price * 1.010,  # 1.0% profit
                current_price * 1.015   # 1.5% profit
            ]
        else:
            signal_type = SignalType.SELL_LIMIT
            entry = current_price * 1.005  # 0.5% above current
            stop_loss = current_price * 1.015  # 1.5% above entry
            take_profits = [
                current_price * 0.995,  # 0.5% profit
                current_price * 0.990,  # 1.0% profit
                current_price * 0.985   # 1.5% profit
            ]
        
        return signal_type, round(entry, 5), round(stop_loss, 5), [round(tp, 5) for tp in take_profits]
    
    async def _calculate_swing_parameters(self, symbol: str, current_price: float,
                                        tech_analysis: Dict, confidence: float) -> Tuple:
        """محاسبه پارامترهای سیگنال Swing"""
        # تعیین جهت معامله بر اساس تحلیل
        if tech_analysis.get('trend') == 'BULLISH':
            signal_type = SignalType.BUY_STOP
            entry = current_price * 1.005  # 0.5% above current
            stop_loss = current_price * 0.98  # 2.5% below entry
            take_profits = [
                current_price * 1.02,  # 1.5% profit
                current_price * 1.035,  # 3.0% profit
                current_price * 1.05   # 4.5% profit
            ]
        else:
            signal_type = SignalType.SELL_STOP
            entry = current_price * 0.995  # 0.5% below current
            stop_loss = current_price * 1.02  # 2.5% above entry
            take_profits = [
                current_price * 0.98,  # 1.5% profit
                current_price * 0.965,  # 3.0% profit
                current_price * 0.95   # 4.5% profit
            ]
        
        return signal_type, round(entry, 5), round(stop_loss, 5), [round(tp, 5) for tp in take_profits]
    
    def _get_signal_strength(self, confidence: float) -> str:
        """تعیین قدرت سیگنال بر اساس اطمینان"""
        if confidence >= 0.8:
            return "STRONG"
        elif confidence >= 0.6:
            return "MEDIUM"
        else:
            return "WEAK"
    
    def _calculate_risk_reward(self, entry: float, stop_loss: float, take_profits: List[float]) -> float:
        """محاسبه نسبت ریسک به ریوارد"""
        risk = abs(entry - stop_loss)
        avg_reward = np.mean([abs(tp - entry) for tp in take_profits])
        return avg_reward / risk if risk > 0 else 0
    
    def _filter_signals_by_confidence(self, signals: List[Dict]) -> List[Dict]:
        """فیلتر کردن سیگنال‌ها بر اساس اطمینان"""
        return [signal for signal in signals if signal['confidence'] >= self.signal_config['min_confidence']]
    
    async def cleanup(self):
        """پاک‌سازی منابع"""
        self.logger.info("🧹 Cleaning up Signal Generator resources...")
        self.performance_history.clear()

# نمونه سینگلتون برای استفاده در سراسر سیستم
signal_generator = SignalGenerator()
