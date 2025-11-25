#!/usr/bin/env python3
"""
Data Validation Module
Input Validation and Sanitization
Developer: Seyed Aladdin Mousavi Jashni
"""

import re
import json
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import logging

class DataValidator:
    """اعتبارسنجی داده‌های ورودی و خروجی"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # الگوهای regex برای اعتبارسنجی
        self.patterns = {
            'symbol': r'^[A-Z0-9/]{1,20}$',
            'email': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
            'phone': r'^\+?[1-9]\d{1,14}$',
            'uuid': r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
        }
        
        # محدودیت‌های عددی
        self.limits = {
            'price_min': 0.00001,
            'price_max': 1000000,
            'quantity_min': 0.0001,
            'quantity_max': 100000,
            'percentage_min': -100,
            'percentage_max': 1000
        }
    
    def validate_market_data(self, market_data: Dict) -> Tuple[bool, List[str]]:
        """
        اعتبارسنجی داده‌های بازار
        
        Args:
            market_data: داده‌های بازار
            
        Returns:
            Tuple[bool, List[str]]: (معتبر بودن, لیست خطاها)
        """
        errors = []
        
        try:
            # اعتبارسنجی ساختار پایه
            if not isinstance(market_data, dict):
                errors.append("Market data must be a dictionary")
                return False, errors
            
            # اعتبارسنجی timestamp
            if 'timestamp' not in market_data:
                errors.append("Missing timestamp")
            else:
                if not self._validate_timestamp(market_data['timestamp']):
                    errors.append("Invalid timestamp format")
            
            # اعتبارسنجی بخش‌های مختلف بازار
            market_sections = ['forex', 'crypto', 'indices', 'metals']
            for section in market_sections:
                if section in market_data:
                    section_errors = self._validate_market_section(
                        market_data[section], section
                    )
                    errors.extend(section_errors)
            
            return len(errors) == 0, errors
            
        except Exception as e:
            self.logger.error(f"Error validating market data: {e}")
            errors.append(f"Validation error: {str(e)}")
            return False, errors
    
    def _validate_market_section(self, section_data: Dict, section_name: str) -> List[str]:
        """اعتبارسنجی یک بخش از داده‌های بازار"""
        errors = []
        
        if not isinstance(section_data, dict):
            errors.append(f"{section_name} data must be a dictionary")
            return errors
        
        for symbol, data in section_data.items():
            # اعتبارسنجی نماد
            if not self._validate_symbol(symbol, section_name):
                errors.append(f"Invalid symbol format: {symbol}")
                continue
            
            # اعتبارسنجی داده‌های قیمت
            if not isinstance(data, dict):
                errors.append(f"Price data for {symbol} must be a dictionary")
                continue
            
            price_errors = self._validate_price_data(data, symbol)
            errors.extend(price_errors)
        
        return errors
    
    def _validate_price_data(self, price_data: Dict, symbol: str) -> List[str]:
        """اعتبارسنجی داده‌های قیمت"""
        errors = []
        required_fields = ['price', 'timestamp']
        
        # بررسی فیلدهای اجباری
        for field in required_fields:
            if field not in price_data:
                errors.append(f"Missing required field '{field}' for {symbol}")
        
        # اعتبارسنجی قیمت
        if 'price' in price_data:
            price = price_data['price']
            if not self._validate_numeric(price, 'price'):
                errors.append(f"Invalid price for {symbol}: {price}")
        
        # اعتبارسنجی timestamp
        if 'timestamp' in price_data:
            if not self._validate_timestamp(price_data['timestamp']):
                errors.append(f"Invalid timestamp for {symbol}")
        
        # اعتبارسنجی تغییرات
        if 'change' in price_data:
            change = price_data['change']
            if not self._validate_numeric(change, 'change'):
                errors.append(f"Invalid change value for {symbol}: {change}")
        
        if 'change_percent' in price_data:
            change_percent = price_data['change_percent']
            if not self._validate_percentage(change_percent):
                errors.append(f"Invalid change percentage for {symbol}: {change_percent}")
        
        # اعتبارسنجی حجم
        if 'volume' in price_data:
            volume = price_data['volume']
            if not isinstance(volume, (int, float)) or volume < 0:
                errors.append(f"Invalid volume for {symbol}: {volume}")
        
        return errors
    
    def validate_signal(self, signal_data: Dict) -> Tuple[bool, List[str]]:
        """
        اعتبارسنجی داده‌های سیگنال
        
        Args:
            signal_data: داده‌های سیگنال
            
        Returns:
            Tuple[bool, List[str]]: (معتبر بودن, لیست خطاها)
        """
        errors = []
        
        try:
            required_fields = [
                'symbol', 'type', 'entry', 'stop_loss', 'take_profits',
                'timeframe', 'confidence', 'timestamp'
            ]
            
            # بررسی فیلدهای اجباری
            for field in required_fields:
                if field not in signal_data:
                    errors.append(f"Missing required field: {field}")
            
            # اعتبارسنجی نماد
            if 'symbol' in signal_data:
                symbol = signal_data['symbol']
                if not self._validate_symbol(symbol, 'any'):
                    errors.append(f"Invalid symbol: {symbol}")
            
            # اعتبارسنجی نوع سیگنال
            if 'type' in signal_data:
                valid_types = ['BUY_LIMIT', 'SELL_LIMIT', 'BUY_STOP', 'SELL_STOP', 
                              'BUY_MARKET', 'SELL_MARKET']
                if signal_data['type'] not in valid_types:
                    errors.append(f"Invalid signal type: {signal_data['type']}")
            
            # اعتبارسنجی قیمت‌ها
            price_fields = ['entry', 'stop_loss']
            for field in price_fields:
                if field in signal_data:
                    price = signal_data[field]
                    if not self._validate_numeric(price, 'price'):
                        errors.append(f"Invalid {field} price: {price}")
            
            # اعتبارسنجی take profits
            if 'take_profits' in signal_data:
                take_profits = signal_data['take_profits']
                if not isinstance(take_profits, list) or len(take_profits) == 0:
                    errors.append("Take profits must be a non-empty list")
                else:
                    for i, tp in enumerate(take_profits):
                        if not self._validate_numeric(tp, 'price'):
                            errors.append(f"Invalid take profit #{i+1}: {tp}")
            
            # اعتبارسنجی اطمینان
            if 'confidence' in signal_data:
                confidence = signal_data['confidence']
                if not (0 <= confidence <= 1):
                    errors.append(f"Confidence must be between 0 and 1: {confidence}")
            
            # اعتبارسنجی تایم‌فریم
            if 'timeframe' in signal_data:
                valid_timeframes = ['15m', '1h', '4h', '1d', '1w']
                if signal_data['timeframe'] not in valid_timeframes:
                    errors.append(f"Invalid timeframe: {signal_data['timeframe']}")
            
            # اعتبارسنجی timestamp
            if 'timestamp' in signal_data:
                if not self._validate_timestamp(signal_data['timestamp']):
                    errors.append("Invalid timestamp")
            
            return len(errors) == 0, errors
            
        except Exception as e:
            self.logger.error(f"Error validating signal data: {e}")
            errors.append(f"Validation error: {str(e)}")
            return False, errors
    
    def validate_user_input(self, user_data: Dict) -> Tuple[bool, List[str]]:
        """اعتبارسنجی داده‌های کاربر"""
        errors = []
        
        # اعتبارسنجی ایمیل
        if 'email' in user_data:
            if not re.match(self.patterns['email'], user_data['email']):
                errors.append("Invalid email format")
        
        # اعتبارسنجی تلفن
        if 'phone' in user_data:
            if not re.match(self.patterns['phone'], user_data['phone']):
                errors.append("Invalid phone number format")
        
        # اعتبارسنجی سایر فیلدها
        if 'username' in user_data:
            username = user_data['username']
            if len(username) < 3 or len(username) > 50:
                errors.append("Username must be between 3 and 50 characters")
        
        return len(errors) == 0, errors
    
    def _validate_symbol(self, symbol: str, asset_type: str) -> bool:
        """اعتبارسنجی فرمت نماد"""
        if not isinstance(symbol, str):
            return False
        
        # اعتبارسنجی عمومی
        if not re.match(self.patterns['symbol'], symbol):
            return False
        
        # اعتبارسنجی خاص بر اساس نوع دارایی
        if asset_type == 'forex':
            return '/' in symbol and len(symbol.split('/')) == 2
        elif asset_type == 'crypto':
            return '/' in symbol and symbol.endswith('/USD')
        elif asset_type == 'metals':
            return symbol.startswith('X') and '/' in symbol
        
        return True
    
    def _validate_timestamp(self, timestamp: str) -> bool:
        """اعتبارسنجی فرمت timestamp"""
        try:
            # بررسی فرمت ISO
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            
            # بررسی معقول بودن تاریخ (نه در آینده دور)
            if dt > datetime.now() + timedelta(days=1):
                return False
            
            return True
        except (ValueError, TypeError):
            return False
    
    def _validate_numeric(self, value: Any, value_type: str) -> bool:
        """اعتبارسنجی مقادیر عددی"""
        if not isinstance(value, (int, float)):
            return False
        
        limits = self.limits
        
        if value_type == 'price':
            return limits['price_min'] <= value <= limits['price_max']
        elif value_type == 'quantity':
            return limits['quantity_min'] <= value <= limits['quantity_max']
        elif value_type == 'change':
            return abs(value) <= limits['price_max'] * 0.5  # حداکثر تغییر 50%
        
        return True
    
    def _validate_percentage(self, percentage: Any) -> bool:
        """اعتبارسنجی مقادیر درصدی"""
        if not isinstance(percentage, (int, float)):
            return False
        
        return self.limits['percentage_min'] <= percentage <= self.limits['percentage_max']
    
    def sanitize_string(self, text: str, max_length: int = 255) -> str:
        """پاک‌سازی رشته‌های متنی"""
        if not isinstance(text, str):
            return ""
        
        # حذف کاراکترهای خطرناک
        sanitized = re.sub(r'[<>"\']', '', text)
        
        # محدود کردن طول
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length]
        
        return sanitized.strip()
    
    def validate_json_schema(self, data: Any, schema: Dict) -> Tuple[bool, List[str]]:
        """اعتبارسنجی داده بر اساس schema"""
        # پیاده‌سازی اعتبارسنجی JSON Schema
        # اینجا می‌توان از کتابخانه‌هایی مانند jsonschema استفاده کرد
        pass

# نمونه سینگلتون برای استفاده آسان
data_validator = DataValidator()

# توابع shortcut برای استفاده راحت
def validate_market_data(market_data: Dict) -> Tuple[bool, List[str]]:
    return data_validator.validate_market_data(market_data)

def validate_signal(signal_data: Dict) -> Tuple[bool, List[str]]:
    return data_validator.validate_signal(signal_data)
