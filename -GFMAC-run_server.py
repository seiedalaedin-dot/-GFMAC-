#!/usr/bin/env python3
"""
Financial Analyzer Pro - Main Server
FastAPI Server Entry Point
Developer: Seyed Aladdin Mousavi Jashni
"""

import uvicorn
import logging
import asyncio
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
import os
import sys

# اضافه کردن مسیر src به sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(current_dir, 'src')
sys.path.append(src_path)

from src.api.routes import api_router
from src.api.middleware import setup_custom_middlewares
from src.config import config
from src.utils.logger import setup_logging

# تنظیم لاگ‌گیری
logger = setup_logging("financial-analyzer-server")

# ایجاد اپلیکیشن FastAPI
app = FastAPI(
    title=config.APP_NAME,
    description="Advanced Financial Analysis Platform with Crisis Prediction and Trading Signals",
    version=config.VERSION,
    docs_url=None,  # غیرفعال کردن docs پیش‌فرض
    redoc_url=None,  # غیرفعال کردن redoc پیش‌فرض
    contact={
        "name": "Seyed Aladdin Mousavi Jashni",
        "email": "support@financial-analyzer.pro",
    },
    license_info={
        "name": "Proprietary",
        "url": "https://financial-analyzer.pro/license",
    }
)

# تنظیم میدلورهای سفارشی
setup_custom_middlewares(app)

# ثبت روترهای API
app.include_router(api_router)

# ===== Custom Documentation Endpoints =====
@app.get("/api/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    """داکیومنت Swagger UI سفارشی"""
    return get_swagger_ui_html(
        openapi_url="/api/openapi.json",
        title=f"{config.APP_NAME} - API Documentation",
        swagger_favicon_url="https://fastapi.tiangolo.com/img/favicon.png"
    )

@app.get("/api/openapi.json", include_in_schema=False)
async def get_custom_openapi():
    """OpenAPI schema سفارشی"""
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=config.APP_NAME,
        version=config.VERSION,
        description="Advanced Financial Analysis Platform",
        routes=app.routes,
    )
    
    # اضافه کردن اطلاعات امنیتی
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT"
        }
    }
    
    # اضافه کردن امنیت به endpointها
    for path in openapi_schema["paths"].values():
        for method in path.values():
            method["security"] = [{"BearerAuth": []}]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

# ===== Startup and Shutdown Events =====
@app.on_event("startup")
async def startup_event():
    """رویداد راه‌اندازی سرور"""
    try:
        logger.info("🚀 Starting Financial Analyzer Pro Server...")
        logger.info(f"📊 Application: {config.APP_NAME}")
        logger.info(f"🔢 Version: {config.VERSION}")
        logger.info(f"👨‍💻 Developer: {config.DEVELOPER}")
        logger.info(f"🌐 Environment: {'Production' if not config.DEBUG else 'Development'}")
        logger.info(f"📍 Host: {config.HOST}")
        logger.info(f"🎯 Port: {config.PORT}")
        
        # مقداردهی اولیه ماژول‌های اصلی
        await initialize_core_modules()
        
        logger.info("✅ Server started successfully!")
        logger.info("📚 API Documentation available at: http://localhost:8000/api/docs")
        logger.info("🔍 Health check available at: http://localhost:8000/api/system/health")
        
    except Exception as e:
        logger.error(f"❌ Server startup failed: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """رویداد خاموشی سرور"""
    try:
        logger.info("🛑 Shutting down Financial Analyzer Pro Server...")
        
        # پاک‌سازی منابع
        await cleanup_resources()
        
        logger.info("✅ Server shutdown completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Server shutdown failed: {e}")

# ===== Core Initialization =====
async def initialize_core_modules():
    """مقداردهی اولیه ماژول‌های اصلی"""
    try:
        logger.info("🔧 Initializing core modules...")
        
        # ایمپورت ماژول‌های اصلی
        from src.core.crisis_analyzer import crisis_analyzer
        from src.core.monte_carlo import monte_carlo_engine
        from src.core.signal_generator import signal_generator
        from src.data.market_data import market_data_manager
        from src.security.auth_manager import auth_manager
        from src.security.session_manager import session_manager
        
        # لیست ماژول‌ها برای مقداردهی اولیه
        modules = [
            (market_data_manager, "Market Data Manager"),
            (crisis_analyzer, "Crisis Analyzer"),
            (monte_carlo_engine, "Monte Carlo Engine"),
            (signal_generator, "Signal Generator"),
            (auth_manager, "Authentication Manager"),
            (session_manager, "Session Manager")
        ]
        
        # مقداردهی اولیه تمام ماژول‌ها
        for module, name in modules:
            try:
                await module.initialize()
                logger.info(f"✅ {name} initialized successfully")
            except Exception as e:
                logger.error(f"❌ {name} initialization failed: {e}")
                raise
        
        logger.info("🎯 All core modules initialized successfully!")
        
    except Exception as e:
        logger.error(f"❌ Core modules initialization failed: {e}")
        raise

async def cleanup_resources():
    """پاک‌سازی منابع"""
    try:
        logger.info("🧹 Cleaning up resources...")
        
        # ایمپورت ماژول‌های اصلی
        from src.core.crisis_analyzer import crisis_analyzer
        from src.core.monte_carlo import monte_carlo_engine
        from src.core.signal_generator import signal_generator
        from src.data.market_data import market_data_manager
        from src.security.auth_manager import auth_manager
        from src.security.session_manager import session_manager
        
        # لیست ماژول‌ها برای پاک‌سازی
        modules = [
            (market_data_manager, "Market Data Manager"),
            (crisis_analyzer, "Crisis Analyzer"),
            (monte_carlo_engine, "Monte Carlo Engine"),
            (signal_generator, "Signal Generator"),
            (auth_manager, "Authentication Manager"),
            (session_manager, "Session Manager")
        ]
        
        # پاک‌سازی تمام ماژول‌ها
        for module, name in modules:
            try:
                await module.cleanup()
                logger.info(f"✅ {name} cleaned up successfully")
            except Exception as e:
                logger.warning(f"⚠️ {name} cleanup failed: {e}")
        
        logger.info("✅ All resources cleaned up successfully!")
        
    except Exception as e:
        logger.error(f"❌ Resources cleanup failed: {e}")

# ===== Global Exception Handler =====
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """مدیریت خطاهای سراسری"""
    logger.error(f"💥 Global exception: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": "Internal server error",
            "error_id": "SERVER_ERROR_001"
        }
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """مدیریت خطاهای HTTP"""
    logger.warning(f"🌐 HTTP exception: {exc.status_code} - {exc.detail}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "message": exc.detail,
            "error_id": f"HTTP_ERROR_{exc.status_code}"
        }
    )

# ===== Main Execution =====
def main():
    """تابع اصلی اجرای سرور"""
    try:
        logger.info("💰 Financial Analyzer Pro - Starting Server...")
        
        # تنظیمات uvicorn
        uvicorn_config = uvicorn.Config(
            app=app,
            host=config.HOST,
            port=config.PORT,
            reload=config.DEBUG,  # فعال کردن reload در حالت توسعه
            log_level="info" if config.DEBUG else "warning",
            access_log=True,
            workers=1 if config.DEBUG else 4  # تعداد workerها
        )
        
        # ایجاد سرور
        server = uvicorn.Server(uvicorn_config)
        
        # اجرای سرور
        logger.info(f"🎯 Server configured: {config.HOST}:{config.PORT}")
        logger.info(f"🔧 Debug mode: {'ENABLED' if config.DEBUG else 'DISABLED'}")
        logger.info(f"👥 Workers: {uvicorn_config.workers}")
        
        # اجرای سرور
        asyncio.run(server.serve())
        
    except KeyboardInterrupt:
        logger.info("👋 Server stopped by user")
    except Exception as e:
        logger.error(f"💥 Server execution failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # اجرای سرور
    main()
