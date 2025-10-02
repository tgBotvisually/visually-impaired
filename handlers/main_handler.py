from aiogram import F, Router
from aiogram.types import Message
from aiogram.filters import CommandStart, CommandObject

from keyboard.reply_kb import MainKb
from utils.handlers_util import send_voice_message, get_form_id
from utils.lexicon import text, BUTTONS
# from services.forms import YandexForms
# from config import config
router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, command: CommandObject):
    # if command.args:
    #     await another_algorithm(form_id=command.args)
    #     если мы переходим по ссылке f'https://t.me/{me.username}?start={form_id}'
    #     действия бота уже идут к заполнению формы
    await send_voice_message(message, text['help'],'help.wav', BUTTONS['start'])


@router.message(F.text == 'Продолжить')
async def continue_handler(message: Message):
    await send_voice_message(message, text['instruction'],'instruction.wav', BUTTONS['forms'])


@router.message(F.text == 'Политика конфиденциальности')
async def privacy_handler(message: Message):
    await send_voice_message(message, text['privacy'],'privacy.wav', BUTTONS['forms'])


@router.message(F.text.contains('forms.yandex.ru'))
async def get_url_handler(message: Message):
    me = await message.bot.get_me()
    form_id = get_form_id(message.text)
    await message.answer(
        f'Ваша ссылка: https://t.me/{me.username}?start={form_id}',
        reply_markup=MainKb(BUTTONS['forms']).get_keyboard()
    )


@router.message(F.text == 'Создать ссылку')
async def create_form_handler(message: Message):
    await message.answer(text=text['primer'])



@router.message(F.text == 'Открыть форму')
async def get_form_handler(message: Message):
    await message.answer(text=text['open_form'])



@router.message(F.text == 'Да')
async def forms_question_handler(message: Message):
    # тут приходят вопросы пошагово
    pass


