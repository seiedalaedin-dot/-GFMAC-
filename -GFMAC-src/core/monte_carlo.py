#!/usr/bin/env python3
"""
Monte Carlo Simulation Engine
Advanced Financial Risk Analysis
Developer: Seyed Aladdin Mousavi Jashni
"""

import asyncio
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import scipy.stats as stats

from config import config

class MonteCarloEngine:
    """موتور شبیه‌سازی مونت کارلو برای تحلیل ریسک"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.simulation_count = config.MONTE_CARLO['SIMULATION_COUNT']
        self.confidence_levels = config.MONTE_CARLO['CONFIDENCE_LEVELS']
        self.time_horizon = config.MONTE_CARLO['TIME_HORIZON']
        self.risk_free_rate = 0.02  # نرخ سود بدون ریسک
        
        # ذخیره نتایج شبیه‌سازی
        self.simulation_results = {}
        self.correlation_matrices = {}
        
    async def initialize(self):
        """مقداردهی اولیه موتور مونت کارلو"""
        self.logger.info("🎯 Initializing Monte Carlo Engine...")
        self.logger.info(f"📊 Simulation count: {self.simulation_count:,}")
        self.logger.info(f"📈 Time horizon: {self.time_horizon} days")
        self.logger.info(f"🎯 Confidence levels: {self.confidence_levels}")
    
    async def analyze_portfolio_risk(self, market_data: Dict) -> Dict:
        """
        تحلیل ریسک پرتفولیو با شبیه‌سازی مونت کارلو
        
        Args:
            market_data: داده‌های بازار
            
        Returns:
            Dict: نتایج تحلیل ریسک
        """
        try:
            self.logger.info("🔍 Starting Monte Carlo portfolio analysis...")
            
            # محاسبه ماتریس همبستگی
            correlation_matrix = await self._calculate_correlation_matrix(market_data)
            
            # شبیه‌سازی پرتفولیو
            portfolio_simulations = await self._simulate_portfolio(
                market_data, correlation_matrix
            )
            
            # محاسبه معیارهای ریسک
            risk_metrics = await self._calculate_risk_metrics(portfolio_simulations)
            
            # تحلیل سناریوهای بحران
            crisis_scenarios = await self._analyze_crisis_scenarios(portfolio_simulations)
            
            results = {
                "timestamp": datetime.now().isoformat(),
                "risk_metrics": risk_metrics,
                "crisis_scenarios": crisis_scenarios,
                "portfolio_simulation": {
                    "mean_final_value": np.mean(portfolio_simulations),
                    "median_final_value": np.median(portfolio_simulations),
                    "std_final_value": np.std(portfolio_simulations)
                },
                "simulation_parameters": {
                    "simulation_count": self.simulation_count,
                    "time_horizon": self.time_horizon,
                    "confidence_levels": self.confidence_levels
                }
            }
            
            self.logger.info("✅ Monte Carlo analysis completed successfully!")
            return results
            
        except Exception as e:
            self.logger.error(f"❌ Monte Carlo analysis failed: {e}")
            return self._get_error_metrics()
    
    async def _calculate_correlation_matrix(self, market_data: Dict) -> np.ndarray:
        """محاسبه ماتریس همبستگی بین دارایی‌ها"""
        try:
            # استخراج داده‌های تاریخی برای محاسبه همبستگی
            price_data = {}
            
            # جمع‌آوری داده‌های قیمت
            for asset_type in ['forex', 'crypto', 'indices', 'metals']:
                if asset_type in market_data:
                    for symbol, data in market_data[asset_type].items():
                        price_data[symbol] = data.get('price', 1.0)
            
            # در اینجا باید داده‌های تاریخی واقعی استفاده شود
            # برای نمونه، از یک ماتریس همبستگی پیش‌فرض استفاده می‌کنیم
            
            assets = list(price_data.keys())
            n_assets = len(assets)
            
            # ایجاد یک ماتریس همبستگی نمونه
            # در عمل، این ماتریس باید از داده‌های تاریخی محاسبه شود
            np.random.seed(42)  برای ثابت بودن نتایج
            base_correlation = 0.3
            correlation_matrix = np.full((n_assets, n_assets), base_correlation)
            np.fill_diagonal(correlation_matrix, 1.0)
            
            # اضافه کردن کمی نویز برای واقعی‌تر شدن
            noise = np.random.normal(0, 0.1, (n_assets, n_assets))
            correlation_matrix = correlation_matrix + noise
            correlation_matrix = (correlation_matrix + correlation_matrix.T) / 2
            
            # اطمینان از مثبت بودن معین
            eigenvalues = np.linalg.eigvals(correlation_matrix)
            if np.any(eigenvalues <= 0):
                correlation_matrix = self._make_positive_definite(correlation_matrix)
            
            self.correlation_matrices['current'] = {
                'matrix': correlation_matrix,
                'assets': assets,
                'timestamp': datetime.now()
            }
            
            return correlation_matrix
            
        except Exception as e:
            self.logger.error(f"Error calculating correlation matrix: {e}")
            # بازگشت ماتریس همانی در صورت خطا
            n_assets = 10  # تعداد تقریبی دارایی‌ها
            return np.eye(n_assets)
    
    def _make_positive_definite(self, matrix: np.ndarray) -> np.ndarray:
        """تبدیل ماتریس به معین مثبت"""
        # روش تصحیح برای اطمینان از معین مثبت بودن
        min_eigenval = np.min(np.real(np.linalg.eigvals(matrix)))
        if min_eigenval < 0:
            matrix -= (min_eigenval - 1e-6) * np.eye(matrix.shape[0])
        return matrix
    
    async def _simulate_portfolio(self, market_data: Dict, correlation_matrix: np.ndarray) -> np.ndarray:
        """شبیه‌سازی پرتفولیو با در نظر گرفتن همبستگی"""
        try:
            # پارامترهای شبیه‌سازی
            n_assets = correlation_matrix.shape[0]
            dt = 1 / 252  # گام زمانی (یک روز معاملاتی)
            
            # محاسبه پارامترهای هر دارایی
            asset_params = await self._calculate_asset_parameters(market_data)
            
            # تولید مسیرهای شبیه‌سازی
            portfolio_values = np.zeros(self.simulation_count)
            
            for i in range(self.simulation_count):
                # شبیه‌سازی همزمان تمام دارایی‌ها با در نظر گرفتن همبستگی
                correlated_returns = self._generate_correlated_returns(
                    asset_params, correlation_matrix, self.time_horizon
                )
                
                # محاسبه ارزش پرتفولیو
                portfolio_value = self._calculate_portfolio_value(
                    asset_params, correlated_returns
                )
                
                portfolio_values[i] = portfolio_value
            
            return portfolio_values
            
        except Exception as e:
            self.logger.error(f"Error in portfolio simulation: {e}")
            return np.zeros(self.simulation_count)
    
    async def _calculate_asset_parameters(self, market_data: Dict) -> List[Dict]:
        """محاسبه پارامترهای هر دارایی برای شبیه‌سازی"""
        asset_params = []
        
        # اینجا باید پارامترهای واقعی از داده‌های تاریخی محاسبه شود
        # برای نمونه از مقادیر پیش‌فرض استفاده می‌کنیم
        
        for asset_type in ['forex', 'crypto', 'indices', 'metals']:
            if asset_type in market_data:
                for symbol, data in market_data[asset_type].items():
                    params = {
                        'symbol': symbol,
                        'current_price': data.get('price', 1.0),
                        'mu': 0.08,  # بازده مورد انتظار سالانه
                        'sigma': 0.20,  # نوسان سالانه
                        'weight': 1.0  # وزن در پرتفولیو
                    }
                    asset_params.append(params)
        
        return asset_params
    
    def _generate_correlated_returns(self, asset_params: List[Dict], 
                                   correlation_matrix: np.ndarray, 
                                   periods: int) -> np.ndarray:
        """تولید بازده‌های همبسته"""
        n_assets = len(asset_params)
        
        # تجزیه کولسکی برای تولید اعداد تصادفی همبسته
        try:
            L = np.linalg.cholesky(correlation_matrix)
        except np.linalg.LinAlgError:
            # اگر ماتریس معین مثبت نباشد، از SVD استفاده می‌کنیم
            U, s, Vt = np.linalg.svd(correlation_matrix)
            L = U @ np.sqrt(np.diag(s))
        
        # تولید اعداد تصادفی مستقل
        Z = np.random.normal(0, 1, (periods, n_assets))
        
        # اعمال همبستگی
        correlated_Z = Z @ L.T
        
        # تبدیل به بازده‌های تصادفی
        returns = np.zeros((periods, n_assets))
        for i, params in enumerate(asset_params):
            mu = params['mu'] / 252  # بازده روزانه
            sigma = params['sigma'] / np.sqrt(252)  # نوسان روزانه
            returns[:, i] = mu + sigma * correlated_Z[:, i]
        
        return returns
    
    def _calculate_portfolio_value(self, asset_params: List[Dict], returns: np.ndarray) -> float:
        """محاسبه ارزش نهایی پرتفولیو"""
        final_prices = []
        total_weight = sum(asset['weight'] for asset in asset_params)
        
        for i, asset in enumerate(asset_params):
            # محاسبه قیمت نهایی دارایی
            price_path = asset['current_price'] * np.cumprod(1 + returns[:, i])
            final_price = price_path[-1]
            
            # اعمال وزن
            weighted_value = final_price * (asset['weight'] / total_weight)
            final_prices.append(weighted_value)
        
        return sum(final_prices)
    
    async def _calculate_risk_metrics(self, simulations: np.ndarray) -> Dict:
        """محاسبه معیارهای ریسک"""
        try:
            # محاسبه بازده‌ها
            returns = (simulations - np.mean(simulations)) / np.mean(simulations)
            
            # Value at Risk (VaR)
            var_metrics = {}
            for confidence in self.confidence_levels:
                var = np.percentile(returns, (1 - confidence) * 100)
                var_metrics[f'var_{int(confidence*100)}'] = float(var)
            
            # Conditional VaR (Expected Shortfall)
            cvar_metrics = {}
            for confidence in self.confidence_levels:
                var_threshold = np.percentile(returns, (1 - confidence) * 100)
                tail_returns = returns[returns <= var_threshold]
                cvar = np.mean(tail_returns) if len(tail_returns) > 0 else var_threshold
                cvar_metrics[f'cvar_{int(confidence*100)}'] = float(cvar)
            
            # سایر معیارهای ریسک
            max_drawdown = self._calculate_max_drawdown(simulations)
            sharpe_ratio = self._calculate_sharpe_ratio(returns)
            sortino_ratio = self._calculate_sortino_ratio(returns)
            
            return {
                'value_at_risk': var_metrics,
                'conditional_var': cvar_metrics,
                'max_drawdown': float(max_drawdown),
                'sharpe_ratio': float(sharpe_ratio),
                'sortino_ratio': float(sortino_ratio),
                'volatility': float(np.std(returns)),
                'expected_return': float(np.mean(returns)),
                'skewness': float(stats.skew(returns)),
                'kurtosis': float(stats.kurtosis(returns))
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating risk metrics: {e}")
            return {}
    
    def _calculate_max_drawdown(self, values: np.ndarray) -> float:
        """محاسبه حداکثر drawdown"""
        peak = np.maximum.accumulate(values)
        drawdown = (values - peak) / peak
        return np.min(drawdown)
    
    def _calculate_sharpe_ratio(self, returns: np.ndarray) -> float:
        """محاسبه شارپ ریشو"""
        excess_returns = returns - self.risk_free_rate / 252
        return np.mean(excess_returns) / np.std(excess_returns) * np.sqrt(252)
    
    def _calculate_sortino_ratio(self, returns: np.ndarray) -> float:
        """محاسبه سورتینو ریشو"""
        excess_returns = returns - self.risk_free_rate / 252
        downside_returns = excess_returns[excess_returns < 0]
        downside_std = np.std(downside_returns) if len(downside_returns) > 0 else 0
        return np.mean(excess_returns) / downside_std * np.sqrt(252) if downside_std != 0 else 0
    
    async def _analyze_crisis_scenarios(self, simulations: np.ndarray) -> Dict:
        """تحلیل سناریوهای بحران"""
        # محاسبه احتمال رویدادهای بحرانی
        total_simulations = len(simulations)
        initial_value = np.mean(simulations)  # مقدار اولیه تقریبی
        
        crisis_scenarios = {
            'mild_crisis': {
                'threshold': 0.9,  # کاهش ۱۰٪
                'probability': np.sum(simulations < initial_value * 0.9) / total_simulations,
                'description': 'کاهش متوسط بازار'
            },
            'severe_crisis': {
                'threshold': 0.7,  # کاهش ۳۰٪
                'probability': np.sum(simulations < initial_value * 0.7) / total_simulations,
                'description': 'کاهش شدید بازار'
            },
            'extreme_crisis': {
                'threshold': 0.5,  # کاهش ۵۰٪
                'probability': np.sum(simulations < initial_value * 0.5) / total_simulations,
                'description': 'بحران مالی شدید'
            }
        }
        
        return crisis_scenarios
    
    def _get_error_metrics(self) -> Dict:
        """معیارهای خطا در صورت شکست تحلیل"""
        return {
            "timestamp": datetime.now().isoformat(),
            "risk_metrics": {
                "value_at_risk": {"var_95": -0.05, "var_99": -0.08},
                "conditional_var": {"cvar_95": -0.07, "cvar_99": -0.10},
                "max_drawdown": -0.15,
                "sharpe_ratio": 0.0,
                "sortino_ratio": 0.0,
                "volatility": 0.0,
                "expected_return": 0.0
            },
            "crisis_scenarios": {},
            "error": True
        }
    
    async def simulate_single_asset(self, symbol: str, current_price: float, 
                                  historical_data: List[float]) -> Dict:
        """شبیه‌سازی تک دارایی"""
        # پیاده‌سازی شبیه‌سازی برای یک دارایی خاص
        pass
    
    async def cleanup(self):
        """پاک‌سازی منابع"""
        self.logger.info("🧹 Cleaning up Monte Carlo resources...")
        self.simulation_results.clear()
        self.correlation_matrices.clear()

# نمونه سینگلتون برای استفاده در سراسر سیستم
monte_carlo_engine = MonteCarloEngine()
