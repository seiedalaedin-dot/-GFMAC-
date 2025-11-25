
import logging
import sys
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from typing import Optional

def setup_logging(name: str = None, level: int = logging.INFO, 
                  log_file: str = None, max_bytes: int = 10*1024*1024,
                  backup_count: int = 5) -> logging.Logger:
    """
    راه‌اندازی پیشرفته سیستم لاگ‌گیری
    
    Args:
        name: نام logger
        level: سطح لاگ‌گیری
        log_file: مسیر فایل لاگ
        max_bytes: حداکثر سایز فایل لاگ
        backup_count: تعداد فایل‌های بک‌آپ
        
    Returns:
        logging.Logger: شیء logger
    """
    if name is None:
        name = __name__
    
    logger = logging.getLogger(name)
    
    # اگر logger از قبل تنظیم شده، بازگرداندن همان
    if logger.handlers:
        return logger
    
    logger.setLevel(level)
    
    # فرمت لاگ
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Handler کنسول
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Handler فایل
    if log_file:
        # اطمینان از وجود دایرکتوری
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        file_handler = RotatingFileHandler(
            log_file, 
            maxBytes=max_bytes, 
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # Handler برای خطاها
    error_handler = logging.StreamHandler(sys.stderr)
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    logger.addHandler(error_handler)
    
    return logger

def get_logger(name: str = None) -> logging.Logger:
    """
    دریافت logger با تنظیمات پیش‌فرض
    
    Args:
        name: نام logger
        
    Returns:
        logging.Logger: شیء logger
    """
    return setup_logging(name)

class PerformanceLogger:
    """لاگر مخصوص عملکرد و زمان‌بندی"""
    
    def __init__(self, name: str = "performance"):
        self.logger = setup_logging(name)
        self.timers = {}
    
    def start_timer(self, operation: str):
        """شروع تایمر برای یک عملیات"""
        self.timers[operation] = datetime.now()
        self.logger.info(f"⏱️ Starting operation: {operation}")
    
    def stop_timer(self, operation: str) -> float:
        """توقف تایمر و محاسبه زمان اجرا"""
        if operation not in self.timers:
            self.logger.warning(f"Timer for operation '{operation}' not found")
            return 0.0
        
        start_time = self.timers[operation]
        execution_time = (datetime.now() - start_time).total_seconds()
        
        self.logger.info(f"✅ Operation '{operation}' completed in {execution_time:.3f} seconds")
        del self.timers[operation]
        
        return execution_time
    
    def log_performance_metric(self, metric: str, value: float, unit: str = ""):
        """ثبت معیار عملکرد"""
        self.logger.info(f"📊 Performance Metric - {metric}: {value} {unit}".strip())

class SecurityLogger:
    """لاگر مخصوص امنیت و دسترسی"""
    
    def __init__(self, name: str = "security"):
        self.logger = setup_logging(name)
    
    def log_login_attempt(self, user_id: str, ip: str, success: bool):
        """ثبت تلاش ورود"""
        status = "SUCCESS" if success else "FAILED"
        self.logger.info(f"🔐 Login attempt - User: {user_id}, IP: {ip}, Status: {status}")
    
    def log_api_call(self, endpoint: str, method: str, user_id: str = "unknown"):
        """ثبت فراخوانی API"""
        self.logger.info(f"🌐 API Call - {method} {endpoint} by User: {user_id}")
    
    def log_suspicious_activity(self, activity: str, details: str):
        """ثبت فعالیت مشکوک"""
        self.logger.warning(f"🚨 Suspicious Activity - {activity}: {details}")

class TradingLogger:
    """لاگر مخصوص معاملات و سیگنال‌ها"""
    
    def __init__(self, name: str = "trading"):
        self.logger = setup_logging(name)
    
    def log_signal_generated(self, symbol: str, signal_type: str, confidence: float):
        """ثبت تولید سیگنال"""
        self.logger.info(f"📈 Signal Generated - {symbol}: {signal_type} (Confidence: {confidence:.2f})")
    
    def log_trade_execution(self, symbol: str, action: str, quantity: float, price: float):
        """ثبت اجرای معامله"""
        self.logger.info(f"💰 Trade Executed - {symbol}: {action} {quantity} @ {price}")
    
    def log_portfolio_update(self, total_value: float, profit_loss: float):
        """ثبت به‌روزرسانی پرتفولیو"""
        self.logger.info(f"📊 Portfolio Update - Total: {total_value:.2f}, P&L: {profit_loss:.2f}")

# نمونه‌های سینگلتون برای استفاده آسان
performance_logger = PerformanceLogger()
security_logger = SecurityLogger()
trading_logger = TradingLogger()
