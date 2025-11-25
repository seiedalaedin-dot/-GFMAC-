#!/usr/bin/env python3
"""
Technical Indicators Module
Advanced Technical Analysis Calculations
Developer: Seyed Aladdin Mousavi Jashni
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
import logging
from enum import Enum

class IndicatorType(Enum):
    """انواع اندیکاتورهای تکنیکال"""
    TREND = "trend"
    MOMENTUM = "momentum"
    VOLATILITY = "volatility"
    VOLUME = "volume"

class TechnicalIndicators:
    """محاسبه‌گر اندیکاتورهای تکنیکال پیشرفته"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def calculate_all_indicators(self, df: pd.DataFrame) -> Dict:
        """
        محاسبه کلیه اندیکاتورهای تکنیکال
        
        Args:
            df: DataFrame شامل ستون‌های ['Close', 'High', 'Low', 'Volume']
            
        Returns:
            Dict: تمام اندیکاتورهای محاسبه شده
        """
        try:
            indicators = {}
            
            # اندیکاتورهای روند
            indicators.update(self._calculate_trend_indicators(df))
            
            # اندیکاتورهای مومنتوم
            indicators.update(self._calculate_momentum_indicators(df))
            
            # اندیکاتورهای نوسان
            indicators.update(self._calculate_volatility_indicators(df))
            
            # اندیکاتورهای حجم
            indicators.update(self._calculate_volume_indicators(df))
            
            return indicators
            
        except Exception as e:
            self.logger.error(f"Error calculating indicators: {e}")
            return {}
    
    def _calculate_trend_indicators(self, df: pd.DataFrame) -> Dict:
        """محاسبه اندیکاتورهای روند"""
        indicators = {}
        
        # Moving Averages
        indicators['sma_20'] = self.sma(df['Close'], 20)
        indicators['sma_50'] = self.sma(df['Close'], 50)
        indicators['sma_200'] = self.sma(df['Close'], 200)
        
        indicators['ema_12'] = self.ema(df['Close'], 12)
        indicators['ema_26'] = self.ema(df['Close'], 26)
        
        # Parabolic SAR
        indicators['parabolic_sar'] = self.parabolic_sar(df)
        
        # Ichimoku Cloud
        ichimoku = self.ichimoku_cloud(df)
        indicators.update(ichimoku)
        
        return indicators
    
    def _calculate_momentum_indicators(self, df: pd.DataFrame) -> Dict:
        """محاسبه اندیکاتورهای مومنتوم"""
        indicators = {}
        
        # RSI
        indicators['rsi'] = self.rsi(df['Close'], 14)
        
        # MACD
        macd_line, signal_line, histogram = self.macd(df['Close'])
        indicators['macd_line'] = macd_line
        indicators['macd_signal'] = signal_line
        indicators['macd_histogram'] = histogram
        
        # Stochastic
        indicators['stochastic_k'] = self.stochastic(df, 14)
        indicators['stochastic_d'] = self.sma(indicators['stochastic_k'], 3)
        
        # Williams %R
        indicators['williams_r'] = self.williams_r(df, 14)
        
        # CCI
        indicators['cci'] = self.cci(df, 20)
        
        return indicators
    
    def _calculate_volatility_indicators(self, df: pd.DataFrame) -> Dict:
        """محاسبه اندیکاتورهای نوسان"""
        indicators = {}
        
        # Bollinger Bands
        bb_upper, bb_middle, bb_lower = self.bollinger_bands(df['Close'], 20)
        indicators['bb_upper'] = bb_upper
        indicators['bb_middle'] = bb_middle
        indicators['bb_lower'] = bb_lower
        indicators['bb_width'] = (bb_upper - bb_lower) / bb_middle
        
        # Average True Range (ATR)
        indicators['atr'] = self.atr(df, 14)
        
        # Keltner Channel
        kc_upper, kc_middle, kc_lower = self.keltner_channel(df, 20)
        indicators['kc_upper'] = kc_upper
        indicators['kc_middle'] = kc_middle
        indicators['kc_lower'] = kc_lower
        
        return indicators
    
    def _calculate_volume_indicators(self, df: pd.DataFrame) -> Dict:
        """محاسبه اندیکاتورهای حجم"""
        indicators = {}
        
        # On-Balance Volume (OBV)
        indicators['obv'] = self.obv(df['Close'], df['Volume'])
        
        # Volume Weighted Average Price (VWAP)
        indicators['vwap'] = self.vwap(df)
        
        # Accumulation/Distribution Line
        indicators['ad_line'] = self.accumulation_distribution(df)
        
        # Chaikin Money Flow
        indicators['cmf'] = self.chaikin_money_flow(df, 20)
        
        return indicators
    
    # ===== IMPLEMENTATION OF INDICATORS =====
    
    def sma(self, prices: pd.Series, period: int) -> pd.Series:
        """میانگین متحرک ساده"""
        return prices.rolling(window=period).mean()
    
    def ema(self, prices: pd.Series, period: int) -> pd.Series:
        """میانگین متحرک نمایی"""
        return prices.ewm(span=period, adjust=False).mean()
    
    def rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """شاخص قدرت نسبی"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def macd(self, prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple:
        """MACD"""
        ema_fast = self.ema(prices, fast)
        ema_slow = self.ema(prices, slow)
        macd_line = ema_fast - ema_slow
        signal_line = self.ema(macd_line, signal)
        histogram = macd_line - signal_line
        return macd_line, signal_line, histogram
    
    def bollinger_bands(self, prices: pd.Series, period: int = 20, std_dev: int = 2) -> Tuple:
        """باندهای بولینگر"""
        sma = self.sma(prices, period)
        std = prices.rolling(window=period).std()
        upper_band = sma + (std * std_dev)
        lower_band = sma - (std * std_dev)
        return upper_band, sma, lower_band
    
    def stochastic(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """استوکاستیک"""
        low_min = df['Low'].rolling(window=period).min()
        high_max = df['High'].rolling(window=period).max()
        k = 100 * ((df['Close'] - low_min) / (high_max - low_min))
        return k
    
    def williams_r(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """ویلیامز %R"""
        high_max = df['High'].rolling(window=period).max()
        low_min = df['Low'].rolling(window=period).min()
        williams_r = -100 * ((high_max - df['Close']) / (high_max - low_min))
        return williams_r
    
    def cci(self, df: pd.DataFrame, period: int = 20) -> pd.Series:
        """شاخص کانال کالا"""
        tp = (df['High'] + df['Low'] + df['Close']) / 3
        sma_tp = self.sma(tp, period)
        mad = tp.rolling(window=period).apply(lambda x: np.mean(np.abs(x - np.mean(x))))
        cci = (tp - sma_tp) / (0.015 * mad)
        return cci
    
    def atr(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """میانگین محدوده واقعی"""
        high_low = df['High'] - df['Low']
        high_close = np.abs(df['High'] - df['Close'].shift())
        low_close = np.abs(df['Low'] - df['Close'].shift())
        true_range = np.maximum(high_low, np.maximum(high_close, low_close))
        atr = true_range.rolling(window=period).mean()
        return atr
    
    def parabolic_sar(self, df: pd.DataFrame, acceleration: float = 0.02, maximum: float = 0.2) -> pd.Series:
        """Parabolic SAR"""
        high = df['High'].values
        low = df['Low'].values
        close = df['Close'].values
        
        sar = np.zeros(len(close))
        trend = np.zeros(len(close))
        ep = np.zeros(len(close))
        af = np.zeros(len(close))
        
        # Initialize
        sar[0] = high[0] if close[0] < close[1] else low[0]
        trend[0] = 1 if close[0] > close[1] else -1
        ep[0] = high[0] if trend[0] == 1 else low[0]
        af[0] = acceleration
        
        for i in range(1, len(close)):
            # Update SAR
            sar[i] = sar[i-1] + af[i-1] * (ep[i-1] - sar[i-1])
            
            # Check for trend reversal
            if trend[i-1] == 1:
                if low[i] < sar[i]:
                    trend[i] = -1
                    sar[i] = ep[i-1]
                    ep[i] = low[i]
                    af[i] = acceleration
                else:
                    trend[i] = 1
                    if high[i] > ep[i-1]:
                        ep[i] = high[i]
                        af[i] = min(af[i-1] + acceleration, maximum)
                    else:
                        ep[i] = ep[i-1]
                        af[i] = af[i-1]
            else:
                if high[i] > sar[i]:
                    trend[i] = 1
                    sar[i] = ep[i-1]
                    ep[i] = high[i]
                    af[i] = acceleration
                else:
                    trend[i] = -1
                    if low[i] < ep[i-1]:
                        ep[i] = low[i]
                        af[i] = min(af[i-1] + acceleration, maximum)
                    else:
                        ep[i] = ep[i-1]
                        af[i] = af[i-1]
        
        return pd.Series(sar, index=df.index)
    
    def ichimoku_cloud(self, df: pd.DataFrame) -> Dict:
        """ابر ایچیموکو"""
        high = df['High']
        low = df['Low']
        
        # Tenkan-sen (Conversion Line)
        tenkan_sen = (high.rolling(window=9).max() + low.rolling(window=9).min()) / 2
        
        # Kijun-sen (Base Line)
        kijun_sen = (high.rolling(window=26).max() + low.rolling(window=26).min()) / 2
        
        # Senkou Span A (Leading Span A)
        senkou_span_a = ((tenkan_sen + kijun_sen) / 2).shift(26)
        
        # Senkou Span B (Leading Span B)
        senkou_span_b = ((high.rolling(window=52).max() + low.rolling(window=52).min()) / 2).shift(26)
        
        # Chikou Span (Lagging Span)
        chikou_span = df['Close'].shift(-26)
        
        return {
            'ichimoku_tenkan': tenkan_sen,
            'ichimoku_kijun': kijun_sen,
            'ichimoku_senkou_a': senkou_span_a,
            'ichimoku_senkou_b': senkou_span_b,
            'ichimoku_chikou': chikou_span
        }
    
    def keltner_channel(self, df: pd.DataFrame, period: int = 20, multiplier: float = 2) -> Tuple:
        """کانال کلتنر"""
        ema = self.ema(df['Close'], period)
        atr = self.atr(df, period)
        upper = ema + (multiplier * atr)
        lower = ema - (multiplier * atr)
        return upper, ema, lower
    
    def obv(self, close: pd.Series, volume: pd.Series) -> pd.Series:
        """حجم موجودی تراز"""
        obv = np.zeros(len(close))
        obv[0] = volume.iloc[0]
        
        for i in range(1, len(close)):
            if close.iloc[i] > close.iloc[i-1]:
                obv[i] = obv[i-1] + volume.iloc[i]
            elif close.iloc[i] < close.iloc[i-1]:
                obv[i] = obv[i-1] - volume.iloc[i]
            else:
                obv[i] = obv[i-1]
        
        return pd.Series(obv, index=close.index)
    
    def vwap(self, df: pd.DataFrame) -> pd.Series:
        """قیمت متوسط وزنی حجم"""
        typical_price = (df['High'] + df['Low'] + df['Close']) / 3
        vwap = (typical_price * df['Volume']).cumsum() / df['Volume'].cumsum()
        return vwap
    
    def accumulation_distribution(self, df: pd.DataFrame) -> pd.Series:
        """خط توزیع/تجمع"""
        clv = ((df['Close'] - df['Low']) - (df['High'] - df['Close'])) / (df['High'] - df['Low'])
        clv = clv.replace([np.inf, -np.inf], 0).fillna
