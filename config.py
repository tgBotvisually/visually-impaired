from pydantic_settings import  BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Сеттинги переменных окружения."""
    model_config = SettingsConfigDict(
        env_file='.env', env_file_encoding='utf-8'
    )

    BOT_TOKEN: str
    AUTH_YANDEX_FORMS: str
    API_YAFORMS_BASE_URL: str
    YAFORMS_BASE_URL: str


config = Settings()
