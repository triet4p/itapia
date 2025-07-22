from itapia_common.dblib.services import APIMetadataService, APINewsService, APIPricesService
from itapia_common.dblib.session import get_rdbms_session, get_redis_connection

from sqlalchemy.orm import Session
from redis.client import Redis

from fastapi import Depends

def get_metadata_service(rdbms_session: Session = Depends(get_rdbms_session)) -> APIMetadataService:
    return APIMetadataService(rdbms_session)

def get_prices_service(rdbms_session: Session = Depends(get_rdbms_session),
                       redis_client: Redis = Depends(get_redis_connection),
                       metadata_service: APIMetadataService = Depends(get_metadata_service)):
    return APIPricesService(rdbms_session, redis_client, metadata_service)

def get_news_service(rdbms_session: Session = Depends(get_rdbms_session),
                     metadata_service: APIMetadataService = Depends(get_metadata_service)):
    return APINewsService(rdbms_session, metadata_service)