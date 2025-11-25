#!/usr/bin/env python3
"""
API Middleware Module
Security and Logging Middleware
Developer: Seyed Aladdin Mousavi Jashni
"""

import time
import logging
from fastapi import Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Dict, List, Optional
import json

from src.security.auth_manager import auth_manager
from src.security.session_manager import session_manager
from src.utils.logger import security_logger

class SecurityMiddleware(BaseHTTPMiddleware):
    """میدلور امنیتی برای احراز هویت و اعتبارسنجی"""
    
    def __init__(self, app):
        super().__init__(app)
        self.logger = logging.getLogger(__name__)
        
        # مسیرهای عمومی که نیاز به احراز هویت ندارند
        self.public_paths = {
            '/api/docs',
            '/api/redoc', 
            '/api/openapi.json',
            '/api/health',
            '/api/auth/login',
            '/api/auth/register',
            '/api/auth/verify-sms'
        }
    
    async def dispatch(self, request: Request, call_next):
        """پردازش درخواست‌های ورودی"""
        
        # بررسی مسیرهای عمومی
        if request.url.path in self.public_paths:
            return await call_next(request)
        
        # استخراج توکن از هدر
        auth_header = request.headers.get('authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return Response(
                content=json.dumps({'error': 'Authorization header required'}),
                status_code=401,
                media_type='application/json'
            )
        
        token = auth_header[7:]  # حذف 'Bearer '
        
        try:
            # اعتبارسنجی توکن
            is_valid, token_data = await auth_manager.verify_token(token)
            if not is_valid:
                return Response(
                    content=json.dumps({'error': 'Invalid token'}),
                    status_code=401,
                    media_type='application/json'
                )
            
            # بررسی سشن
            session_id = request.headers.get('x-session-id')
            if session_id:
                session_valid, session_data = await session_manager.validate_session(
                    session_id, token
                )
                if not session_valid:
                    return Response(
                        content=json.dumps({'error': 'Invalid session'}),
                        status_code=401,
                        media_type='application/json'
                    )
            
            # اضافه کردن اطلاعات کاربر به request
            request.state.user_id = token_data.get('user_id')
            request.state.user_permissions = token_data.get('permissions', [])
            request.state.token_data = token_data
            
            # ثبت لاگ امنیتی
            security_logger.log_api_call(
                request.url.path,
                request.method,
                token_data.get('user_id', 'unknown')
            )
            
            # ادامه پردازش درخواست
            response = await call_next(request)
            return response
            
        except Exception as e:
            self.logger.error(f"Security middleware error: {e}")
            return Response(
                content=json.dumps({'error': 'Authentication failed'}),
                status_code=500,
                media_type='application/json'
            )

class LoggingMiddleware(BaseHTTPMiddleware):
    """میدلور لاگ‌گیری برای ردیابی درخواست‌ها"""
    
    def __init__(self, app):
        super().__init__(app)
        self.logger = logging.getLogger(__name__)
    
    async def dispatch(self, request: Request, call_next):
        """لاگ‌گیری درخواست‌ها و پاسخ‌ها"""
        
        start_time = time.time()
        
        # اطلاعات درخواست
        client_ip = request.client.host if request.client else 'unknown'
        user_agent = request.headers.get('user-agent', 'unknown')
        method = request.method
        path = request.url.path
        query_params = str(request.query_params)
        
        # لاگ درخواست
        self.logger.info(
            f"🌐 REQUEST: {method} {path} | IP: {client_ip} | "
            f"User-Agent: {user_agent[:50]}... | Query: {query_params[:100]}..."
        )
        
        try:
            # پردازش درخواست
            response = await call_next(request)
            
            # محاسبه زمان اجرا
            process_time = time.time() - start_time
            
            # اطلاعات پاسخ
            status_code = response.status_code
            content_length = response.headers.get('content-length', 0)
            
            # لاگ پاسخ
            self.logger.info(
                f"✅ RESPONSE: {method} {path} | Status: {status_code} | "
                f"Time: {process_time:.3f}s | Size: {content_length} bytes"
            )
            
            # اضافه کردن هدرهای مفید
            response.headers['x-process-time'] = str(process_time)
            response.headers['x-request-id'] = self._generate_request_id()
            
            return response
            
        except Exception as e:
            # لاگ خطا
            process_time = time.time() - start_time
            self.logger.error(
                f"❌ ERROR: {method} {path} | Time: {process_time:.3f}s | "
                f"Error: {str(e)}"
            )
            raise
    
    def _generate_request_id(self) -> str:
        """تولید شناسه یکتا برای درخواست"""
        import secrets
        return f"req_{secrets.token_hex(8)}"

class RateLimitMiddleware(BaseHTTPMiddleware):
    """میدلور محدودیت نرخ درخواست"""
    
    def __init__(self, app, max_requests: int = 100, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests_log: Dict[str, List[float]] = {}
        self.logger = logging.getLogger(__name__)
    
    async def dispatch(self, request: Request, call_next):
        """اعمال محدودیت نرخ درخواست"""
        
        client_ip = request.client.host if request.client else 'unknown'
        
        # مسیرهای معاف از محدودیت
        exempt_paths = {'/api/health', '/api/docs'}
        if request.url.path in exempt_paths:
            return await call_next(request)
        
        # بررسی محدودیت
        if not self._check_rate_limit(client_ip):
            self.logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            return Response(
                content=json.dumps({
                    'error': 'Rate limit exceeded',
                    'message': f'Maximum {self.max_requests} requests per {self.window_seconds} seconds'
                }),
                status_code=429,
                media_type='application/json'
            )
        
        return await call_next(request)
    
    def _check_rate_limit(self, client_ip: str) -> bool:
        """بررسی محدودیت نرخ برای IP مشخص"""
        now = time.time()
        
        # پاک‌سازی درخواست‌های قدیمی
        if client_ip in self.requests_log:
            self.requests_log[client_ip] = [
                req_time for req_time in self.requests_log[client_ip]
                if now - req_time < self.window_seconds
            ]
        
        # اضافه کردن درخواست فعلی
        if client_ip not in self.requests_log:
            self.requests_log[client_ip] = []
        
        self.requests_log[client_ip].append(now)
        
        # بررسی تعداد درخواست‌ها
        return len(self.requests_log[client_ip]) <= self.max_requests

class ValidationMiddleware(BaseHTTPMiddleware):
    """میدلور اعتبارسنجی داده‌های ورودی"""
    
    def __init__(self, app):
        super().__init__(app)
        self.logger = logging.getLogger(__name__)
    
    async def dispatch(self, request: Request, call_next):
        """اعتبارسنجی داده‌های ورودی"""
        
        # فقط برای درخواست‌های POST, PUT, PATCH
        if request.method in ['POST', 'PUT', 'PATCH']:
            try:
                # خواندن body
                body = await request.body()
                
                if body:
                    # اعتبارسنجی JSON
                    try:
                        json_data = json.loads(body)
                        request.state.validated_body = json_data
                    except json.JSONDecodeError:
                        return Response(
                            content=json.dumps({'error': 'Invalid JSON format'}),
                            status_code=400,
                            media_type='application/json'
                        )
                
            except Exception as e:
                self.logger.error(f"Validation error: {e}")
                return Response(
                    content=json.dumps({'error': 'Request validation failed'}),
                    status_code=400,
                    media_type='application/json'
                )
        
        return await call_next(request)

def setup_cors_middleware(app):
    """تنظیم میدلور CORS"""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://127.0.0.1:3000", 
            "https://financial-analyzer.pro"
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["x-process-time", "x-request-id"]
    )

def setup_trusted_hosts_middleware(app):
    """تنظیم میدلور میزبان‌های معتبر"""
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=[
            "localhost",
            "127.0.0.1",
            "financial-analyzer.pro",
            "*.financial-analyzer.pro"
        ]
    )

def setup_custom_middlewares(app):
    """تنظیم تمام میدلورهای سفارشی"""
    
    # میدلورهای امنیتی
    app.add_middleware(SecurityMiddleware)
    app.add_middleware(RateLimitMiddleware, max_requests=100, window_seconds=60)
    
    # میدلورهای utility
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(ValidationMiddleware)
    
    # میدلورهای استاندارد
    setup_cors_middleware(app)
    setup_trusted_hosts_middleware(app)
    
    logging.info("✅ All API middlewares configured successfully")
