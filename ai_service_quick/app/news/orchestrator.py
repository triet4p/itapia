import asyncio
import time
import pandas as pd
from datetime import datetime, timezone
from typing import Dict, List, Literal
from functools import partial

import app.core.config as cfg

from app.news.sentiment_analysis import SentimentAnalysisModel


from itapia_common.dblib.schemas.reports.news import (
    NewsAnalysisReport, SingleNewsAnalysisReport
)

from itapia_common.dblib.cache.memory import AsyncInMemoryCache

from itapia_common.logger import ITAPIALogger

logger = ITAPIALogger('News Orchestrator')

def _create_sentiment_model_sync() -> SentimentAnalysisModel:
    return SentimentAnalysisModel(cfg.NEWS_SENTIMENT_ANALYSIS_MODEL)

class NewsOrchestrator:
    TO_CACHE_ELEMENTS = {
        'sentiment': {
            'key': cfg.NEWS_SENTIMENT_ANALYSIS_MODEL,
            'func': _create_sentiment_model_sync,
            'params': {}
        }
    }
    
    def __init__(self):
        self.model_cache = AsyncInMemoryCache()
        # Các sub-module controller/orchestrator khác
        
    async def generate_report(self, ticker: str, texts: List[str]):
        logger.info("Getting required analysis models from cache...")
        sentiment_model: SentimentAnalysisModel = await self._get_or_load_element('sentiment')
        # Other ... 
        
        logger.info(f"Running sentiment analysis for {len(texts)} news items...")
        loop = asyncio.get_running_loop()
        
        sentiment_analysis_reports, = await asyncio.gather(
            loop.run_in_executor(None, sentiment_model.analysis_sentiment, texts)
        )
        
        single_reports: List[SingleNewsAnalysisReport] = []
        num_to_process = len(texts)
        for i in range(num_to_process):
            # Other ...
            single_reports.append(SingleNewsAnalysisReport(
                text=texts[i],
                sentiment_analysis=sentiment_analysis_reports[i],
                ner=None,
                impact_assessment=None,
                keyword_highlighting_evidence=None
            ))
            
        return NewsAnalysisReport(
            ticker=ticker,
            reports=single_reports
        )
        
    async def _get_or_load_element(self, element_type: Literal['sentiment', 'ner', 'keyword-highlight']):
        """
        Lấy model từ cache. Nếu không có, tải về từ Hugging Face và cache lại.
        Hàm này sẽ tự động "hồi sinh" Task từ metadata đã lưu.
        """
        element = NewsOrchestrator.TO_CACHE_ELEMENTS[element_type]
        key = element['key']
        func = element['func']
        params = element['params']
        func_with_params = partial(func, **params)
        async def model_factory():
            logger.info(f"CACHE MISS: Loading sentiment model...")
            
            # Chạy hàm blocking trong executor
            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(
                None, 
                func_with_params
            )
            
        return await self.model_cache.get_or_set_with_lock(key, model_factory)
    
    def _get_or_load_element_sync(self, element_type: Literal['sentiment', 'ner', 'keyword-highlight']):
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        return loop.run_until_complete(
            self._get_or_load_element(element_type)
        )
    
    async def preload_caches(self):
        logger.info("--- NEWS: Starting pre-warming process for all models ---")
        
        tasks = []
        for element_type in self.TO_CACHE_ELEMENTS.keys():
            # Tạo các task để chạy song song
            task = asyncio.create_task(self._get_or_load_element(element_type))
            tasks.append(task)
        
        # Chờ tất cả các task tải xong
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Kiểm tra lỗi sau khi chạy xong
        for result, element_type in zip(results, self.TO_CACHE_ELEMENTS.keys()):
            if isinstance(result, Exception):
                logger.err(f"A critical error occurred during pre-warming of element '{element_type}': {result}")

        logger.info("--- NEWS: Completed pre-warming process for all models ---")