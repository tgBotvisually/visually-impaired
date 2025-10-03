import re
from services.silero import silero
from aiogram.types import Message, BufferedInputFile
from keyboard.reply_kb import MainKb


async def send_voice_message(message: Message, text: str, filename: str, keyboard_buttons: list):
    audio_bytes = silero.text_to_speech(text=text)

    voice_input_file = BufferedInputFile(audio_bytes, filename=filename)
    await message.answer(text=text)
    await message.answer_voice(
        voice=voice_input_file,
        reply_markup=MainKb(keyboard_buttons).get_keyboard()
    )


def get_form_id(url: str):
    match = re.search(r'([a-f0-9]{8,32})', url)
    print(match)
    return match.group(1)
