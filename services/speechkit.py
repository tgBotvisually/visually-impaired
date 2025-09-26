import aiohttp
from http import HTTPStatus

from config import config


class YandexTTS:
    def __init__(self):
        self.api_key = config.SPEECHKIT_TOKEN
        self.folder = config.FOLDER_SPEECHKIT
        self.url = 'https://tts.api.cloud.yandex.net/speech/v1/tts:synthesize'

    async def synthesize(self, text, voice: str = 'alena', emotion: str = 'neutral'):
        headers = {
            # 'Authorization': f'Api-Key {self.iam_key}' #  для IAM токена 12 часов
            'Authorization':f'Api-Key {self.api_key}'  # https://cloud.yandex.ru/docs/speechkit/concepts/auth
        }

        data = {
            'folderId': self.folder,
            'text':text,
            'lang':'ru-RU',
            'voice': voice,
            'emotion':emotion,
            'format':'oggopus',
            'sampleRateHertz':48000,
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(self.url, data=data, headers=headers) as response:
                if response.status == HTTPStatus.OK:
                    return await response.read()
                else:
                    error_text = await response.text()
                    raise Exception(f'yandex tts error: {error_text}')

yandex_tts = YandexTTS()