from pydantic_settings import  BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Сеттинги переменных окружения.

    ---

    # TODO
    Время жизни IAM-токена — не больше 12 часов, но рекомендуется запрашивать
    его чаще, например каждый час.
    https://yandex.cloud/ru/docs/iam/operations/iam-token/create#via-cli
    """
    model_config = SettingsConfigDict(
        env_file='.env', env_file_encoding='utf-8'
    )

    BOT_TOKEN: str
    AUTH_YANDEX_FORMS: str
    FORMS_PUBLIC_API: str
    YAFORMS_BASE_URL: str
    TELEGRAM_CHAT_ID: str
    WEBAPP_HOST: str = '::'
    WEBAPP_PORT: int = 8080
    YAFORMS_WEBHOOK_PATH: str = '/yandex/forms'


config = Settings()
