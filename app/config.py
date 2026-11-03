import os
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "LLM Quality Gate - AI Ops Agent"
    VERSION: str = "1.0.0"
    API_PREFIX: str = "/api"

    # LLM Settings: Groq & OpenAI
    GROQ_API_KEY: Optional[str] = os.getenv("GROQ_API_KEY", None)
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY", None)
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    # Observability & Webhooks
    LANGFUSE_PUBLIC_KEY: Optional[str] = os.getenv("LANGFUSE_PUBLIC_KEY", None)
    LANGFUSE_SECRET_KEY: Optional[str] = os.getenv("LANGFUSE_SECRET_KEY", None)
    LANGFUSE_HOST: str = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
    SLACK_WEBHOOK_URL: Optional[str] = os.getenv("SLACK_WEBHOOK_URL", None)

    # Database & Storage
    DB_PATH: str = os.getenv("DB_PATH", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "ops_agent.db"))
    JIRA_PROJECT_KEY: str = "OPS"

    # Quality Gate Thresholds
    FAITHFULNESS_THRESHOLD: float = float(os.getenv("FAITHFULNESS_THRESHOLD", "0.70"))
    ANSWER_RELEVANCY_THRESHOLD: float = float(os.getenv("ANSWER_RELEVANCY_THRESHOLD", "0.70"))
    HALLUCINATION_MAX_THRESHOLD: float = float(os.getenv("HALLUCINATION_MAX_THRESHOLD", "0.30"))

    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()
