#!/usr/bin/env python3
"""
Crisis Analyzer Core Module
Financial Crisis 2025-2026 Analysis
Developer: Seyed Aladdin Mousavi Jashni
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import numpy as np
import pandas as pd

from config import config

class CrisisAnalyzer:
    """تحلیلگر بحران مالی ۲۰۲۵-۲۰۲۶"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.scenarios = self._initialize_scenarios()
        self.indicators = self._initialize_indicators()
        self.alert_history = []
        
    def _initialize_scenarios(self) -> Dict:
        """مقداردهی اولیه سناریوهای بحران"""
        return {
            # سناریوهای کلاسیک
            "CREDIT_COLLAPSE": {
                "name": "فروپاشی اعتبار شرکتها",
                "weight": 0.30,
                "indicators": ["corporate_bonds", "credit_spreads", "default_rates"],
                "threshold": 0.7,
                "active": False
            },
            "LIQUIDITY_SHOCK": {
                "name": "شوک نقدینگی", 
                "weight": 0.25,
                "indicators": ["money_flows", "liquidity_ratios", "volatility"],
                "threshold": 0.6,
                "active": False
            },
            "GEOPOLITICAL_ENTROPY": {
                "name": "آشفتگی ژئوپلیتیک",
                "weight": 0.20,
                "indicators": ["oil_prices", "safe_haven_flows", "currency_volatility"],
                "threshold": 0.65,
                "active": False
            },
            
            # سناریوهای توسعه یافته
            "TECH_CRASH": {
                "name": "ریسک فناوری",
                "weight": 0.15,
                "indicators": ["nasdaq", "tech_volume", "crypto_market"],
                "threshold": 0.55,
                "active": False
            },
            "ENERGY_CRISIS": {
                "name": "بحران انرژی",
                "weight": 0.10,
                "indicators": ["brent_oil", "energy_index", "supply_chain"],
                "threshold": 0.6,
                "active": False
            }
        }
    
    def _initialize_indicators(self) -> Dict:
        """مقداردهی اولیه شاخص‌های نظارتی"""
        return {
            "EUR/USD": {
                "threshold": 0.08,  # کاهش ۸٪ در ۳۰ روز
                "current_value": None,
                "trend": None
            },
            "XAU/USD": {
                "threshold": 0.10,  # افزایش ۱۰٪ در ۱۴ روز
                "current_value": None, 
                "trend": None
            },
            "BTC/USD": {
                "threshold": 0.20,  # کاهش ۲۰٪ در ۳۰ روز
                "current_value": None,
                "trend": None
            },
            "SP500": {
                "threshold": 0.15,  # کاهش ۱۵٪ در ۳۰ روز
                "current_value": None,
                "trend": None
            },
            "VIX": {
                "threshold": 0.50,  # افزایش ۵۰٪ در ۷ روز
                "current_value": None,
                "trend": None
            },
            "GER30": {
                "threshold": 0.12,  # کاهش ۱۲٪ در ۳۰ روز
                "current_value": None,
                "trend": None
            }
        }
    
    async def initialize(self):
        """مقداردهی اولیه تحلیلگر بحران"""
        self.logger.info("📊 Initializing Crisis Analyzer...")
        self.logger.info(f"🎯 Loaded {len(self.scenarios)} crisis scenarios")
        self.logger.info(f"📈 Monitoring {len(self.indicators)} key indicators")
    
    async def analyze(self, market_data: Dict) -> Dict:
        """
        تحلیل جامع بحران بر اساس داده‌های بازار
        
        Args:
            market_data: داده‌های بازار دریافتی از MarketDataManager
            
        Returns:
            Dict: گزارش تحلیل بحران
        """
        try:
            self.logger.info("🔍 Starting crisis analysis...")
            
            # به‌روزرسانی مقادیر شاخص‌ها
            await self._update_indicators(market_data)
            
            # محاسبه امتیاز بحران
            crisis_score = await self._calculate_crisis_score()
            
            # شناسایی سناریوهای فعال
            active_scenarios = await self._identify_active_scenarios()
            
            # تعیین سطح هشدار
            alert_level = self._determine_alert_level(crisis_score, active_scenarios)
            
            # تولید توصیه‌ها
            recommendations = await self._generate_recommendations(alert_level, active_scenarios)
            
            report = {
                "timestamp": datetime.now().isoformat(),
                "crisis_score": crisis_score,
                "alert_level": alert_level,
                "dominant_scenario": self._get_dominant_scenario(active_scenarios),
                "active_scenarios": active_scenarios,
                "indicators_status": self._get_indicators_status(),
                "recommendations": recommendations,
                "market_condition": self._get_market_condition(crisis_score)
            }
            
            # ذخیره در تاریخچه
            self.alert_history.append(report)
            
            self.logger.info(f"✅ Crisis analysis completed. Score: {crisis_score:.3f}")
            return report
            
        except Exception as e:
            self.logger.error(f"❌ Crisis analysis failed: {e}")
            return self._get_error_report()
    
    async def _update_indicators(self, market_data: Dict):
        """به‌روزرسانی مقادیر شاخص‌ها"""
        try:
            # به‌روزرسانی شاخص‌های فارکس
            for symbol in config.MONITORED_INSTRUMENTS["FOREX"]:
                if symbol in market_data.get("forex", {}):
                    price_data = market_data["forex"][symbol]
                    self._update_indicator_value(symbol, price_data.get("price"))
            
            # به‌روزرسانی شاخص‌های کریپتو
            for symbol in config.MONITORED_INSTRUMENTS["CRYPTO"]:
                if symbol in market_data.get("crypto", {}):
                    price_data = market_data["crypto"][symbol]
                    self._update_indicator_value(symbol, price_data.get("price"))
            
            # به‌روزرسانی شاخص‌های سهام
            for symbol in config.MONITORED_INSTRUMENTS["INDICES"]:
                if symbol in market_data.get("indices", {}):
                    price_data = market_data["indices"][symbol]
                    self._update_indicator_value(symbol, price_data.get("price"))
            
            # به‌روزرسانی فلزات گرانبها
            for symbol in config.MONITORED_INSTRUMENTS["METALS"]:
                if symbol in market_data.get("metals", {}):
                    price_data = market_data["metals"][symbol]
                    self._update_indicator_value(symbol, price_data.get("price"))
                    
        except Exception as e:
            self.logger.error(f"Error updating indicators: {e}")
    
    def _update_indicator_value(self, symbol: str, value: float):
        """به‌روزرسانی مقدار یک شاخص"""
        if symbol in self.indicators and value is not None:
            self.indicators[symbol]["current_value"] = value
            # در اینجا می‌توان تحلیل روند را اضافه کرد
    
    async def _calculate_crisis_score(self) -> float:
        """محاسبه امتیاز بحران کلی"""
        try:
            scores = []
            
            # محاسبه امتیاز بر اساس شاخص‌ها
            for symbol, indicator in self.indicators.items():
                if indicator["current_value"] is not None:
                    # اینجا منطق محاسبه امتیاز بر اساس انحراف از آستانه
                    score = self._calculate_indicator_score(symbol, indicator)
                    scores.append(score)
            
            # محاسبه امتیاز بر اساس سناریوها
            scenario_scores = []
            for scenario_name, scenario in self.scenarios.items():
                scenario_score = self._calculate_scenario_score(scenario)
                scenario_scores.append(scenario_score * scenario["weight"])
            
            if scores and scenario_scores:
                final_score = (np.mean(scores) + np.mean(scenario_scores)) / 2
                return min(max(final_score, 0.0), 1.0)  # نرمال‌سازی بین ۰ و ۱
            else:
                return 0.0
                
        except Exception as e:
            self.logger.error(f"Error calculating crisis score: {e}")
            return 0.0
    
    def _calculate_indicator_score(self, symbol: str, indicator: Dict) -> float:
        """محاسبه امتیاز برای یک شاخص خاص"""
        # اینجا منطق پیچیده‌تری برای محاسبه امتیاز هر شاخص
        # بر اساس انحراف از آستانه، روند، و نوسانات
        return 0.0  # مقدار موقت
    
    def _calculate_scenario_score(self, scenario: Dict) -> float:
        """محاسبه امتیاز برای یک سناریو"""
        # محاسبه امتیاز سناریو بر اساس شاخص‌های وابسته
        return 0.0  # مقدار موقت
    
    async def _identify_active_scenarios(self) -> List[Dict]:
        """شناسایی سناریوهای فعال"""
        active_scenarios = []
        
        for scenario_name, scenario in self.scenarios.items():
            # محاسبه امتیاز سناریو
            scenario_score = self._calculate_scenario_score(scenario)
            
            if scenario_score >= scenario["threshold"]:
                scenario["active"] = True
                scenario["current_score"] = scenario_score
                active_scenarios.append(scenario)
            else:
                scenario["active"] = False
        
        return active_scenarios
    
    def _determine_alert_level(self, crisis_score: float, active_scenarios: List) -> str:
        """تعیین سطح هشدار"""
        if crisis_score >= 0.7 or len(active_scenarios) >= 3:
            return "CRITICAL"
        elif crisis_score >= 0.5 or len(active_scenarios) >= 2:
            return "HIGH"
        elif crisis_score >= 0.3 or len(active_scenarios) >= 1:
            return "MEDIUM"
        elif crisis_score >= 0.1:
            return "LOW"
        else:
            return "NORMAL"
    
    def _get_dominant_scenario(self, active_scenarios: List) -> str:
        """شناسایی سناریوی غالب"""
        if not active_scenarios:
            return "NORMAL"
        
        # پیدا کردن سناریو با بالاترین امتیاز
        dominant = max(active_scenarios, key=lambda x: x.get("current_score", 0))
        return dominant["name"]
    
    def _get_indicators_status(self) -> Dict:
        """دریافت وضعیت شاخص‌ها"""
        status = {}
        for symbol, indicator in self.indicators.items():
            status[symbol] = {
                "current_value": indicator["current_value"],
                "threshold": indicator["threshold"],
                "trend": indicator["trend"]
            }
        return status
    
    def _get_market_condition(self, crisis_score: float) -> str:
        """تعیین وضعیت بازار"""
        if crisis_score >= 0.7:
            return "CRISIS"
        elif crisis_score >= 0.5:
            return "HIGH_RISK"
        elif crisis_score >= 0.3:
            return "MODERATE_RISK"
        elif crisis_score >= 0.1:
            return "LOW_RISK"
        else:
            return "NORMAL"
    
    async def _generate_recommendations(self, alert_level: str, active_scenarios: List) -> List[str]:
        """تولید توصیه‌های استراتژیک"""
        recommendations = []
        
        if alert_level in ["CRITICAL", "HIGH"]:
            recommendations.extend([
                "کاهش شدید ریسک پرتفولیو",
                "افزایش نقدینگی به حداقل ۳۰٪",
                "حرکت به سمت دارایی‌های امن (طلا، اوراق قرضه)",
                "غیرفعال کردن معاملات پرریسک"
            ])
        elif alert_level == "MEDIUM":
            recommendations.extend([
                "کاهش متوسط ریسک",
                "افزایش حاشیه ایمنی در معاملات",
                "نظارت دقیق بر شاخص‌های کلیدی",
                "تنوع‌بخشی بیشتر پرتفولیو"
            ])
        else:
            recommendations.extend([
                "ادامه استراتژی عادی",
                "نظارت منظم بر بازار",
                "حفظ تنوع پرتفولیو",
                "آماده‌باش برای تغییر شرایط"
            ])
        
        # اضافه کردن توصیه‌های خاص سناریو
        for scenario in active_scenarios:
            if scenario["name"] == "ریسک فناوری":
                recommendations.append("کاهش وزن سهام فناوری در پرتفولیو")
            elif scenario["name"] == "بحران انرژی":
                recommendations.append("افزایش سرمایه‌گذاری در انرژی‌های جایگزین")
        
        return recommendations
    
    def _get_error_report(self) -> Dict:
        """گزارش خطا در صورت شکست تحلیل"""
        return {
            "timestamp": datetime.now().isoformat(),
            "crisis_score": 0.0,
            "alert_level": "UNKNOWN",
            "dominant_scenario": "ANALYSIS_ERROR",
            "active_scenarios": [],
            "indicators_status": {},
            "recommendations": ["سیستم تحلیل بحران موقتاً غیرفعال است"],
            "market_condition": "UNKNOWN",
            "error": True
        }
    
    def get_alert_history(self, limit: int = 10) -> List[Dict]:
        """دریافت تاریخچه هشدارها"""
        return self.alert_history[-limit:] if self.alert_history else []
    
    async def cleanup(self):
        """پاک‌سازی منابع"""
        self.logger.info("🧹 Cleaning up Crisis Analyzer resources...")
        self.alert_history.clear()

# نمونه سینگلتون برای استفاده در سراسر سیستم
crisis_analyzer = CrisisAnalyzer()
