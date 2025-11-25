#!/usr/bin/env python3
"""
Session Manager Module
Advanced Session Management and Security
Developer: Seyed Aladdin Mousavi Jashni
"""

import asyncio
import logging
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
import json
import hashlib

class SessionManager:
    """مدیریت پیشرفته سشن‌های کاربر با امنیت بالا"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # ذخیره‌سازی سشن‌ها
        self.active_sessions = {}
        self.session_metadata = {}
        
        # تنظیمات سشن
        self.session_config = {
            'max_sessions_per_user': 5,
            'session_timeout': timedelta(hours=24),
            'refresh_interval': timedelta(hours=1),
            'cleanup_interval': timedelta(minutes=30)
        }
        
        # لاگ فعالیت‌های سشن
        self.session_log = []
    
    async def initialize(self):
        """مقداردهی اولیه مدیر سشن"""
        self.logger.info("🔐 Initializing Session Manager...")
        self.logger.info(f"⏰ Session timeout: {self.session_config['session_timeout']}")
        self.logger.info(f"🔄 Refresh interval: {self.session_config['refresh_interval']}")
        
        # شروع تمیزکاری دوره‌ای
        asyncio.create_task(self._periodic_cleanup())
    
    async def create_session(self, user_id: str, user_agent: str = "", 
                           ip_address: str = "") -> Dict:
        """
        ایجاد سشن جدید برای کاربر
        
        Args:
            user_id: شناسه کاربر
            user_agent: اطلاعات مرورگر کاربر
            ip_address: آدرس IP
            
        Returns:
            Dict: اطلاعات سشن ایجاد شده
        """
        try:
            # بررسی تعداد سشن‌های فعال کاربر
            user_sessions = self._get_user_sessions(user_id)
            if len(user_sessions) >= self.session_config['max_sessions_per_user']:
                # حذف قدیمی‌ترین سشن
                await self._remove_oldest_session(user_id)
            
            # تولید شناسه سشن یکتا
            session_id = self._generate_session_id()
            
            # تولید توکن سشن
            session_token = self._generate_session_token()
            
            # زمان‌های سشن
            created_at = datetime.now()
            expires_at = created_at + self.session_config['session_timeout']
            
            # ایجاد سشن
            session_data = {
                'session_id': session_id,
                'user_id': user_id,
                'session_token': session_token,
                'created_at': created_at.isoformat(),
                'expires_at': expires_at.isoformat(),
                'last_activity': created_at.isoformat(),
                'user_agent': user_agent,
                'ip_address': ip_address,
                'is_active': True,
                'refresh_count': 0
            }
            
            # ذخیره سشن
            self.active_sessions[session_id] = session_data
            
            # ذخیره metadata
            self.session_metadata[session_id] = {
                'access_times': [created_at],
                'request_count': 0,
                'data_accessed': set(),
                'permissions_used': set()
            }
            
            self._log_session_event('SESSION_CREATED', session_id, user_id, 
                                  f"New session created from {ip_address}")
            
            self.logger.info(f"✅ Session created for user {user_id}")
            
            return {
                'session_id': session_id,
                'session_token': session_token,
                'expires_at': expires_at.isoformat(),
                'refresh_token': self._generate_refresh_token(session_id)
            }
            
        except Exception as e:
            self.logger.error(f"❌ Session creation failed: {e}")
            raise
    
    async def validate_session(self, session_id: str, session_token: str, 
                             required_permissions: List[str] = None) -> Tuple[bool, Dict]:
        """
        اعتبارسنجی سشن
        
        Args:
            session_id: شناسه سشن
            session_token: توکن سشن
            required_permissions: مجوزهای مورد نیاز
            
        Returns:
            Tuple[bool, Dict]: (معتبر بودن, اطلاعات سشن)
        """
        try:
            # بررسی وجود سشن
            if session_id not in self.active_sessions:
                self._log_session_event('SESSION_NOT_FOUND', session_id, 'unknown')
                return False, {'error': 'Session not found'}
            
            session_data = self.active_sessions[session_id]
            
            # بررسی فعال بودن سشن
            if not session_data.get('is_active', False):
                self._log_session_event('SESSION_INACTIVE', session_id, session_data['user_id'])
                return False, {'error': 'Session is not active'}
            
            # بررسی انقضای سشن
            if self._is_session_expired(session_data):
                await self.terminate_session(session_id, 'expired')
                self._log_session_event('SESSION_EXPIRED', session_id, session_data['user_id'])
                return False, {'error': 'Session expired'}
            
            # بررسی تطابق توکن
            if session_data.get('session_token') != session_token:
                self._log_session_event('INVALID_TOKEN', session_id, session_data['user_id'])
                return False, {'error': 'Invalid session token'}
            
            # بررسی مجوزها
            if required_permissions:
                has_permissions = await self._check_permissions(
                    session_data['user_id'], required_permissions
                )
                if not has_permissions:
                    self._log_session_event('INSUFFICIENT_PERMISSIONS', session_id, session_data['user_id'])
                    return False, {'error': 'Insufficient permissions'}
            
            # به‌روزرسانی آخرین فعالیت
            await self._update_session_activity(session_id)
            
            # افزایش شماره درخواست‌ها
            self.session_metadata[session_id]['request_count'] += 1
            
            self._log_session_event('SESSION_VALIDATED', session_id, session_data['user_id'])
            
            return True, {
                'session_data': session_data,
                'user_id': session_data['user_id'],
                'permissions': await self._get_user_permissions(session_data['user_id'])
            }
            
        except Exception as e:
            self.logger.error(f"❌ Session validation failed: {e}")
            return False, {'error': 'Session validation failed'}
    
    async def refresh_session(self, session_id: str, refresh_token: str) -> Tuple[bool, Dict]:
        """
        تمدید سشن
        
        Args:
            session_id: شناسه سشن
            refresh_token: توکن تمدید
            
        Returns:
            Tuple[bool, Dict]: (موفقیت, اطلاعات سشن جدید)
        """
        try:
            # بررسی وجود سشن
            if session_id not in self.active_sessions:
                return False, {'error': 'Session not found'}
            
            session_data = self.active_sessions[session_id]
            
            # بررسی توکن تمدید
            expected_refresh_token = self._generate_refresh_token(session_id)
            if refresh_token != expected_refresh_token:
                self._log_session_event('INVALID_REFRESH_TOKEN', session_id, session_data['user_id'])
                return False, {'error': 'Invalid refresh token'}
            
            # بررسی تعداد تمدیدها
            if session_data.get('refresh_count', 0) >= 10:
                await self.terminate_session(session_id, 'max_refresh_reached')
                return False, {'error': 'Maximum refresh count reached'}
            
            # تمدید سشن
            new_expires_at = datetime.now() + self.session_config['session_timeout']
            session_data['expires_at'] = new_expires_at.isoformat()
            session_data['last_activity'] = datetime.now().isoformat()
            session_data['refresh_count'] = session_data.get('refresh_count', 0) + 1
            
            # تولید توکن جدید
            new_session_token = self._generate_session_token()
            session_data['session_token'] = new_session_token
            
            self._log_session_event('SESSION_REFRESHED', session_id, session_data['user_id'])
            
            return True, {
                'session_token': new_session_token,
                'expires_at': new_expires_at.isoformat(),
                'refresh_token': self._generate_refresh_token(session_id)
            }
            
        except Exception as e:
            self.logger.error(f"❌ Session refresh failed: {e}")
            return False, {'error': 'Session refresh failed'}
    
    async def terminate_session(self, session_id: str, reason: str = "user_request") -> bool:
        """
        خاتمه سشن
        
        Args:
            session_id: شناسه سشن
            reason: دلیل خاتمه
            
        Returns:
            bool: موفقیت عملیات
        """
        try:
            if session_id not in self.active_sessions:
                return False
            
            session_data = self.active_sessions[session_id]
            user_id = session_data['user_id']
            
            # غیرفعال کردن سشن
            session_data['is_active'] = False
            session_data['terminated_at'] = datetime.now().isoformat()
            session_data['termination_reason'] = reason
            
            # حذف از سشن‌های فعال
            del self.active_sessions[session_id]
            
            # حذف metadata
            if session_id in self.session_metadata:
                del self.session_metadata[session_id]
            
            self._log_session_event('SESSION_TERMINATED', session_id, user_id, f"Reason: {reason}")
            self.logger.info(f"✅ Session {session_id} terminated for user {user_id}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Session termination failed: {e}")
            return False
    
    async def terminate_all_user_sessions(self, user_id: str, 
                                        exclude_session_id: str = None) -> int:
        """
        خاتمه تمام سشن‌های کاربر
        
        Args:
            user_id: شناسه کاربر
            exclude_session_id: سشن معاف از خاتمه
            
        Returns:
            int: تعداد سشن‌های خاتمه یافته
        """
        try:
            terminated_count = 0
            user_sessions = self._get_user_sessions(user_id)
            
            for session_id in user_sessions:
                if session_id == exclude_session_id:
                    continue
                
                if await self.terminate_session(session_id, 'user_logout_all'):
                    terminated_count += 1
            
            self._log_session_event('ALL_SESSIONS_TERMINATED', 'multiple', user_id,
                                  f"Terminated {terminated_count} sessions")
            
            return terminated_count
            
        except Exception as e:
            self.logger.error(f"❌ Terminate all sessions failed: {e}")
            return 0
    
    async def get_session_info(self, session_id: str) -> Optional[Dict]:
        """دریافت اطلاعات سشن"""
        if session_id not in self.active_sessions:
            return None
        
        session_data = self.active_sessions[session_id].copy()
        metadata = self.session_metadata.get(session_id, {}).copy()
        
        # ترکیب اطلاعات
        session_info = {
            **session_data,
            'metadata': {
                'request_count': metadata.get('request_count', 0),
                'last_access_times': [
                    t.isoformat() for t in metadata.get('access_times', [])
                ],
                'data_accessed': list(metadata.get('data_accessed', set())),
                'permissions_used': list(metadata.get('permissions_used', set()))
            }
        }
        
        return session_info
    
    async def get_user_sessions(self, user_id: str) -> List[Dict]:
        """دریافت تمام سشن‌های کاربر"""
        user_sessions = []
        
        for session_id, session_data in self.active_sessions.items():
            if session_data['user_id'] == user_id and session_data.get('is_active', False):
                session_info = await self.get_session_info(session_id)
                if session_info:
                    user_sessions.append(session_info)
        
        return user_sessions
    
    async def update_session_data(self, session_id: str, data: Dict) -> bool:
        """به‌روزرسانی داده‌های سشن"""
        try:
            if session_id not in self.active_sessions:
                return False
            
            # به‌روزرسانی داده‌ها
            self.active_sessions[session_id].update(data)
            
            # به‌روزرسانی آخرین فعالیت
            await self._update_session_activity(session_id)
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Session data update failed: {e}")
            return False
    
    def _generate_session_id(self) -> str:
        """تولید شناسه سشن یکتا"""
        return f"sess_{secrets.token_hex(16)}"
    
    def _generate_session_token(self) -> str:
        """تولید توکن سشن"""
        return secrets.token_urlsafe(32)
    
    def _generate_refresh_token(self, session_id: str) -> str:
        """تولید توکن تمدید"""
        # استفاده از هش برای امنیت بیشتر
        base_string = f"{session_id}_{secrets.token_hex(8)}"
        return hashlib.sha256(base_string.encode()).hexdigest()[:32]
    
    def _get_user_sessions(self, user_id: str) -> List[str]:
        """دریافت شناسه سشن‌های کاربر"""
        return [
            session_id for session_id, session_data in self.active_sessions.items()
            if session_data['user_id'] == user_id and session_data.get('is_active', False)
        ]
    
    async def _remove_oldest_session(self, user_id: str) -> bool:
        """حذف قدیمی‌ترین سشن کاربر"""
        user_sessions = self._get_user_sessions(user_id)
        
        if not user_sessions:
            return False
        
        # پیدا کردن سشن با قدیمی‌ترین فعالیت
        oldest_session = min(
            user_sessions,
            key=lambda sid: self.active_sessions[sid]['last_activity']
        )
        
        return await self.terminate_session(oldest_session, 'session_limit_reached')
    
    def _is_session_expired(self, session_data: Dict) -> bool:
        """بررسی انقضای سشن"""
        try:
            expires_at = datetime.fromisoformat(session_data['expires_at'])
            return datetime.now() > expires_at
        except (ValueError, KeyError):
            return True
    
    async def _update_session_activity(self, session_id: str):
        """به‌روزرسانی زمان آخرین فعالیت"""
        if session_id not in self.active_sessions:
            return
        
        now = datetime.now()
        self.active_sessions[session_id]['last_activity'] = now.isoformat()
        
        # به‌روزرسانی metadata
        if session_id in self.session_metadata:
            self.session_metadata[session_id]['access_times'].append(now)
            
            # حفظ فقط ۱۰ تاریخ آخرین دسترسی
            access_times = self.session_metadata[session_id]['access_times']
            if len(access_times) > 10:
                self.session_metadata[session_id]['access_times'] = access_times[-10:]
    
    async def _check_permissions(self, user_id: str, required_permissions: List[str]) -> bool:
        """بررسی مجوزهای کاربر"""
        # اینجا باید از سیستم مدیریت مجوزها استفاده شود
        # برای نمونه، همیشه True برمی‌گردانیم
        user_permissions = await self._get_user_permissions(user_id)
        return all(perm in user_permissions for perm in required_permissions)
    
    async def _get_user_permissions(self, user_id: str) -> Set[str]:
        """دریافت مجوزهای کاربر"""
        # اینجا باید از دیتابیس خوانده شود
        # برای نمونه، یک مجموعه پیش‌فرض برمی‌گردانیم
        return {
            'read_market_data',
            'view_signals',
            'access_basic_analysis',
            'manage_own_portfolio'
        }
    
    async def _periodic_cleanup(self):
        """تمیزکاری دوره‌ای سشن‌های منقضی"""
        while True:
            try:
                await asyncio.sleep(self.session_config['cleanup_interval'].total_seconds())
                await self._cleanup_expired_sessions()
            except Exception as e:
                self.logger.error(f"❌ Periodic cleanup failed: {e}")
    
    async def _cleanup_expired_sessions(self):
        """حذف سشن‌های منقضی شده"""
        expired_sessions = []
        
        for session_id, session_data in self.active_sessions.items():
            if self._is_session_expired(session_data):
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            await self.terminate_session(session_id, 'auto_cleanup')
        
        if expired_sessions:
            self.logger.info(f"🧹 Cleaned up {len(expired_sessions)} expired sessions")
    
    def _log_session_event(self, event_type: str, session_id: str, 
                          user_id: str = None, details: str = ""):
        """ثبت رویداد سشن"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type,
            'session_id': session_id,
            'user_id': user_id,
            'details': details,
            'ip_address': self.active_sessions.get(session_id, {}).get('ip_address', 'unknown')
        }
        
        self.session_log.append(log_entry)
        
        # لاگ کردن رویدادهای مهم
        if event_type in ['SESSION_CREATED', 'SESSION_TERMINATED', 'INVALID_TOKEN']:
            self.logger.info(f"🔐 SESSION: {event_type} - User: {user_id} - {details}")
    
    async def get_session_logs(self, user_id: str = None, limit: int = 100) -> List[Dict]:
        """دریافت لاگ سشن‌ها"""
        logs = self.session_log
        
        if user_id:
            logs = [log for log in logs if log.get('user_id') == user_id]
        
        return logs[-limit:]
    
    async def get_session_stats(self) -> Dict:
        """دریافت آمار سشن‌ها"""
        active_sessions = len(self.active_sessions)
        
        # گروه‌بندی بر اساس کاربر
        users_with_sessions = set()
        for session_data in self.active_sessions.values():
            users_with_sessions.add(session_data['user_id'])
        
        # محاسبه سشن‌های منقضی شده
        expired_count = 0
        for session_data in self.active_sessions.values():
            if self._is_session_expired(session_data):
                expired_count += 1
        
        return {
            'total_active_sessions': active_sessions,
            'unique_users_with_sessions': len(users_with_sessions),
            'expired_sessions_pending_cleanup': expired_count,
            'total_session_events': len(self.session_log),
            'cleanup_interval_minutes': self.session_config['cleanup_interval'].total_seconds() / 60
        }
    
    async def cleanup(self):
        """پاک‌سازی منابع"""
        self.logger.info("🧹 Cleaning up Session Manager resources...")
        
        # خاتمه تمام سشن‌ها
        for session_id in list(self.active_sessions.keys()):
            await self.terminate_session(session_id, 'system_shutdown')
        
        self.session_log.clear()

# نمونه سینگلتون برای استفاده در سراسر سیستم
session_manager = SessionManager()
