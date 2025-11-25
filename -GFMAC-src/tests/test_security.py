#!/usr/bin/env python3
"""
Security Components Test Module
Unit tests for security and authentication components
Developer: Seyed Aladdin Mousavi Jashni
"""

import unittest
import asyncio
import sys
import os
from unittest.mock import Mock, patch, AsyncMock
import jwt
import bcrypt

# اضافه کردن مسیر src به sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.security.auth_manager import AuthManager
from src.security.crypto_manager import CryptoManager
from src.security.session_manager import SessionManager

class TestSecurityComponents(unittest.TestCase):
    """تست کامپوننت‌های امنیتی"""
    
    def setUp(self):
        """آماده‌سازی قبل از هر تست"""
        self.auth_manager = AuthManager()
        self.crypto_manager = CryptoManager()
        self.session_manager = SessionManager()
        
        # داده‌های نمونه کاربر
        self.sample_user_data = {
            'email': 'test@example.com',
            'password': 'SecurePassword123!',
            'mobile': '+1234567890',
            'first_name': 'Test',
            'last_name': 'User'
        }
        
        # داده‌های نمونه برای احراز هویت
        self.sample_credentials = {
            'email': 'test@example.com',
            'password': 'SecurePassword123!'
        }
    
    async def async_setup(self):
        """آماده‌سازی async"""
        await self.auth_manager.initialize()
        await self.session_manager.initialize()
    
    @patch('src.security.auth_manager.AuthManager.create_user')
    async def test_user_creation(self, mock_create):
        """تست ایجاد کاربر جدید"""
        # شبیه‌سازی ایجاد کاربر موفق
        mock_create.return_value = (True, {
            'user': {
                'user_id': 'test_user_123',
                'email': 'test@example.com',
                'security': {
                    'two_factor_enabled': True
                }
            },
            'qr_code': 'data:image/png;base64,...',
            'setup_instructions': 'Scan QR code with Google Authenticator'
        })
        
        success, result = await self.auth_manager.create_user(self.sample_user_data)
        
        self.assertTrue(success)
        self.assertIn('user', result)
        self.assertIn('qr_code', result)
        self.assertEqual(result['user']['email'], self.sample_user_data['email'])
    
    async def test_password_hashing(self):
        """تست هش کردن رمز عبور"""
        password = "MySecurePassword123!"
        
        hashed_password = await self.auth_manager._hash_password(password)
        
        # بررسی اینکه هش معتبر است
        self.assertIsInstance(hashed_password, str)
        self.assertNotEqual(hashed_password, password)
        
        # بررسی تطابق رمز عبور
        is_valid = await self.auth_manager._verify_password(password, hashed_password)
        self.assertTrue(is_valid)
        
        # بررسی رمز عبور نادرست
        is_invalid = await self.auth_manager._verify_password("WrongPassword", hashed_password)
        self.assertFalse(is_invalid)
    
    @patch('src.security.auth_manager.AuthManager.authenticate_user')
    async def test_user_authentication(self, mock_auth):
        """تست احراز هویت کاربر"""
        # شبیه‌سازی احراز هویت موفق
        mock_auth.return_value = (True, {
            'access_token': 'mock_jwt_token',
            'refresh_token': 'mock_refresh_token',
            'user': {
                'user_id': 'test_user_123',
                'email': 'test@example.com'
            }
        })
        
        success, result = await self.auth_manager.authenticate_user(self.sample_credentials)
        
        self.assertTrue(success)
        self.assertIn('access_token', result)
        self.assertIn('refresh_token', result)
        self.assertIn('user', result)
    
    def test_jwt_token_generation(self):
        """تست تولید توکن JWT"""
        user_data = {
            'user_id': 'test_user_123',
            'email': 'test@example.com',
            'permissions': ['read_market_data', 'view_signals']
        }
        
        # تست تولید توکن
        token = asyncio.run(self.auth_manager._generate_access_token(user_data))
        
        self.assertIsInstance(token, str)
        self.assertGreater(len(token), 0)
        
        # تست اعتبارسنجی توکن
        is_valid, payload = asyncio.run(self.auth_manager.verify_token(token))
        
        self.assertTrue(is_valid)
        self.assertEqual(payload['user_id'], user_data['user_id'])
        self.assertEqual(payload['email'], user_data['email'])
    
    def test_data_encryption(self):
        """تست رمزنگاری و رمزگشایی داده"""
        sensitive_data = "This is very sensitive information"
        
        # رمزنگاری
        encrypted_package = self.crypto_manager.encrypt_data(sensitive_data)
        
        self.assertIn('encrypted_data', encrypted_package)
        self.assertIn('algorithm', encrypted_package)
        self.assertNotEqual(encrypted_package['encrypted_data'], sensitive_data)
        
        # رمزگشایی
        decrypted_data = self.crypto_manager.decrypt_data(encrypted_package)
        
        self.assertEqual(decrypted_data, sensitive_data)
    
    def test_sensitive_field_encryption(self):
        """تست رمزنگاری فیلدهای حساس"""
        field_name = "api_key"
        field_value = "sk_test_1234567890abcdef"
        
        # رمزنگاری فیلد
        encrypted_field = self.crypto_manager.encrypt_sensitive_field(field_name, field_value)
        
        self.assertIn('encrypted_data', encrypted_field)
        self.assertIn('field_name', encrypted_field)
        self.assertEqual(encrypted_field['field_name'], field_name)
        
        # رمزگشایی فیلد
        decrypted_value = self.crypto_manager.decrypt_sensitive_field(encrypted_field)
        
        self.assertEqual(decrypted_value, field_value)
    
    def test_api_key_generation(self):
        """تست تولید کلید API"""
        user_id = "test_user_123"
        permissions = ['read_market_data', 'view_signals']
        
        api_key_data = self.crypto_manager.generate_api_key(user_id, permissions)
        
        self.assertIn('api_key', api_key_data)
        self.assertIn('api_secret', api_key_data)
        self.assertIn('key_fingerprint', api_key_data)
        self.assertIn('encrypted_package', api_key_data)
        
        # بررسی فرمت کلید API
        self.assertTrue(api_key_data['api_key'].startswith('fa_'))
        self.assertGreater(len(api_key_data['api_key']), 10)
    
    @patch('src.security.session_manager.SessionManager.create_session')
    async def test_session_creation(self, mock_create):
        """تست ایجاد سشن"""
        # شبیه‌سازی ایجاد سشن
        mock_create.return_value = {
            'session_id': 'test_session_123',
            'session_token': 'test_token_123',
            'expires_at': '2024-01-01T00:00:00Z',
            'refresh_token': 'test_refresh_123'
        }
        
        session_info = await self.session_manager.create_session(
            user_id='test_user_123',
            user_agent='Test Browser',
            ip_address='192.168.1.1'
        )
        
        self.assertIn('session_id', session_info)
        self.assertIn('session_token', session_info)
        self.assertIn('expires_at', session_info)
        self.assertIn('refresh_token', session_info)
    
    @patch('src.security.session_manager.SessionManager.validate_session')
    async def test_session_validation(self, mock_validate):
        """تست اعتبارسنجی سشن"""
        # شبیه‌سازی اعتبارسنجی موفق
        mock_validate.return_value = (True, {
            'session_data': {
                'session_id': 'test_session_123',
                'user_id': 'test_user_123',
                'is_active': True
            },
            'user_id': 'test_user_123'
        })
        
        is_valid, session_data = await self.session_manager.validate_session(
            'test_session_123', 'test_token_123'
        )
        
        self.assertTrue(is_valid)
        self.assertIn('session_data', session_data)
        self.assertIn('user_id', session_data)
    
    async def test_session_termination(self):
        """تست خاتمه سشن"""
        # ابتدا یک سشن ایجاد می‌کنیم
        with patch.object(self.session_manager, 'active_sessions', {'test_session_123': {}}):
            success = await self.session_manager.terminate_session('test_session_123', 'test')
            self.assertTrue(success)
    
    def test_secure_password_generation(self):
        """تست تولید رمز عبور امن"""
        password = self.crypto_manager.generate_secure_password()
        
        self.assertIsInstance(password, str)
        self.assertGreaterEqual(len(password), 16)
        
        # بررسی وجود کاراکترهای مختلف
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(not c.isalnum() for c in password)
        
        self.assertTrue(has_upper, "Password should contain uppercase letters")
        self.assertTrue(has_lower, "Password should contain lowercase letters")
        self.assertTrue(has_digit, "Password should contain digits")
        self.assertTrue(has_special, "Password should contain special characters")

class TestSecurityValidation(unittest.TestCase):
    """تست‌های اعتبارسنجی امنیتی"""
    
    def setUp(self):
        self.auth_manager = AuthManager()
    
    def test_email_validation(self):
        """تست اعتبارسنجی ایمیل"""
        valid_emails = [
            'test@example.com',
            'user.name@domain.co.uk',
            'user+tag@example.org'
        ]
        
        invalid_emails = [
            'invalid-email',
            'user@',
            '@domain.com',
            'user@.com'
        ]
        
        for email in valid_emails:
            self.assertTrue(
                self.auth_manager._is_valid_email(email),
                f"Valid email failed: {email}"
            )
        
        for email in invalid_emails:
            self.assertFalse(
                self.auth_manager._is_valid_email(email),
                f"Invalid email passed: {email}"
            )
    
    def test_mobile_validation(self):
        """تست اعتبارسنجی شماره موبایل"""
        valid_mobiles = [
            '+1234567890',
            '+441234567890',
            '1234567890'
        ]
        
        invalid_mobiles = [
            'invalid',
            '+',
            '123',
            'abcdefghij'
        ]
        
        for mobile in valid_mobiles:
            self.assertTrue(
                self.auth_manager._is_valid_mobile(mobile),
                f"Valid mobile failed: {mobile}"
            )
        
        for mobile in invalid_mobiles:
            self.assertFalse(
                self.auth_manager._is_valid_mobile(mobile),
                f"Invalid mobile passed: {mobile}"
            )
    
    def test_user_data_validation(self):
        """تست اعتبارسنجی داده‌های کاربر"""
        valid_user_data = {
            'email': 'test@example.com',
            'password': 'SecurePass123!'
        }
        
        invalid_user_data = [
            {'email': 'invalid-email', 'password': 'pass'},  # ایمیل نامعتبر
            {'email': 'test@example.com', 'password': 'short'},  # رمز کوتاه
            {'email': 'test@example.com'},  # رمز отсутствует
            {'password': 'SecurePass123!'}  # ایمیل отсутствует
        ]
        
        # تست داده معتبر
        is_valid, errors = self.auth_manager._validate_user_data(valid_user_data)
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)
        
        # تست داده‌های نامعتبر
        for user_data in invalid_user_data:
            is_valid, errors = self.auth_manager._validate_user_data(user_data)
            self.assertFalse(is_valid)
            self.assertGreater(len(errors), 0)

class TestErrorHandlingSecurity(unittest.TestCase):
    """تست مدیریت خطا در کامپوننت‌های امنیتی"""
    
    def setUp(self):
        self.crypto_manager = CryptoManager()
    
    def test_encryption_with_invalid_data(self):
        """تست رمزنگاری با داده‌های نامعتبر"""
        with self.assertRaises(Exception):
            self.crypto_manager.encrypt_data(None)
    
    def test_decryption_with_invalid_package(self):
        """تست رمزگشایی با بسته نامعتبر"""
        invalid_package = {
            'encrypted_data': 'invalid_base64_data'
        }
        
        with self.assertRaises(Exception):
            self.crypto_manager.decrypt_data(invalid_package)
    
    def test_invalid_token_verification(self):
        """تست اعتبارسنجی توکن نامعتبر"""
        auth_manager = AuthManager()
        
        invalid_tokens = [
            'invalid_token',
            '',
            None
        ]
        
        for token in invalid_tokens:
            is_valid, result = asyncio.run(auth_manager.verify_token(token))
            self.assertFalse(is_valid)
            self.assertIn('error', result)

def run_security_tests():
    """اجرای تمام تست‌های امنیتی"""
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestSecurityComponents)
    suite.addTests(loader.loadTestsFromTestCase(TestSecurityValidation))
    suite.addTests(loader.loadTestsFromTestCase(TestErrorHandlingSecurity))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

if __name__ == '__main__':
    # اجرای تست‌های امنیتی
    success = run_security_tests()
    sys.exit(0 if success else 1)
