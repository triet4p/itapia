"""Universal news fetching and processing pipeline.

This module implements a pipeline to fetch universal news articles
using keywords and topics from GNews API, process the data, and store it in the database.
"""

import hashlib
import re
import sys
import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional
from urllib.parse import urlparse, urlunparse

from gnews import GNews
from itapia_common.dblib.services import DataNewsService
from itapia_common.dblib.session import get_singleton_rdbms_engine
from itapia_common.logger import ITAPIALogger

from .utils import UNIVERSAL_KEYWORDS_EN, UNIVERSAL_TOPIC_EN, FetchException

logger = ITAPIALogger("Universal News Processor")


def _extract_news_data_by_keyword(
    keywords: list[str],
    period_days: int = 5,
    sleep_time: int = 5,
    max_results: int = 2,
    end_date: Optional[datetime] = None,
) -> list[dict]:
    """Extract news data for a list of keywords.

    Args:
        keywords (list[str]): List of keywords to search for news.
        period_days (int, optional): Number of days to look back for news. Defaults to 5.
        sleep_time (int, optional): Time to wait (in seconds) between requests. Defaults to 5.
        max_results (int, optional): Maximum number of results per keyword. Defaults to 2.
        end_date (Optional[datetime], optional): End date for news search. Defaults to None.

    Returns:
        list[dict]: List of raw news data dictionaries.
    """
    all_news_data = []

    if end_date is None:
        gnews_client = GNews(
            language="en",
            country="US",
            max_results=max_results,
            period=f"{period_days}d",
        )
    else:
        start_date = end_date - timedelta(days=period_days)
        print(start_date)
        gnews_client = GNews(
            language="en",
            country="US",
            max_results=max_results,
            start_date=start_date,
            end_date=end_date,
        )

    for keyword in keywords:
        logger.info(f"Fetching news for keyword: '{keyword}'...")
        try:
            news_for_keyword = gnews_client.get_news(keyword)

            # Attach keyword to each article to track source
            for article in news_for_keyword:
                article["keyword"] = keyword
                article["prior"] = 2

            all_news_data.extend(news_for_keyword)

        except Exception as e:
            logger.err(f"Failed to fetch news for '{keyword}'. Error: {e}")

        # Always delay to avoid being blocked
        time.sleep(sleep_time)

    return all_news_data


def _extract_news_data_by_topic(
    topics: list[str],
    period_days: int = 5,
    sleep_time: int = 5,
    max_results: int = 20,
    end_date: Optional[datetime] = None,
) -> list[dict]:
    """Extract news data for a list of topics.

    Args:
        topics (list[str]): List of topics to search for news.
        period_days (int, optional): Number of days to look back for news. Defaults to 5.
        sleep_time (int, optional): Time to wait (in seconds) between requests. Defaults to 5.
        max_results (int, optional): Maximum number of results per topic. Defaults to 20.
        end_date (Optional[datetime], optional): End date for news search. Defaults to None.

    Returns:
        list[dict]: List of raw news data dictionaries.
    """
    all_news_data = []
    if end_date is None:
        gnews_client = GNews(
            language="en",
            country="US",
            max_results=max_results,
            period=f"{period_days}d",
        )
    else:
        start_date = end_date - timedelta(days=period_days)
        gnews_client = GNews(
            language="en",
            country="US",
            max_results=max_results,
            start_date=start_date,
            end_date=end_date,
        )

    for topic in topics:
        logger.info(f"Fetching news for topic: '{topic}'...")
        try:
            news_for_keyword = gnews_client.get_news(topic)

            # Attach topic to each article to track source
            for article in news_for_keyword:
                article["keyword"] = topic
                article["prior"] = 1

            all_news_data.extend(news_for_keyword)

        except Exception as e:
            logger.err(f"Failed to fetch news for '{topic}'. Error: {e}")

        # Always delay to avoid being blocked
        time.sleep(sleep_time)

    return all_news_data


def _normalize_text(text: str) -> str:
    """Normalize text to create consistent identifiers.

    Args:
        text (str): Text to normalize.

    Returns:
        str: Normalized text.
    """
    if not text:
        return ""
    # Convert to lowercase
    text = text.lower()
    # Remove punctuation
    text = re.sub(r"[^\w\s]", "", text)
    # Remove extra whitespace
    text = " ".join(text.split())
    return text


def _normalize_url(url: str) -> str:
    """Normalize URL to remove unnecessary elements.

    Args:
        url (str): URL to normalize.

    Returns:
        str: Normalized URL.
    """
    if not url:
        return ""
    parsed = urlparse(url)
    # Reconstruct URL with core components only, ignoring query params, fragment
    # Can be customized to keep important query params if needed
    clean_url = urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", "", ""))
    # Ensure consistent trailing slash or no trailing slash
    return clean_url.lower()


def _generate_article_uuid(link: str, title: str) -> str:
    """Generate a unique and consistent UUID v5 for a specific article based on normalized link and title.

    Args:
        link (str): Article URL.
        title (str): Article title.

    Returns:
        str: UUID v5 string.
    """
    normalized_link = _normalize_url(link)
    normalized_title = _normalize_text(title)

    # Use a clear separator to avoid collisions
    # Example: link='ab', title='c' and link='a', title='bc' both create 'abc'
    # 'ab|c' and 'a|bc' will be different.
    canonical_string = f"{normalized_link}|{normalized_title}"

    return str(uuid.uuid5(uuid.NAMESPACE_URL, canonical_string))


def _create_content_hash(text: str) -> str:
    """Create a SHA-256 hash from normalized text.

    Args:
        text (str): Text to hash.

    Returns:
        str: SHA-256 hash string.
    """
    normalized = _normalize_text(text)
    # Use SHA-256 for high security and near-impossibility of collisions
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _transform_element(element: dict):
    """Transform a GNews dictionary into the database schema.

    Args:
        element (dict): Raw news data from GNews.

    Returns:
        dict: Transformed news data compatible with database schema.

    Raises:
        FetchException: If required fields are missing from the news data.
    """
    transformed = {}

    # GNews doesn't provide UUID, we'll create one based on link or uuid4
    # Use link as base to create more stable UUID, avoiding duplicates
    link = element.get("url")
    title = element.get("title")
    if (not link) or (not title):
        raise FetchException(
            "News article is missing 'url', cannot create a stable UUID."
        )

    transformed["news_uuid"] = _generate_article_uuid(link, title)

    transformed["title"] = title
    if not transformed["title"]:
        raise FetchException(f"News with link {link} is missing a 'title'.")

    transformed["title_hash"] = _create_content_hash(title)

    # GNews doesn't have summary, can use description
    transformed["summary"] = element.get("description", "")

    # Process time
    pub_date_str = element.get("published date")
    if pub_date_str:
        # GNews format: 'Tue, 18 Jun 2024 10:00:00 GMT'
        # Need to parse it
        try:
            transformed["publish_time"] = datetime.strptime(
                pub_date_str, "%a, %d %b %Y %H:%M:%S %Z"
            ).replace(tzinfo=timezone.utc)
        except ValueError:
            logger.warn(f"Could not parse publish date: {pub_date_str}")
    else:
        logger.warn(f"News with link {link} is missing 'published date'.")

    transformed["collect_time"] = datetime.now(timezone.utc)

    # Get publisher information
    publisher_info = element.get("publisher")  # This is a dict
    transformed["provider"] = publisher_info.get("title", "") if publisher_info else ""
    transformed["link"] = link

    # Add keyword
    transformed["keyword"] = element["keyword"]
    transformed["news_prior"] = element["prior"]

    return transformed


def _transform(data: list[dict]):
    """Transform raw news data into database schema.

    Args:
        data (list[dict]): List of raw news data dictionaries.

    Returns:
        list[dict]: List of transformed news data dictionaries.
    """
    transformed_data = []
    for element in data:
        try:
            transformed_data.append(_transform_element(element))
        except FetchException as e:
            logger.warn(e.msg)
            continue
    return transformed_data


def full_pipeline(
    news_service: DataNewsService,
    keywords: list[str],
    topics: list[str],
    period_days: int = 5,
    max_results: int = 20,
    sleep_time: int = 5,
    end_date: Optional[datetime] = None,
):
    """Execute complete pipeline to fetch universal news.

    Args:
        news_service (DataNewsService): Service to manage news data storage.
        keywords (list[str]): List of keywords to search for news.
        topics (list[str]): List of topics to search for news.
        period_days (int, optional): Number of days to look back for news. Defaults to 5.
        max_results (int, optional): Maximum number of results per search. Defaults to 20.
        sleep_time (int, optional): Time to wait (in seconds) between requests. Defaults to 5.
        end_date (Optional[datetime], optional): End date for news search. Defaults to None.
    """
    try:
        logger.info(f"Getting universal news for {len(keywords)} keywords...")
        raw_data1 = _extract_news_data_by_keyword(
            keywords, period_days, sleep_time, max_results, end_date
        )

        logger.info(f"Getting universal news for {len(topics)} topics...")
        raw_data2 = _extract_news_data_by_topic(
            topics, period_days, sleep_time, max_results, end_date
        )

        raw_data = raw_data1 + raw_data2

        logger.info(f"Transforming {len(raw_data)} news articles...")
        transformed_data = _transform(raw_data)

        logger.info(f"Loading {len(transformed_data)} news articles to DB...")
        news_service.add_news(
            data=transformed_data, type="universal", unique_cols=["title_hash"]
        )

        logger.info(f"Successfully processed universal news!")
    except Exception as e:
        logger.err(f"An unknown exception occurred in the universal news pipeline: {e}")


if __name__ == "__main__":
    end_date = (
        datetime.strptime(sys.argv[1], "%Y-%m-%d") if len(sys.argv) >= 2 else None
    )
    period_days = int(sys.argv[2]) if len(sys.argv) >= 3 else 7

    print(end_date)

    engine = get_singleton_rdbms_engine()
    news_service = DataNewsService(engine)

    full_pipeline(
        news_service=news_service,
        keywords=UNIVERSAL_KEYWORDS_EN,
        topics=UNIVERSAL_TOPIC_EN,
        period_days=period_days,
        max_results=15,
        sleep_time=2,
        end_date=end_date,
    )
