"""Technical analysis orchestrator for coordinating feature engineering and analysis engines."""

import pandas as pd

from typing import Any, Dict, Literal

from .feature_engine import DailyFeatureEngine, IntradayFeatureEngine
from .analysis_engine.daily import DailyAnalysisEngine
from .analysis_engine.intraday import IntradayAnalysisEngine

from itapia_common.schemas.entities.analysis.technical import TechnicalReport
from itapia_common.logger import ITAPIALogger

logger = ITAPIALogger('Technical Orchestrator')


class TechnicalOrchestrator:
    """Orchestrator for technical analysis workflows.
    
    Coordinates feature engineering and analysis engines for both daily and intraday data.
    """
    
    def get_daily_features(self, ohlcv_df: pd.DataFrame) -> pd.DataFrame:
        """Generate features for daily technical analysis.
        
        Args:
            ohlcv_df (pd.DataFrame): OHLCV data for feature generation
            
        Returns:
            pd.DataFrame: DataFrame enriched with technical features
        """
        logger.info("GENERATE DAILY FEATURES")
        try:
            engine = DailyFeatureEngine(ohlcv_df)
            return engine.add_all_features().get_features(handle_na_method='forward_fill', 
                                                        reset_index=False)
        except (ValueError, TypeError) as e:
            logger.err(f"Daily Feature Engine: {e}. Returning empty DataFrame.")
            return pd.DataFrame()
            

    def get_intraday_features(self, ohlcv_df: pd.DataFrame) -> pd.DataFrame:
        """Generate features for intraday technical analysis.
        
        Args:
            ohlcv_df (pd.DataFrame): OHLCV data for feature generation
            
        Returns:
            pd.DataFrame: DataFrame enriched with technical features
        """
        logger.info("GENERATE INTRADAY FEATURES")
        try:
            engine = IntradayFeatureEngine(ohlcv_df)
            return engine.add_all_intraday_features().get_features(handle_na_method='forward_fill',
                                                                reset_index=False)
        except (ValueError, TypeError) as e:
            logger.err(f"Intraday Feature Engine: {e}. Returning empty DataFrame.")
            return pd.DataFrame()
        
    def get_daily_analysis(self, enriched_df: pd.DataFrame,
                           analysis_type: Literal['short', 'medium', 'long'] = 'medium'):
        """Generate daily technical analysis report.
        
        Args:
            enriched_df (pd.DataFrame): DataFrame with technical features
            analysis_type (Literal['short', 'medium', 'long'], optional): Analysis timeframe. 
                Defaults to 'medium'.
                
        Returns:
            Analysis report from DailyAnalysisEngine
            
        Raises:
            Exception: If analysis engine encounters errors
        """
        logger.info("GENERATE DAILY ANALYSIS")
        try:
            # DailyAnalysisEngine may throw ValueError if insufficient data
            engine = DailyAnalysisEngine(enriched_df, analysis_type=analysis_type)
            return engine.get_analysis_report()
        except (ValueError, TypeError) as e:
            logger.err(f"Daily Analysis Engine: {e}. Returning error report.")
            raise e
        
    def get_intraday_analysis(self, enriched_df: pd.DataFrame):
        """Generate intraday technical analysis report.
        
        Args:
            enriched_df (pd.DataFrame): DataFrame with technical features
            
        Returns:
            Analysis report from IntradayAnalysisEngine
        """
        logger.info("GENERATE INTRADAY ANALYSIS")
        try:
            # IntradayAnalysisEngine may throw ValueError if insufficient data
            engine = IntradayAnalysisEngine(enriched_df)
            return engine.get_analysis_report()
        except (ValueError, TypeError) as e:
            logger.err(f"Intraday Analysis Engine: {e}. Returning error report.")
    
    def get_full_analysis(self, enriched_daily_df: pd.DataFrame,
                          enriched_intraday_df: pd.DataFrame,
                          required_type: Literal['daily', 'intraday', 'all'] = 'all',
                          daily_analysis_type: Literal['short', 'medium', 'long'] = 'medium') -> TechnicalReport:
        """Generate complete technical analysis report.
        
        Args:
            enriched_daily_df (pd.DataFrame): Daily DataFrame with technical features
            enriched_intraday_df (pd.DataFrame): Intraday DataFrame with technical features
            required_type (Literal['daily', 'intraday', 'all'], optional): Type of analysis required. 
                Defaults to 'all'.
            daily_analysis_type (Literal['short', 'medium', 'long'], optional): Daily analysis timeframe. 
                Defaults to 'medium'.
                
        Returns:
            TechnicalReport: Complete technical analysis report
        """
        daily_report = None
        intraday_report = None
        
        if required_type == 'daily' or required_type == 'all':
            daily_report = self.get_daily_analysis(enriched_daily_df, daily_analysis_type)
        if required_type == 'intraday' or required_type == 'all':
            intraday_report = self.get_intraday_analysis(enriched_intraday_df)
            
        return TechnicalReport(
            report_type=required_type,
            daily_report=daily_report,
            intraday_report=intraday_report
        )
             
    def get_full_past_analysis(self, enriched_daily_df: pd.DataFrame,
                               current_date_enriched: pd.Series) -> TechnicalReport:
        """Generate complete past technical analysis report.
        
        Args:
            enriched_daily_df (pd.DataFrame): Daily DataFrame with technical features
            current_date_enriched (pd.Series): Current date enriched data series
            
        Returns:
            TechnicalReport: Complete technical analysis report with mock intraday data
        """
        daily_report = self.get_daily_analysis(enriched_df=enriched_daily_df, analysis_type='medium')
        intraday_mock_report = IntradayAnalysisEngine.get_mock_report(current_date_enriched)
        
        return TechnicalReport(
            report_type='all',
            daily_report=daily_report,
            intraday_report=intraday_mock_report
        )