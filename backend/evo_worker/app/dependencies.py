# Mở/Tạo file app/dependencies.py

from typing import Optional

from .backtest.selector import BacktestPointSelector

from .backtest.context import BacktestContextManager
from .backtest.data_prepare import BacktestDataPreparer

from itapia_common.dblib.services import (
    APIMetadataService, APIPricesService, BacktestReportService
)
from itapia_common.dblib.session import get_rdbms_session, get_redis_connection

# Biến global được "bảo vệ" bằng dấu gạch dưới, chỉ được truy cập qua các hàm getter
_backtest_context_manager: Optional[BacktestContextManager] = None

def create_dependencies():
    """
    Hàm "nhà máy" này được gọi MỘT LẦN DUY NHẤT trong lifespan để khởi tạo tất cả các đối tượng.
    """
    global _backtest_context_manager
    
    # Chỉ khởi tạo nếu chưa có
    if _backtest_context_manager is not None:
        return

    # Logic khởi tạo DB và services
    db_session_gen = get_rdbms_session()
    redis_gen = get_redis_connection()
    db = next(db_session_gen)
    redis = next(redis_gen)
    
    # Logic khởi tạo này có thể gây ra lỗi nếu DB không kết nối được
    # Nên bọc trong try...finally để đảm bảo session được đóng
    try:
        metadata_service = APIMetadataService(rdbms_session=db)
        prices_service = APIPricesService(rdbms_session=db, redis_client=redis, metadata_service=metadata_service)
        backtest_report_service = BacktestReportService(db_session=db)
        
        backtest_data_preparer = BacktestDataPreparer(
            prices_service=prices_service, 
            backtest_report_service=backtest_report_service,
            metadata_service=metadata_service
        )
        
        # Khởi tạo và gán vào biến global
        _backtest_context_manager = BacktestContextManager(data_preparer=backtest_data_preparer)
    finally:
        db.close()
        redis.close()


def get_backtest_context_manager() -> BacktestContextManager:
    """
    Hàm Dependency Injector cho FastAPI.
    Nó trả về instance đã được tạo trong lifespan.
    """
    if _backtest_context_manager is None:
        raise RuntimeError("BacktestContextManager has not been initialized. Check lifespan event.")
    return _backtest_context_manager

def close_dependencies():
    """
    Hàm dọn dẹp, được gọi khi ứng dụng tắt.
    """
    global _backtest_context_manager
    _backtest_context_manager = None