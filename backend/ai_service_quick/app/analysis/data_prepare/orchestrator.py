from datetime import datetime

import app.core.config as cfg
from itapia_common.dblib.services import (
    APIMetadataService,
    APINewsService,
    APIPricesService,
)
from itapia_common.logger import ITAPIALogger

from .data_transform import *

logger = ITAPIALogger("Data Prepare Orchestrator")


class DataPrepareOrchestrator:
    """
    Orchestrate the entire data preparation process.
    This is the single interface that other AI modules should use to fetch data.
    """

    def __init__(
        self,
        metadata_service: APIMetadataService,
        prices_service: APIPricesService,
        news_service: APINewsService,
    ):
        self.metadata_service = metadata_service
        self.prices_service = prices_service
        self.news_service = news_service

    def get_all_tickers(self) -> List[str]:
        """
        Get all tickers available in ITAPIA system.
        """
        logger.info(f"Preparing ticker list...")
        ticker_lst = list(self.metadata_service.metadata_cache.keys())
        return [ticker.upper() for ticker in ticker_lst]

    def get_daily_ohlcv_for_ticker(
        self, ticker: str, limit: int = 2000
    ) -> pd.DataFrame:
        """
        Get and transform daily OHLCV data of a single ticker into validated DataFrame.

        If any error occured, return empty DataFrame.
        """
        logger.info(f"Preparing daily OHLCV for ticker '{ticker}'...")
        res = self.prices_service.get_daily_prices(ticker, limit=limit, skip=0)
        json_res = res.model_dump()
        if not json_res:
            logger.warn("Null response. Return empty DF.")
            return pd.DataFrame()

        try:
            df = transform_single_ticker_response(json_res)
            return df
        except KeyError as e:
            logger.err(f"Could not process a response. Error: {e}. Skipping.")
            return pd.DataFrame()

    def get_daily_ohlcv_for_sector(
        self, sector_code: str, limit_per_ticker: int = 2000
    ) -> pd.DataFrame:
        """
        Get and transform daily OHLCV data for all tickers of a sector, then concat them into a big and validated DataFrame.

        If any error occured, return empty DataFrame.
        """
        logger.info(f"Preparing daily OHLCV for sector '{sector_code}'...")
        res_lst = self.prices_service.get_daily_prices_by_sector(
            sector_code, limit=limit_per_ticker, skip=0
        )
        json_list = [x.model_dump() for x in res_lst]
        if not json_list:
            logger.warn("Null response. Return empty DF.")
            return pd.DataFrame()

        df = transform_multi_ticker_responses(json_list)
        return df

    def get_intraday_ohlcv_for_ticker(self, ticker: str) -> pd.DataFrame:
        """
        Get and transform intraday OHLCV data of a single ticker into validated DataFrame.

        If any error occured, return empty DataFrame.
        """
        logger.info(f"Preparing intraday OHLCV for ticker '{ticker}'...")
        json_res = self.prices_service.get_intraday_prices(ticker).model_dump()
        if not json_res:
            logger.warn("Null response. Return empty DF.")
            return pd.DataFrame()

        try:
            df = transform_single_ticker_response(json_res)
            return df
        except ValueError as e:
            logger.err(f"Could not process a response. Error: {e}. Skipping.")
            return pd.DataFrame()

    def get_all_sectors_as_df(self) -> pd.DataFrame:
        logger.info(f"Preparing sector list...")
        sector_list = self.metadata_service.get_all_sectors()
        sector_list = [x.model_dump() for x in sector_list]
        if not sector_list:
            logger.warn("Null response. Return empty DF.")
            return pd.DataFrame()
        logger.info(f"Transforming to DF...")
        return pd.DataFrame(sector_list)

    def get_all_sectors_code(self) -> List[str]:
        logger.info(f"Preparing sector list...")
        sector_list = self.metadata_service.get_all_sectors()
        sector_list = [x.sector_code for x in sector_list]
        if not sector_list:
            logger.warn("Null response. Return empty list.")
            return []

        return sector_list

    def get_sector_code_of(self, ticker: str):
        return self.metadata_service.get_sector_code_of(ticker)

    def is_exist(self, ticker: str):
        try:
            self.metadata_service.get_validate_ticker_info(ticker, "news")
            return True
        except ValueError as e:
            return False

    def _get_full_text_from_news(self, news):
        text: str = news.title
        if news.summary is not None:
            text += "." + news.summary
        return text

    def get_all_news_text_for_ticker(self, ticker: str) -> List[str]:
        """
        Fetch and combine all news for a ticker, contains:

        L1: Relevant news

        L2: Contextual universal news

        L3: Macro universal news

        Args:
            ticker (str): Ticker to fetch data.

        Returns:
            List[str]: List of all news, each news element is made up of its `title` and `summary`
        """

        logger.info(f"Preparing combined news feed for ticker: {ticker}")
        sector_list = self.metadata_service.get_all_sectors()
        sector_code = self.get_sector_code_of(ticker)
        for x in sector_list:
            if x.sector_code == sector_code:
                sector = x.sector_name
                break

        all_news_text_with_time = []

        logger.info(f"Fetching L1 (Relevant) news...")
        relevant_news = self.news_service.get_relevant_news(
            ticker, skip=0, limit=cfg.NEWS_COUNT_RELEVANT
        )
        for news in relevant_news.datas:
            all_news_text_with_time.append(
                (self._get_full_text_from_news(news), news.publish_ts)
            )

        universal_news_hash = set()

        logger.info(f"Fetching L2 (Contextual) universal news...")
        contextual_search_terms = f"{sector}"
        contextual_news = self.news_service.get_universal_news(
            contextual_search_terms, skip=0, limit=cfg.NEWS_COUNT_CONTEXTUAL
        )
        for news in contextual_news.datas:
            if news.title_hash not in universal_news_hash:
                universal_news_hash.add(news.title_hash)
                all_news_text_with_time.append(
                    (self._get_full_text_from_news(news), news.publish_ts)
                )

        logger.info(f"Fetching L3 (Macro) universal news...")
        macro_search_terms_lst = [
            "Federal Reserve policy",
            "US inflation report CPI",
            "S&P 500",
        ]
        for macro_search_terms in macro_search_terms_lst:
            macro_news = self.news_service.get_universal_news(
                macro_search_terms, skip=0, limit=cfg.NEWS_COUNT_MACRO
            )
            for news in macro_news.datas:
                if news.title_hash not in universal_news_hash:
                    universal_news_hash.add(news.title_hash)
                    all_news_text_with_time.append(
                        (self._get_full_text_from_news(news), news.publish_ts)
                    )

        all_news_text_with_time.sort(key=lambda x: x[1], reverse=True)

        return [x[0] for x in all_news_text_with_time[: cfg.NEWS_TOTAL_LIMIT]]

    def get_history_news_for_ticker(
        self, ticker: str, before_date: datetime
    ) -> List[str]:
        """
        Fetch and combine all history news for a ticker, serve for backtesting, contains:

        L2: Contextual universal news

        L3: Macro universal news

        Args:
            ticker (str): Ticker to fetch data.
            before_date (datetime): Time bound to fetch news

        Returns:
            List[str]: List of all news, each news element is made up of its `title` and `summary`
        """
        logger.info(f"Preparing combined news feed for ticker: {ticker}")
        sector_list = self.metadata_service.get_all_sectors()
        sector_code = self.get_sector_code_of(ticker)
        for x in sector_list:
            if x.sector_code == sector_code:
                sector = x.sector_name
                break

        all_news_text_with_time = []
        universal_news_hash = set()

        logger.info(f"Fetching L2 (Contextual) universal news...")
        contextual_search_terms = f"{sector}"
        contextual_news = self.news_service.get_universal_news(
            contextual_search_terms,
            skip=0,
            limit=cfg.NEWS_COUNT_CONTEXTUAL,
            before_date=before_date,
        )
        for news in contextual_news.datas:
            if news.title_hash not in universal_news_hash:
                universal_news_hash.add(news.title_hash)
                all_news_text_with_time.append(
                    (self._get_full_text_from_news(news), news.publish_ts)
                )

        logger.info(f"Fetching L3 (Macro) universal news...")
        macro_search_terms_lst = [
            "Federal Reserve policy",
            "US inflation report CPI",
            "S&P 500",
        ]
        for macro_search_terms in macro_search_terms_lst:
            macro_news = self.news_service.get_universal_news(
                macro_search_terms,
                skip=0,
                limit=cfg.NEWS_COUNT_MACRO,
                before_date=before_date,
            )
            for news in macro_news.datas:
                if news.title_hash not in universal_news_hash:
                    universal_news_hash.add(news.title_hash)
                    all_news_text_with_time.append(
                        (self._get_full_text_from_news(news), news.publish_ts)
                    )

        all_news_text_with_time.sort(key=lambda x: x[1], reverse=True)

        return [x[0] for x in all_news_text_with_time[: cfg.NEWS_TOTAL_LIMIT]]
