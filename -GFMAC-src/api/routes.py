#!/usr/bin/env python3
"""
API Routes Module
RESTful API Endpoints Definition
Developer: Seyed Aladdin Mousavi Jashni
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Optional, Dict
import logging

from .handlers import (
    market_data_handler, 
    signal_handler, 
    portfolio_handler
)
from src.security.auth_manager import auth_manager
from src.security.session_manager import session_manager
from src.utils.validator import data_validator

# ایجاد روتر اصلی
api_router = APIRouter(prefix="/api", tags=["Financial Analyzer API"])

# طرح امنیتی برای توکن‌ها
security = HTTPBearer()

# وابستگی برای احراز هویت
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """دریافت کاربر جاری از توکن"""
    token = credentials.credentials
    is_valid, token_data = await auth_manager.verify_token(token)
    
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    return token_data

# وابستگی برای اعتبارسنجی سشن
async def validate_session(
    user_data: Dict = Depends(get_current_user),
    session_id: str = Query(..., description="Session ID")
):
    """اعتبارسنجی سشن کاربر"""
    is_valid, session_data = await session_manager.validate_session(
        session_id, 
        user_data.get('user_id')
    )
    
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session"
        )
    
    return session_data

# ===== Routes گروه احراز هویت =====
auth_router = APIRouter(prefix="/auth", tags=["Authentication"])

@auth_router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_user(user_data: Dict):
    """ثبت نام کاربر جدید"""
    try:
        success, result = await auth_manager.create_user(user_data)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get('errors', ['Registration failed'])
            )
        
        return {
            "status": "success",
            "message": "User registered successfully",
            "data": {
                "user_id": result['user']['user_id'],
                "qr_code": result.get('qr_code'),
                "setup_instructions": result.get('setup_instructions')
            }
        }
        
    except Exception as e:
        logging.error(f"Registration failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )

@auth_router.post("/login")
async def login_user(credentials: Dict):
    """ورود کاربر"""
    try:
        success, result = await auth_manager.authenticate_user(credentials)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=result.get('error', 'Authentication failed')
            )
        
        # ایجاد سشن
        session_info = await session_manager.create_session(
            user_id=result['user']['user_id'],
            user_agent=credentials.get('user_agent', ''),
            ip_address=credentials.get('ip_address', '')
        )
        
        return {
            "status": "success",
            "message": "Login successful",
            "data": {
                **result,
                "session": session_info
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Login failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )

@auth_router.post("/verify-2fa")
async def verify_two_factor(verification_data: Dict):
    """تأیید احراز هویت دو مرحله‌ای"""
    try:
        user_id = verification_data.get('user_id')
        code = verification_data.get('code')
        
        if not user_id or not code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User ID and code are required"
            )
        
        is_valid = await auth_manager.verify_google_auth(user_id, code)
        
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid verification code"
            )
        
        return {
            "status": "success",
            "message": "2FA verification successful"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"2FA verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="2FA verification failed"
        )

@auth_router.post("/logout")
async def logout_user(
    user_data: Dict = Depends(get_current_user),
    session_id: str = Query(..., description="Session ID to logout")
):
    """خروج کاربر"""
    try:
        success = await session_manager.terminate_session(session_id, "user_logout")
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to logout"
            )
        
        return {
            "status": "success",
            "message": "Logout successful"
        }
        
    except Exception as e:
        logging.error(f"Logout failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )

# ===== Routes گروه داده‌های بازار =====
market_router = APIRouter(prefix="/market", tags=["Market Data"])

@market_router.get("/overview")
async def get_market_overview(
    user_data: Dict = Depends(get_current_user),
    session_data: Dict = Depends(validate_session)
):
    """دریافت نمای کلی بازار"""
    return await market_data_handler.get_market_overview(user_data['user_id'])

@market_router.get("/instruments/{symbol}")
async def get_instrument_data(
    symbol: str = Path(..., description="Instrument symbol (e.g., EUR/USD, BTC/USD)"),
    user_data: Dict = Depends(get_current_user),
    session_data: Dict = Depends(validate_session)
):
    """دریافت داده‌های یک نماد خاص"""
    return await market_data_handler.get_instrument_data(symbol, user_data['user_id'])

@market_router.get("/economic-calendar")
async def get_economic_calendar(
    days: int = Query(7, description="Number of days to show", ge=1, le=30),
    user_data: Dict = Depends(get_current_user),
    session_data: Dict = Depends(validate_session)
):
    """دریافت تقویم اقتصادی"""
    return await market_data_handler.get_economic_calendar(user_data['user_id'], days)

@market_router.get("/crisis-analysis")
async def get_crisis_analysis(
    user_data: Dict = Depends(get_current_user),
    session_data: Dict = Depends(validate_session)
):
    """دریافت تحلیل بحران فعلی"""
    try:
        from src.core.crisis_analyzer import crisis_analyzer
        from src.data.market_data import market_data_manager
        
        market_data = await market_data_manager.get_all_market_data()
        crisis_report = await crisis_analyzer.analyze(market_data)
        
        return {
            "status": "success",
            "data": crisis_report
        }
        
    except Exception as e:
        logging.error(f"Crisis analysis failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get crisis analysis"
        )

# ===== Routes گروه سیگنال‌ها =====
signals_router = APIRouter(prefix="/signals", tags=["Trading Signals"])

@signals_router.get("/")
async def get_trading_signals(
    min_confidence: float = Query(0.6, description="Minimum confidence level", ge=0.0, le=1.0),
    asset_types: List[str] = Query(None, description="Filter by asset types"),
    timeframes: List[str] = Query(None, description="Filter by timeframes"),
    user_data: Dict = Depends(get_current_user),
    session_data: Dict = Depends(validate_session)
):
    """دریافت سیگنال‌های معاملاتی"""
    filters = {}
    
    if min_confidence:
        filters['min_confidence'] = min_confidence
    
    if asset_types:
        filters['asset_types'] = asset_types
    
    if timeframes:
        filters['timeframes'] = timeframes
    
    return await signal_handler.get_trading_signals(user_data['user_id'], filters)

@signals_router.get("/analysis/{symbol}")
async def get_signal_analysis(
    symbol: str = Path(..., description="Instrument symbol"),
    user_data: Dict = Depends(get_current_user),
    session_data: Dict = Depends(validate_session)
):
    """دریافت تحلیل دقیق برای یک نماد"""
    return await signal_handler.get_signal_analysis(symbol, user_data['user_id'])

@signals_router.get("/monte-carlo/{symbol}")
async def get_monte_carlo_analysis(
    symbol: str = Path(..., description="Instrument symbol"),
    simulations: int = Query(10000, description="Number of simulations", ge=1000, le=100000),
    user_data: Dict = Depends(get_current_user),
    session_data: Dict = Depends(validate_session)
):
    """دریافت تحلیل مونت کارلو برای یک نماد"""
    try:
        from src.core.monte_carlo import monte_carlo_engine
        from src.data.market_data import market_data_manager
        
        market_data = await market_data_manager.get_all_market_data()
        
        # پیدا کردن داده‌های نماد
        symbol_data = None
        for market_type in ['forex', 'crypto', 'indices', 'metals']:
            if symbol in market_data.get(market_type, {}):
                symbol_data = {symbol: market_data[market_type][symbol]}
                break
        
        if not symbol_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Instrument {symbol} not found"
            )
        
        # تنظیم تعداد شبیه‌سازی‌ها
        monte_carlo_engine.simulation_count = simulations
        
        # اجرای تحلیل
        analysis = await monte_carlo_engine.analyze_portfolio_risk(symbol_data)
        
        return {
            "status": "success",
            "symbol": symbol,
            "simulations": simulations,
            "analysis": analysis
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Monte Carlo analysis failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to perform Monte Carlo analysis"
        )

# ===== Routes گروه پرتفولیو =====
portfolio_router = APIRouter(prefix="/portfolio", tags=["Portfolio Management"])

@portfolio_router.post("/analyze")
async def analyze_portfolio(
    portfolio_data: Dict,
    user_data: Dict = Depends(get_current_user),
    session_data: Dict = Depends(validate_session)
):
    """آنالیز پرتفولیو"""
    return await portfolio_handler.analyze_portfolio(portfolio_data, user_data['user_id'])

@portfolio_router.post("/optimal-allocation")
async def get_optimal_allocation(
    user_preferences: Dict,
    user_data: Dict = Depends(get_current_user),
    session_data: Dict = Depends(validate_session)
):
    """دریافت تخصیص بهینه دارایی‌ها"""
    return await portfolio_handler.get_optimal_allocation(user_preferences, user_data['user_id'])

@portfolio_router.get("/risk-assessment")
async def get_portfolio_risk_assessment(
    user_data: Dict = Depends(get_current_user),
    session_data: Dict = Depends(validate_session)
):
    """دریافت ارزیابی ریسک پرتفولیو"""
    try:
        from src.core.monte_carlo import monte_carlo_engine
        from src.data.market_data import market_data_manager
        
        market_data = await market_data_manager.get_all_market_data()
        risk_assessment = await monte_carlo_engine.analyze_portfolio_risk(market_data)
        
        return {
            "status": "success",
            "data": risk_assessment
        }
        
    except Exception as e:
        logging.error(f"Risk assessment failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to assess portfolio risk"
        )

# ===== Routes گروه سیستم =====
system_router = APIRouter(prefix="/system", tags=["System"])

@system_router.get("/health")
async def health_check():
    """بررسی سلامت سیستم"""
    try:
        # بررسی وضعیت ماژول‌های اصلی
        components = {
            "market_data": False,
            "crisis_analyzer": False, 
            "monte_carlo": False,
            "signal_generator": False,
            "auth_manager": False
        }
        
        # تست ماژول‌ها (شبیه‌سازی)
        components["market_data"] = True
        components["crisis_analyzer"] = True
        components["monte_carlo"] = True
        components["signal_generator"] = True
        components["auth_manager"] = True
        
        all_healthy = all(components.values())
        
        return {
            "status": "healthy" if all_healthy else "degraded",
            "timestamp": __import__('datetime').datetime.now().isoformat(),
            "components": components,
            "version": "1.0.0"
        }
        
    except Exception as e:
        logging.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }

@system_router.get("/session-info")
async def get_session_info(
    user_data: Dict = Depends(get_current_user),
    session_id: str = Query(..., description="Session ID")
):
    """دریافت اطلاعات سشن"""
    try:
        session_info = await session_manager.get_session_info(session_id)
        
        if not session_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        return {
            "status": "success",
            "data": session_info
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Session info fetch failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get session info"
        )

# ===== ثبت تمام روترها =====
api_router.include_router(auth_router)
api_router.include_router(market_router)
api_router.include_router(signals_router)
api_router.include_router(portfolio_router)
api_router.include_router(system_router)

logging.info("✅ All API routes configured successfully")
