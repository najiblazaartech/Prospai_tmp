from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    SECRET_KEY: str = "dev-secret"
    DATABASE_URL: str = "postgresql+psycopg://prospai:prospai@localhost:5432/prospai"
    ENV: str = "development"
    MISTRAL_API_KEY: str = ""
    APOLLO_API_KEY: str = ""
    DROPCONTACT_API_KEY: str = ""
    # Decouverte web en direct (gratuite, sans cle). Off en tests pour rester
    # deterministes ; on en production (voir .env.example / docker-compose).
    WEB_DISCOVERY: bool = False

    # Conformite : revue manuelle par defaut (RGPD / LinkedIn ToS)
    MANUAL_REVIEW_DEFAULT: bool = True
    # Quotas anti-ban conservateurs
    MAX_LINKEDIN_ACTIONS_PER_DAY: int = 80

    class Config:
        env_file = ".env"

    @property
    def is_mock(self) -> bool:
        return not (self.APOLLO_API_KEY or self.MISTRAL_API_KEY)


@lru_cache
def get_settings() -> Settings:
    return Settings()
