from aiogram import F, Router
from aiogram.types import Message, BufferedInputFile
from aiogram.filters import CommandStart

from services.silero import silero


router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer('Тг бот для речи')


@router.message(F.text)
async def text_handler(message: Message):
    text = message.text

    output_file = "output.wav"
    speech_file = silero.text_to_speech(text=text, output_file=output_file)

    with open(speech_file, 'rb') as f:
        audio_data = f.read()

    voice_input_file = BufferedInputFile(audio_data, filename="voice.ogg")
    await message.answer_voice(voice=voice_input_file)