import asyncio
import boto3
import functools
import logging
from langchain_aws import ChatBedrock
from settings import config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("coding_assistant")

def log_decorator(func):
    
    if asyncio.iscoroutinefunction(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            logger.info(f"-> {func.__name__} called")
            result = await func(*args, **kwargs)
            logger.info(f"<- {func.__name__} completed")
            return result
        return async_wrapper
    else:
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            logger.info(f"-> {func.__name__} called")
            result = func(*args, **kwargs)
            logger.info(f"<- {func.__name__} completed")
            return result
        return sync_wrapper


def get_bedrock_client():
    return boto3.client(
        service_name="bedrock-runtime",
        region_name=config.REGION,
    )


@log_decorator
def get_llm(max_tokens: int = 500, temperature: float = 0.7) -> ChatBedrock:
    return ChatBedrock(
        client=get_bedrock_client(),
        model_id=config.MODEL_ID,
        provider="amazon",
        model_kwargs={
            "max_tokens": max_tokens,
            "temperature": temperature,
        },
    )

def get_db_uri():
    return(f"postgresql://{config.db_username}:{config.db_password}"
           f"@{config.db_host}:{config.db_port}/{config.db_name}")
