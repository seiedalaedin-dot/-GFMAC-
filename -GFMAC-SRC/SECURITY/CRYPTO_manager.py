
Seyyedalaeddin Moussvi Jashmi <seiedalaedin@gmail.com>
1:54 PM (0 minutes ago)
to me

#!/usr/bin/env python3
"""
Crypto Manager Module
Advanced Data Encryption and Security
Developer: Seyed Aladdin Mousavi Jashni
"""

import logging
import secrets
import base64
import hashlib
from typing import Dict, Optional, Union
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend
import os

class CryptoManager:
    """مدیریت رمزنگاری پیشرفته برای داده‌های حساس"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.backend = default_backend()
        
        # کلیدهای رمزنگاری - در عمل باید از محیط امن خوانده شوند
        self.encryption_key = self._derive_key(
            os.getenv('ENCRYPTION_SECRET', 'default-encryption-secret-change-in-production')
        )
        
        self.fernet = Fernet(self.encryption_key)
    
    def _derive_key(self, password: str, salt: bytes = None) -> bytes:
        """اشتقاق کلید رمزنگاری از رمز عبور"""
        if salt is None:
            salt = os.urandom(16)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=self.backend
        )
        
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key
    
    def encrypt_data(self, data: Union[str, bytes], key: bytes = None) -> Dict[str, str]:
        """
        رمزنگاری داده‌ها با الگوریتم پیشرفته
        
        Args:
            data: داده برای رمزنگاری
            key: کلید رمزنگاری (اختیاری)
            
        Returns:
            Dict: داده رمزنگاری شده و metadata
        """
        try:
            if isinstance(data, str):
                data = data.encode('utf-8')
            
            # استفاده از Fernet برای رمزنگاری authenticated
            fernet = self.fernet if key is None else Fernet(key)
            encrypted_data = fernet.encrypt(data)
            
            result = {
                'encrypted_data': base64.urlsafe_b64encode(encrypted_data).decode('utf-8'),
                'algorithm': 'FERNET_AES128',
                'timestamp': self._get_current_timestamp()
            }
            
            self.logger.debug("✅ Data encrypted successfully")
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Encryption failed: {e}")
            raise
    
    def decrypt_data(self, encrypted_package: Dict, key: bytes = None) -> str:
        """
        رمزگشایی داده‌ها
        
        Args:
            encrypted_package: بسته رمزنگاری شده
            key: کلید رمزگشایی (اختیاری)
            
        Returns:
            str: داده رمزگشایی شده
        """
        try:
            encrypted_data = base64.urlsafe_b64decode(
                encrypted_package['encrypted_data'].encode('utf-8')
            )
            
            fernet = self.fernet if key is None else Fernet(key)
            decrypted_data = fernet.decrypt(encrypted_data)
            
            self.logger.debug("✅ Data decrypted successfully")
            return decrypted_data.decode('utf-8')
            
        except Exception as e:
            self.logger.error(f"❌ Decryption failed: {e}")
            raise
    
    def encrypt_sensitive_field(self, field_name: str, value: str) -> Dict[str, str]:
        """
        رمزنگاری فیلدهای حساس با metadata اضافی
        
        Args:
            field_name: نام فیلد
            value: مقدار فیلد
            
        Returns:
            Dict: فیلد رمزنگاری شده
        """
        try:
            # اضافه کردن metadata برای امنیت بیشتر
            metadata = {
                'field_name': field_name,
                'value': value,
                'encrypted_at': self._get_current_timestamp(),
                'version': '1.0'
            }
            
            metadata_str = self._dict_to_json(metadata)
            encrypted_result = self.encrypt_data(metadata_str)
            
            # اضافه کردن اطلاعات اضافی
            encrypted_result['field_name'] = field_name
            encrypted_result['original_length'] = len(value)
            
            return encrypted_result
            
        except Exception as e:
            self.logger.error(f"❌ Field encryption failed: {e}")
            raise
    
    def decrypt_sensitive_field(self, encrypted_field: Dict) -> str:
        """
        رمزگشایی فیلدهای حساس
        
        Args:
            encrypted_field: فیلد رمزنگاری شده
            
        Returns:
            str: مقدار اصلی
        """
        try:
            # رمزگشایی داده
            decrypted_data = self.decrypt_data(encrypted_field)
            metadata = self._json_to_dict(decrypted_data)
            
            # اعتبارسنجی metadata
            if not self._validate_metadata(metadata):
                raise ValueError("Invalid metadata in encrypted field")
            
            return metadata['value']
            
        except Exception as e:
            self.logger.error(f"❌ Field decryption failed: {e}")
            raise
    
    def generate_api_key(self, user_id: str, permissions: list) -> Dict[str, str]:
        """
        تولید کلید API امن
        
        Args:
            user_id: شناسه کاربر
            permissions: لیست مجوزها
            
        Returns:
            Dict: کلید API و اطلاعات مربوطه
        """
        try:
            # تولید کلید تصادفی
            api_key = f"fa_{secrets.token_hex(32)}"
            api_secret = secrets.token_urlsafe(64)
            
            # ایجاد fingerprint برای امنیت بیشتر
            key_fingerprint = self._generate_fingerprint(api_key)
            
            # بسته‌بندی اطلاعات کلید
            key_package = {
                'api_key': api_key,
                'api_secret_hash': self._hash_secret(api_secret),
                'key_fingerprint': key_fingerprint,
                'user_id': user_id,
                'permissions': permissions,
                'created_at': self._get_current_timestamp(),
                'expires_at': self._get_future_timestamp(days=365),
                'is_active': True
            }
            
            # رمزنگاری بسته کلید
            encrypted_package = self.encrypt_data(self._dict_to_json(key_package))
            
            self.logger.info(f"🔑 API key generated for user {user_id}")
            
            return {
                'api_key': api_key,
                'api_secret': api_secret,  # فقط یکبار نمایش داده می‌شود
                'key_fingerprint': key_fingerprint,
                'encrypted_package': encrypted_package,
                'warning': 'Store the API secret securely - it will not be shown again'
            }
            
        except Exception as e:
            self.logger.error(f"❌ API key generation failed: {e}")
            raise
    
    def verify_api_key(self, api_key: str, api_secret: str, stored_package: Dict) -> bool:
        """
        اعتبارسنجی کلید API
        
        Args:
            api_key: کلید API
            api_secret: رمز API
            stored_package: بسته ذخیره شده
            
        Returns:
            bool: معتبر بودن کلید
        """
        try:
            # رمزگشایی بسته کلید
            decrypted_data = self.decrypt_data(stored_package)
            key_data = self._json_to_dict(decrypted_data)
            
            # بررسی انقضا
            if self._is_expired(key_data.get('expires_at')):
                self.logger.warning("API key expired")
                return False
            
            # بررسی فعال بودن
            if not key_data.get('is_active', False):
                self.logger.warning("API key is not active")
                return False
            
            # بررسی تطابق کلید
            if key_data.get('api_key') != api_key:
                self.logger.warning("API key mismatch")
                return False
            
            # بررسی تطابق رمز
            secret_hash = self._hash_secret(api_secret)
            if not self._verify_secret_hash(secret_hash, key_data.get('api_secret_hash')):
                self.logger.warning("API secret mismatch")
                return False
            
            self.logger.debug("✅ API key verified successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ API key verification failed: {e}")
            return False
    
    def encrypt_file(self, file_path: str, output_path: str = None) -> str:
        """
        رمزنگاری فایل
        
        Args:
            file_path: مسیر فایل ورودی
            output_path: مسیر فایل خروجی (اختیاری)
            
        Returns:
            str: مسیر فایل رمزنگاری شده
        """
        try:
            if output_path is None:
                output_path = file_path + '.encrypted'
            
            # تولید IV تصادفی
            iv = os.urandom(16)
            
            # ایجاد cipher
            cipher = Cipher(algorithms.AES(self.encryption_key), modes.CBC(iv), backend=self.backend)
            encryptor = cipher.encryptor()
            
            # padding داده‌ها
            padder = padding.PKCS7(128).padder()
            
            with open(file_path, 'rb') as f_in, open(output_path, 'wb') as f_out:
                # نوشتن IV
                f_out.write(iv)
                
                # رمزنگاری بلوک‌ها
                while True:
                    chunk = f_in.read(8192)
                    if len(chunk) == 0:
                        break
                    elif len(chunk) % 16 != 0:
                        chunk = padder.update(chunk)
                    else:
                        chunk = encryptor.update(chunk)
                    
                    f_out.write(chunk)
                
                # finalize
                final_chunk = padder.finalize()
                if final_chunk:
                    f_out.write(encryptor.update(final_chunk))
                f_out.write(encryptor.finalize())
            
            self.logger.info(f"✅ File encrypted: {file_path} -> {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"❌ File encryption failed: {e}")
            raise
    
    def decrypt_file(self, file_path: str, output_path: str = None) -> str:
        """
        رمزگشایی فایل
        
        Args:
            file_path: مسیر فایل رمزنگاری شده
            output_path: مسیر فایل خروجی (اختیاری)
            
        Returns:
            str: مسیر فایل رمزگشایی شده
        """
        try:
            if output_path is None:
                output_path = file_path.replace('.encrypted', '.decrypted')
            
            with open(file_path, 'rb') as f_in, open(output_path, 'wb') as f_out:
                # خواندن IV
                iv = f_in.read(16)
                
                # ایجاد cipher
                cipher = Cipher(algorithms.AES(self.encryption_key), modes.CBC(iv), backend=self.backend)
                decryptor = cipher.decryptor()
                
                # unpadder
                unpadder = padding.PKCS7(128).unpadder()
                
                # رمزگشایی بلوک‌ها
                while True:
                    chunk = f_in.read(8192)
                    if len(chunk) == 0:
                        break
                    
                    decrypted_chunk = decryptor.update(chunk)
                    f_out.write(unpadder.update(decrypted_chunk))
                
                # finalize
                final_chunk = unpadder.finalize()
                if final_chunk:
                    f_out.write(final_chunk)
            
            self.logger.info(f"✅ File decrypted: {file_path} -> {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"❌ File decryption failed: {e}")
            raise
    
    def _generate_fingerprint(self, data: str) -> str:
        """تولید fingerprint برای داده"""
        return hashlib.sha256(data.encode()).hexdigest()[:16]
    
    def _hash_secret(self, secret: str) -> str:
        """هش کردن رمز عبور"""
        salt = os.urandom(32)
        return hashlib.pbkdf2_hmac(
            'sha256',
            secret.encode(),
            salt,
            100000
        ).hex()
    
    def _verify_secret_hash(self, input_hash: str, stored_hash: str) -> bool:
        """بررسی تطابق هش رمز عبور"""
        # این یک پیاده‌سازی ساده است
        # در عمل باید از روش‌های امن‌تری استفاده شود
        return input_hash == stored_hash
    
    def _get_current_timestamp(self) -> str:
        """دریافت timestamp فعلی"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def _get_future_timestamp(self, days: int = 30) -> str:
        """دریافت timestamp آینده"""
        from datetime import datetime, timedelta
        return (datetime.now() + timedelta(days=days)).isoformat()
    
    def _is_expired(self, timestamp: str) -> bool:
        """بررسی انقضای timestamp"""
        from datetime import datetime
        try:
            expiry_date = datetime.fromisoformat(timestamp)
            return datetime.now() > expiry_date
        except (ValueError, TypeError):
            return True
    
    def _dict_to_json(self, data: Dict) -> str:
        """تبدیل دیکشنری به JSON"""
        import json
        return json.dumps(data, ensure_ascii=False)
    
    def _json_to_dict(self, json_str: str) -> Dict:
        """تبدیل JSON به دیکشنری"""
        import json
        return json.loads(json_str)
    
    def _validate_metadata(self, metadata: Dict) -> bool:
        """اعتبارسنجی metadata"""
        required_fields = ['field_name', 'value', 'encrypted_at']
        return all(field in metadata for field in required_fields)
    
    def generate_secure_password(self, length: int = 16) -> str:
        """تولید رمز عبور امن"""
        import string
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    async def cleanup(self):
        """پاک‌سازی منابع"""
        self.logger.info("🧹 Cleaning up Crypto Manager resources...")
        # در اینجا می‌توان کلیدها را از حافظه پاک کرد

# نمونه سینگلتون برای استفاده در سراسر سیستم
crypto_manager = CryptoManager()
