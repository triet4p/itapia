# api/v1/endpoints/data_viewer.py
from typing import Literal, Union
from fastapi import APIRouter, HTTPException, Depends

from app.orchestrator import AIServiceQuickOrchestrator

from itapia_common.dblib.schemas.reports import ErrorResponse, QuickCheckReport
from itapia_common.dblib.dependencies import get_metadata_service, get_prices_service, get_news_service
from itapia_common.dblib.services import APIMetadataService, APINewsService, APIPricesService

def get_orchestrator(metadata_service: APIMetadataService = Depends(get_metadata_service),
                     prices_service: APIPricesService = Depends(get_prices_service),
                     news_service: APINewsService = Depends(get_news_service)):
    return AIServiceQuickOrchestrator(
        metadata_service,
        prices_service,
        news_service
    )

router = APIRouter()

@router.get("/quick/{ticker}", response_model=Union[QuickCheckReport, ErrorResponse])
def get_quick_analysis(ticker: str, 
                       orchestrator: AIServiceQuickOrchestrator = Depends(get_orchestrator),
                       daily_analysis_type: Literal['short', 'medium', 'long'] = 'medium',
                       required_type: Literal['daily', 'intraday', 'all']='all'):
    report = orchestrator.get_full_analysis_report(ticker, daily_analysis_type, required_type)
    if isinstance(report, ErrorResponse):
        raise HTTPException(status_code=404, detail=report.error)
    
    return report