"""News analysis orchestrator for coordinating various NLP tasks."""

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

from itapia_common.schemas.entities.analysis.news import (
    NewsAnalysisReport, SingleNewsAnalysisReport
)

from itapia_common.dblib.cache.memory import AsyncInMemoryCache

from itapia_common.logger import ITAPIALogger

logger = ITAPIALogger('News Orchestrator')


def _create_sentiment_model_sync() -> SentimentAnalysisModel:
    """Create sentiment analysis model synchronously.
    
    Returns:
        SentimentAnalysisModel: Initialized sentiment analysis model
    """
    return SentimentAnalysisModel(cfg.NEWS_SENTIMENT_ANALYSIS_MODEL)


def _create_ner_model_sync() -> SpacyNERModel:
    """Create spaCy NER model synchronously.
    
    Returns:
        SpacyNERModel: Initialized spaCy NER model
    """
    return SpacyNERModel(cfg.NEWS_SPACY_NER_MODEL)


def _create_impact_assessment_model_sync() -> WordBasedImpactAssessmentModel:
    """Create impact assessment model synchronously.
    
    Returns:
        WordBasedImpactAssessmentModel: Initialized impact assessment model
    """
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
    """Create keyword highlighting model synchronously.
    
    Returns:
        WordBasedKeywordHighlightingModel: Initialized keyword highlighting model
    """
    # Load dictionaries from files (similar to impact assessment)
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
    """Create result summarizer synchronously.
    
    Returns:
        ResultSummarizer: Initialized result summarizer
    """
    return ResultSummarizer()


class NewsOrchestrator:
    """Orchestrates the complete news analysis pipeline."""
    
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
        """Initialize the news orchestrator with model cache."""
        self.model_cache = AsyncInMemoryCache()
        # Other sub-module controllers/orchestrators
        
    async def generate_report(self, ticker: str, texts: List[str]) -> NewsAnalysisReport:
        """Generate a complete news analysis report.
        
        Args:
            ticker (str): Stock ticker symbol
            texts (List[str]): List of news texts to analyze
            
        Returns:
            NewsAnalysisReport: Complete news analysis report
        """
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
        """Get model from cache. If not available, load from Hugging Face and cache it.
        
        This function will automatically "revive" the Task from saved metadata.
        
        Args:
            element_type (Literal): Type of element to load
            
        Returns:
            Model instance loaded from cache or created fresh
        """
        element = NewsOrchestrator.TO_CACHE_ELEMENTS[element_type]
        key = element['key']
        func = element['func']
        params = element['params']
        func_with_params = partial(func, **params)
        async def model_factory():
            logger.info(f"CACHE MISS: Loading sentiment model...")
            
            # Run blocking function in executor
            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(
                None, 
                func_with_params
            )
            
        return await self.model_cache.get_or_set_with_lock(key, model_factory)
    
    async def preload_caches(self):
        """Preload all models by running each element's loading process in parallel."""
        logger.info("--- NEWS: Starting pre-warming process for all models ---")
        
        tasks = []
        for element_type in self.TO_CACHE_ELEMENTS.keys():
            # Create tasks to run in parallel
            task = asyncio.create_task(self._get_or_load_element(element_type))
            tasks.append(task)
        
        # Wait for all tasks to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Check for errors after completion
        failed_elements = []
        for result, element_type in zip(results, self.TO_CACHE_ELEMENTS.keys()):
            if isinstance(result, Exception):
                logger.err(f"A critical error during pre-warming of element '{element_type}': {result}")
                failed_elements.append(element_type)

        # FIX: If any errors occurred, raise an exception
        if failed_elements:
            raise PreloadCacheError(module_name="News Analysis", failed_elements=failed_elements)
                
        logger.info("--- NEWS: Completed pre-warming process for all models ---")