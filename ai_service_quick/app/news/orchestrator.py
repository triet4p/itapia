import asyncio
import pandas as pd
from datetime import datetime, timezone
from typing import Dict, List, Literal
from functools import partial

import app.core.config as cfg

from app.core.exceptions import PreloadCacheError

from .sentiment_analysis import SentimentAnalysisModel
from .ner import TransformerNERModel, SpacyNERModel
from .impact_assessment import WordBasedImpactAssessmentModel
from .keyword_highlight import WordBasedKeywordHighlightingModel
from .summary import ResultSummarizer

from .utils import preprocess_news_texts, load_dictionary

from itapia_common.schemas.entities.reports.news import (
    NewsAnalysisReport, SingleNewsAnalysisReport
)

from itapia_common.dblib.cache.memory import AsyncInMemoryCache

from itapia_common.logger import ITAPIALogger

logger = ITAPIALogger('News Orchestrator')

def _create_sentiment_model_sync() -> SentimentAnalysisModel:
    return SentimentAnalysisModel(cfg.NEWS_SENTIMENT_ANALYSIS_MODEL)

def _create_ner_model_sync() -> SpacyNERModel:
    return SpacyNERModel(cfg.NEWS_SPACY_NER_MODEL)

def _create_impact_assessment_model_sync() -> WordBasedImpactAssessmentModel:
    try:
        high_impact_dictionary = load_dictionary(cfg.NEWS_IMPACT_DICTIONARY_PATH.format(level='high'))
    except FileNotFoundError as e:
        logger.warn('Not found dictionary file, return empty dictionary')
        high_impact_dictionary = set()
    try:
        moderate_impact_dictionary = load_dictionary(cfg.NEWS_IMPACT_DICTIONARY_PATH.format(level='moderate'))
    except FileNotFoundError as e:
        logger.warn('Not found dictionary file, return empty dictionary')
        moderate_impact_dictionary = set()
    try:
        low_impact_dictionary = load_dictionary(cfg.NEWS_IMPACT_DICTIONARY_PATH.format(level='low'))
    except FileNotFoundError as e:
        logger.warn('Not found dictionary file, return empty dictionary')
        low_impact_dictionary = set()
    return WordBasedImpactAssessmentModel(high_impact_dictionary, 
                                          moderate_impact_dictionary,
                                          low_impact_dictionary)

def _create_keyword_highlighting_model_sync() -> WordBasedKeywordHighlightingModel:
    # Tải các từ điển từ file (tương tự như impact assessment)
    try:
        positive_dictionary = load_dictionary(cfg.NEWS_KEYWORD_HIGHLIGHT_PATH.format(direction='positive'))
    except FileNotFoundError:
        logger.warn("Positive LM dictionary not found, using empty set.")
        positive_dictionary = set()

    try:
        negative_dictionary = load_dictionary(cfg.NEWS_KEYWORD_HIGHLIGHT_PATH.format(direction='negative'))
    except FileNotFoundError:
        logger.warn("Negative LM dictionary not found, using empty set.")
        negative_dictionary = set()
        
    return WordBasedKeywordHighlightingModel(
        positive_dictionary=positive_dictionary,
        negative_dictionary=negative_dictionary
    )
    
def _create_summary_model_sync() -> ResultSummarizer:
    return ResultSummarizer()


class NewsOrchestrator:
    TO_CACHE_ELEMENTS = {
        'sentiment': {
            'key': cfg.NEWS_SENTIMENT_ANALYSIS_MODEL,
            'func': _create_sentiment_model_sync,
            'params': {}
        }, 
        'ner': {
            'key': cfg.NEWS_TRANSFORMER_NER_MODEL,
            'func': _create_ner_model_sync, 
            'params': {}
        },
        'impact-assessment': {
            'key': cfg.NEWS_IMPACT_ASSESSMENT_MODEL,
            'func': _create_impact_assessment_model_sync,
            'params': {}
        },
        'keyword-highlight': {
            'key': cfg.NEWS_KEYWORD_HIGHLIGHT_MODEL,
            'func': _create_keyword_highlighting_model_sync,
            'params': {}
        },
        'summary': {
            'key': cfg.NEWS_RESULT_SUMMARY_MODEL,
            'func': _create_summary_model_sync,
            'params': {}
        }
    }
    
    def __init__(self):
        self.model_cache = AsyncInMemoryCache()
        # Các sub-module controller/orchestrator khác
        
    async def generate_report(self, ticker: str, texts: List[str]):
        logger.info("Preprocessing texts ...")
        texts = preprocess_news_texts(texts)
        
        logger.info("Getting required analysis models from cache...")
        sentiment_model: SentimentAnalysisModel = await self._get_or_load_element('sentiment')
        ner_model: SpacyNERModel = await self._get_or_load_element('ner')
        impact_model: WordBasedImpactAssessmentModel = await self._get_or_load_element('impact-assessment')
        keyword_model: WordBasedKeywordHighlightingModel = await self._get_or_load_element('keyword-highlight')
        summary_model: ResultSummarizer = await self._get_or_load_element('summary')
    
        # Other ... 
        
        logger.info(f"Running sentiment analysis for {len(texts)} news items...")
        loop = asyncio.get_running_loop()
        
        sentiment_analysis_reports, ner_reports, impact_reports, keyword_reports = await asyncio.gather(
            loop.run_in_executor(None, sentiment_model.analysis_sentiment, texts),
            loop.run_in_executor(None, ner_model.recognize, texts),
            loop.run_in_executor(None, impact_model.assess, texts),
            loop.run_in_executor(None, keyword_model.extract, texts)
        )
        
        single_reports: List[SingleNewsAnalysisReport] = []
        num_to_process = len(texts)
        for i in range(num_to_process):
            # Other ...
            single_reports.append(SingleNewsAnalysisReport(
                text=texts[i],
                sentiment_analysis=sentiment_analysis_reports[i],
                ner=ner_reports[i],
                impact_assessment=impact_reports[i],
                keyword_highlighting_evidence=keyword_reports[i]
            ))
            
        summary = summary_model.summary(single_reports)
            
        return NewsAnalysisReport(
            ticker=ticker,
            reports=single_reports,
            summary=summary
        )
        
    async def _get_or_load_element(self, element_type: Literal['sentiment', 'ner', 'impact-assessment', 'keyword-highlight', 'summary']):
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
        failed_elements = []
        for result, element_type in zip(results, self.TO_CACHE_ELEMENTS.keys()):
            if isinstance(result, Exception):
                logger.err(f"A critical error during pre-warming of element '{element_type}': {result}")
                failed_elements.append(element_type)

        # SỬA LỖI: Nếu có bất kỳ lỗi nào, hãy ném ra ngoại lệ
        if failed_elements:
            raise PreloadCacheError(module_name="News Analysis", failed_elements=failed_elements)
                
        logger.info("--- NEWS: Completed pre-warming process for all models ---")