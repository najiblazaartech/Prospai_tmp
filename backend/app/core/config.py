from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    SECRET_KEY: str = "dev-secret"
    DATABASE_URL: str = "postgresql+psycopg://prospai:prospai@localhost:5432/prospai"
    ENV: str = "development"
    MISTRAL_API_KEY: str = ""
    APOLLO_API_KEY: str = ""
    DROPCONTACT_API_KEY: str = ""
    # En production, Render définit WEB_DISCOVERY=true pour interdire les données fictives.
    WEB_DISCOVERY: bool = False
    # Origines web autorisées, séparées par des virgules.
    CORS_ORIGINS: str = "http://localhost:3000"

    # Conformité : revue manuelle par défaut (RGPD / LinkedIn ToS)
    MANUAL_REVIEW_DEFAULT: bool = True
    MAX_LINKEDIN_ACTIONS_PER_DAY: int = 80

    class Config:
        env_file = ".env"

    @property
    def is_mock(self) -> bool:
        return not (self.APOLLO_API_KEY or self.MISTRAL_API_KEY)


@lru_cache
def get_settings() -> Settings:
    return Settings()
