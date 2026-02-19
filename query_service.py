import pandas as pd
import hashlib
import json

from langchain_openai import ChatOpenAI
from langchain_experimental.agents import create_pandas_dataframe_agent
from langchain.agents.agent_types import AgentType

from app.core.config import settings
from app.db.redis import redis_client

CACHE_TTL = 3600


def _cache_key(file_id: str, question: str) -> str:
    raw = f"{file_id}:{question.strip().lower()}"
    return "query:" + hashlib.md5(raw.encode()).hexdigest()


def get_cached_answer(file_id: str, question: str):
    key = _cache_key(file_id, question)
    cached = redis_client.get(key)
    if cached:
        return json.loads(cached)
    return None


def cache_answer(file_id: str, question: str, answer: str):
    key = _cache_key(file_id, question)
    redis_client.setex(key, CACHE_TTL, json.dumps({"answer": answer}))


def load_dataframe(file_path: str, file_type: str) -> pd.DataFrame:
    if file_type == "csv":
        return pd.read_csv(file_path)
    return pd.read_excel(file_path)


def query_dataframe(file_path: str, file_type: str, question: str, model: str = "gpt-3.5-turbo") -> str:
    df = load_dataframe(file_path, file_type)

    llm = ChatOpenAI(
        model=model,
        temperature=0,
        openai_api_key=settings.OPENAI_API_KEY
    )

    agent = create_pandas_dataframe_agent(
        llm=llm,
        df=df,
        agent_type=AgentType.OPENAI_FUNCTIONS,
        verbose=False,
        allow_dangerous_code=True
    )

    result = agent.invoke({"input": question})
    return result.get("output", "Could not generate an answer.")
