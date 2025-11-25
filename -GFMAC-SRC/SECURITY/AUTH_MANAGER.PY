#!/usr/bin/env python3
"""
Authentication Manager Module
Advanced Security and User Management
Developer: Seyed Aladdin Mousavi Jashni
"""

import asyncio
import logging
import jwt
import bcrypt
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import qrcode
import io
import base64

from config import config

class AuthManager:
    """مدیریت احراز هویت پیشرفته با قابلیت‌های امنیتی چندلایه"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.secret_key = config.SECURITY.get('JWT_SECRET', 'fallback-secret-key-change-in-production')
        self.algorithm = "HS256"
        
        # ذخیره‌سازی موقت کدهای تأیید
        self.verification_codes = {}
        self.totp_secrets = {}
        
        # لاگ امنیتی
        self.security_log = []
    
    async def initialize(self):
        """مقداردهی اولیه سیستم احراز هویت"""
        self.logger.info("🔐 Initializing Authentication Manager...")
        self.logger.info("✅ Google Authenticator support: ENABLED")
        self.logger.info("✅ SMS Verification support: ENABLED")
        self.logger.info("✅ JWT Token system: ENABLED")
    
    async def create_user(self, user_data: Dict) -> Tuple[bool, Dict]:
        """
        ایجاد کاربر جدید با امنیت کامل
        
        Args:
            user_data: اطلاعات کاربر
            
        Returns:
            Tuple[bool, Dict]: (موفقیت, اطلاعات کاربر ایجاد شده)
        """
        try:
            self.logger.info(f"👤 Creating new user: {user_data.get('email')}")
            
            # اعتبارسنجی داده‌های کاربر
            is_valid, errors = self._validate_user_data(user_data)
            if not is_valid:
                return False, {'errors': errors}
            
            # هش کردن رمز عبور
            hashed_password = await self._hash_password(user_data['password'])
            
            # تولید شناسه یکتا
            user_id = self._generate_user_id()
            
            # تولید کلیدهای امنیتی
            google_auth_secret = self._generate_google_auth_secret()
            api_key = self._generate_api_key()
            
            user_profile = {
                'user_id': user_id,
                'email': user_data['email'],
                'mobile': user_data.get('mobile'),
                'password_hash': hashed_password,
                'security': {
                    'google_auth_secret': google_auth_secret,
                    'api_key': api_key,
                    'two_factor_enabled': True,
                    'login_attempts': 0,
                    'last_login': None,
                    'account_locked': False
                },
                'profile': {
                    'first_name': user_data.get('first_name'),
                    'last_name': user_data.get('last_name'),
                    'created_at': datetime.now().isoformat(),
                    'last_updated': datetime.now().isoformat()
                },
                'permissions': self._get_default_permissions(),
                'preferences': {
                    'notifications': True,
                    'theme': 'dark',
                    'language': 'fa'
                }
            }
            
            # تولید QR code برای Google Authenticator
            qr_code_data = await self._generate_google_auth_qr_code(
                user_data['email'], google_auth_secret
            )
            
            self._log_security_event(
                'USER_CREATED',
                f"User {user_id} created successfully",
                user_id
            )
            
            return True, {
                'user': user_profile,
                'qr_code': qr_code_data,
                'setup_instructions': 'Scan QR code with Google Authenticator app'
            }
            
        except Exception as e:
            self.logger.error(f"❌ User creation failed: {e}")
            self._log_security_event('USER_CREATION_FAILED', str(e))
            return False, {'error': str(e)}
    
    async def authenticate_user(self, credentials: Dict) -> Tuple[bool, Dict]:
        """
        احراز هویت کاربر با چند فاکتور
        
        Args:
            credentials: اطلاعات ورود
            
        Returns:
            Tuple[bool, Dict]: (موفقیت, اطلاعات احراز هویت)
        """
        try:
            identifier = credentials.get('email') or credentials.get('mobile')
            self.logger.info(f"🔐 Authentication attempt for: {identifier}")
            
            # شبیه‌سازی بررسی کاربر در دیتابیس
            user = await self._get_user_by_identifier(identifier)
            if not user:
                self._log_security_event('AUTH_FAILED', f"User not found: {identifier}")
                return False, {'error': 'Invalid credentials'}
            
            # بررسی قفل بودن حساب
            if user['security']['account_locked']:
                self._log_security_event('AUTH_FAILED', f"Account locked: {identifier}")
                return False, {'error': 'Account is locked'}
            
            # بررسی رمز عبور
            password_valid = await self._verify_password(
                credentials['password'], 
                user['password_hash']
            )
            
            if not password_valid:
                # افزایش شماره تلاش‌های ناموفق
                user['security']['login_attempts'] += 1
                
                # قفل کردن حساب پس از ۵ تلاش ناموفق
                if user['security']['login_attempts'] >= 5:
                    user['security']['account_locked'] = True
                    self._log_security_event('ACCOUNT_LOCKED', f"Too many failed attempts: {identifier}")
                
                self._log_security_event('AUTH_FAILED', f"Invalid password: {identifier}")
                return False, {'error': 'Invalid credentials'}
            
            # بررسی احراز هویت دو مرحله‌ای
            if user['security']['two_factor_enabled']:
                two_factor_valid = await self._verify_two_factor(
                    user, 
                    credentials.get('two_factor_code')
                )
                
                if not two_factor_valid:
                    self._log_security_event('AUTH_FAILED', f"Invalid 2FA code: {identifier}")
                    return False, {'error': 'Invalid two-factor code'}
            
            # بازنشانی شماره تلاش‌های ناموفق
            user['security']['login_attempts'] = 0
            user['security']['last_login'] = datetime.now().isoformat()
            
            # تولید توکن JWT
            access_token = await self._generate_access_token(user)
            refresh_token = await self._generate_refresh_token(user)
            
            self._log_security_event(
                'AUTH_SUCCESS',
                f"User {user['user_id']} authenticated successfully",
                user['user_id']
            )
            
            return True, {
                'access_token': access_token,
                'refresh_token': refresh_token,
                'token_type': 'bearer',
                'expires_in': config.JWT_EXPIRATION.total_seconds(),
                'user': self._sanitize_user_data(user)
            }
            
        except Exception as e:
            self.logger.error(f"❌ Authentication failed: {e}")
            self._log_security_event('AUTH_ERROR', str(e))
            return False, {'error': 'Authentication failed'}
    
    async def verify_google_auth(self, user_id: str, token: str) -> bool:
        """
        تأیید کد Google Authenticator
        
        Args:
            user_id: شناسه کاربر
            token: کد تأیید
            
        Returns:
            bool: معتبر بودن کد
        """
        try:
            user = await self._get_user_by_id(user_id)
            if not user or 'google_auth_secret' not in user['security']:
                return False
            
            # اینجا باید از کتابخانه TOTP استفاده شود
            # برای نمونه، یک شبیه‌سازی ساده
            secret = user['security']['google_auth_secret']
            expected_code = self._generate_totp_code(secret)
            
            is_valid = token == expected_code
            
            if is_valid:
                self._log_security_event('2FA_SUCCESS', f"Google Auth verified for user {user_id}", user_id)
            else:
                self._log_security_event('2FA_FAILED', f"Invalid Google Auth code for user {user_id}", user_id)
            
            return is_valid
            
        except Exception as e:
            self.logger.error(f"Error verifying Google Auth: {e}")
            return False
    
    async def send_sms_verification(self, mobile: str) -> Tuple[bool, str]:
        """
        ارسال کد تأیید SMS
        
        Args:
            mobile: شماره موبایل
            
        Returns:
            Tuple[bool, str]: (موفقیت, کد تأیید)
        """
        try:
            # تولید کد تأیید ۶ رقمی
            verification_code = ''.join([str(secrets.randbelow(10)) for _ in range(6)])
            
            # ذخیره کد با زمان انقضا
            self.verification_codes[mobile] = {
                'code': verification_code,
                'expires_at': datetime.now() + timedelta(minutes=5),
                'attempts': 0
            }
            
            # در اینجا باید با سرویس SMS ادغام شود
            self.logger.info(f"📱 SMS verification code for {mobile}: {verification_code}")
            
            self._log_security_event('SMS_SENT', f"Verification code sent to {mobile}")
            
            return True, verification_code
            
        except Exception as e:
            self.logger.error(f"❌ SMS verification failed: {e}")
            return False, ""
    
    async def verify_sms_code(self, mobile: str, code: str) -> bool:
        """
        تأیید کد SMS
        
        Args:
            mobile: شماره موبایل
            code: کد تأیید
            
        Returns:
            bool: معتبر بودن کد
        """
        try:
            if mobile not in self.verification_codes:
                return False
            
            verification_data = self.verification_codes[mobile]
            
            # بررسی انقضا
            if datetime.now() > verification_data['expires_at']:
                del self.verification_codes[mobile]
                return False
            
            # بررسی تعداد تلاش‌ها
            if verification_data['attempts'] >= 3:
                del self.verification_codes[mobile]
                return False
            
            verification_data['attempts'] += 1
            
            is_valid = code == verification_data['code']
            
            if is_valid:
                del self.verification_codes[mobile]
                self._log_security_event('SMS_VERIFIED', f"SMS code verified for {mobile}")
            else:
                self._log_security_event('SMS_FAILED', f"Invalid SMS code for {mobile}")
            
            return is_valid
            
        except Exception as e:
            self.logger.error(f"Error verifying SMS code: {e}")
            return False
    
    async def _generate_access_token(self, user: Dict) -> str:
        """تولید توکن دسترسی JWT"""
        payload = {
            'user_id': user['user_id'],
            'email': user['email'],
            'permissions': user['permissions'],
            'exp': datetime.now() + config.JWT_EXPIRATION,
            'iat': datetime.now(),
            'type': 'access'
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    async def _generate_refresh_token(self, user: Dict) -> str:
        """تولید توکن رفرش JWT"""
        payload = {
            'user_id': user['user_id'],
            'exp': datetime.now() + timedelta(days=30),
            'iat': datetime.now(),
            'type': 'refresh'
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    async def verify_token(self, token: str) -> Tuple[bool, Dict]:
        """اعتبارسنجی توکن JWT"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return True, payload
        except jwt.ExpiredSignatureError:
            self._log_security_event('TOKEN_EXPIRED', "JWT token expired")
            return False, {'error': 'Token expired'}
        except jwt.InvalidTokenError as e:
            self._log_security_event('TOKEN_INVALID', f"Invalid JWT token: {e}")
            return False, {'error': 'Invalid token'}
    
    async def _hash_password(self, password: str) -> str:
        """هش کردن رمز عبور با bcrypt"""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    async def _verify_password(self, password: str, hashed_password: str) -> bool:
        """بررسی تطابق رمز عبور"""
        try:
            return bcrypt.checkpw(
                password.encode('utf-8'), 
                hashed_password.encode('utf-8')
            )
        except Exception as e:
            self.logger.error(f"Password verification error: {e}")
            return False
    
    def _generate_user_id(self) -> str:
        """تولید شناسه یکتای کاربر"""
        return f"user_{secrets.token_hex(8)}"
    
    def _generate_google_auth_secret(self) -> str:
        """تولید کلید مخفی برای Google Authenticator"""
        return base64.b32encode(secrets.token_bytes(10)).decode('utf-8')
    
    def _generate_api_key(self) -> str:
        """تولید کلید API"""
        return f"fa_{secrets.token_hex(16)}"
    
    async def _generate_google_auth_qr_code(self, email: str, secret: str) -> str:
        """تولید QR code برای Google Authenticator"""
        try:
            # ساخت URI برای Google Authenticator
            issuer = "Financial Analyzer Pro"
            auth_uri = f"otpauth://totp/{issuer}:{email}?secret={secret}&issuer={issuer}"
            
            # تولید QR code
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(auth_uri)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            
            # تبدیل به base64
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            buffer.seek(0)
            
            img_str = base64.b64encode(buffer.getvalue()).decode()
            
            return f"data:image/png;base64,{img_str}"
            
        except Exception as e:
            self.logger.error(f"Error generating QR code: {e}")
            return ""
    
    def _generate_totp_code(self, secret: str) -> str:
        """تولید کد TOTP (شبیه‌سازی)"""
        # در عمل باید از کتابخانه pyotp استفاده شود
        import time
        current_time = int(time.time()) // 30
        return f"{current_time % 1000000:06d}"[-6:]
    
    def _validate_user_data(self, user_data: Dict) -> Tuple[bool, List[str]]:
        """اعتبارسنجی داده‌های کاربر"""
        errors = []
        
        if 'email' not in user_data:
            errors.append("Email is required")
        elif not self._is_valid_email(user_data['email']):
            errors.append("Invalid email format")
        
        if 'password' not in user_data:
            errors.append("Password is required")
        elif len(user_data['password']) < 8:
            errors.append("Password must be at least 8 characters")
        
        if 'mobile' in user_data and not self._is_valid_mobile(user_data['mobile']):
            errors.append("Invalid mobile number format")
        
        return len(errors) == 0, errors
    
    def _is_valid_email(self, email: str) -> bool:
        """بررسی معتبر بودن ایمیل"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def _is_valid_mobile(self, mobile: str) -> bool:
        """بررسی معتبر بودن شماره موبایل"""
        import re
        pattern = r'^\+?[1-9]\d{1,14}$'
        return re.match(pattern, mobile) is not None
    
    async def _get_user_by_identifier(self, identifier: str) -> Optional[Dict]:
        """دریافت کاربر بر اساس ایمیل یا موبایل (شبیه‌سازی)"""
        # در عمل باید از دیتابیس خوانده شود
        # اینجا یک کاربر نمونه برمی‌گردانیم
        return {
            'user_id': 'user_sample_123',
            'email': 'user@example.com',
            'mobile': '+1234567890',
            'password_hash': await self._hash_password('password123'),
            'security': {
                'google_auth_secret': 'JBSWY3DPEHPK3PXP',
                'two_factor_enabled': True,
                'login_attempts': 0,
                'account_locked': False,
                'last_login': None
            },
            'permissions': self._get_default_permissions()
        }
    
    async def _get_user_by_id(self, user_id: str) -> Optional[Dict]:
        """دریافت کاربر بر اساس شناسه (شبیه‌سازی)"""
        # مشابه تابع بالا
        return await self._get_user_by_identifier('user@example.com')
    
    async def _verify_two_factor(self, user: Dict, code: str) -> bool:
        """تأیید احراز هویت دو مرحله‌ای"""
        if not code:
            return False
        
        # اول بررسی Google Authenticator
        if await self.verify_google_auth(user['user_id'], code):
            return True
        
        # سپس بررسی SMS
        if user.get('mobile') and await self.verify_sms_code(user['mobile'], code):
            return True
        
        return False
    
    def _get_default_permissions(self) -> List[str]:
        """مجوزهای پیش‌فرض کاربر"""
        return [
            'read_market_data',
            'view_signals', 
            'access_basic_analysis',
            'manage_own_portfolio'
        ]
    
    def _sanitize_user_data(self, user: Dict) -> Dict:
        """پاک‌سازی داده‌های کاربر برای ارسال به کلاینت"""
        sanitized = user.copy()
        
        # حذف فیلدهای حساس
        sanitized.pop('password_hash', None)
        sanitized['security'].pop('google_auth_secret', None)
        sanitized['security'].pop('api_key', None)
        
        return sanitized
    
    def _log_security_event(self, event_type: str, message: str, user_id: str = None):
        """ثبت رویداد امنیتی"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type,
            'message': message,
            'user_id': user_id,
            'ip_address': '127.0.0.1'  # در عمل باید از request گرفته شود
        }
        
        self.security_log.append(log_entry)
        self.logger.info(f"🔒 SECURITY: {event_type} - {message}")
    
    async def get_security_log(self, limit: int = 100) -> List[Dict]:
        """دریافت لاگ امنیتی"""
        return self.security_log[-limit:]
    
    async def cleanup(self):
        """پاک‌سازی منابع"""
        self.logger.info("🧹 Cleaning up Auth Manager resources...")
        self.verification_codes.clear()
        self.totp_secrets.clear()

# نمونه سینگلتون برای استفاده در سراسر سیستم
auth_manager = AuthManager()
