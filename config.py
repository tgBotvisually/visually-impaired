from pydantic_settings import  BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Сеттинги переменных окружения."""
    BOT_TOKEN: str
    SPEECHKIT_TOKEN: str
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')

config = Settings()