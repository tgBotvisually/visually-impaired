from aiogram import F, Router
from aiogram.types import Message
from aiogram.filters import CommandStart, CommandObject
from aiogram.fsm.context import FSMContext

from keyboard.reply_kb import MainKb
from utils.handlers_util import send_voice_message, get_form_id
from utils.lexicon import text, BUTTONS, COMPANY
from services.forms import ya_forms
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
async def get_url_handler(message: Message, state: FSMContext):
    me = await message.bot.get_me()
    form_id = get_form_id(message.text)

    await state.update_data(form_id=form_id)

    await message.answer(
        f'Ваша ссылка: https://t.me/{me.username}?start={form_id}',
        reply_markup=MainKb(BUTTONS['forms']).get_keyboard()
    )


@router.message(F.text == 'Создать ссылку')
async def create_form_handler(message: Message):
    await message.answer(text=text['primer'])


@router.message(F.text == 'Да')
async def forms_question_handler(message: Message):
    # тут приходят вопросы пошагово
    pass


@router.message(F.text == 'Открыть форму')
async def get_form_handler(message: Message, state: FSMContext):
    form_id = state.get_data('form_id')
    form_data = await ya_forms.get_form_data(form_id)

    response_text = (
        f"📋 Вы открыли форму \"{form_data.name}\"\n"
        f"🏢 Отправитель: {COMPANY}'\n"
        f"❓ Количество вопросов: {ya_forms.questions_count(form_data)}\n"
        f"\nВопросы:\n"
    )

    question_number = 1
    for page in form_data.pages:
        for item in page.items:
            response_text += f"• {item.label}\n"
            question_number += 1

    await state.update_data(form_data=form_data)

    await message.answer(
        text=response_text,
        reply_markup=MainKb(['Заполнить форму', 'Инструкция']).get_keyboard()
    )

@router.message(F.text == 'Заполнить форму')
async def start_form_filling(message: Message, state: FSMContext):
    await message.answer(
        text="🚀 Начинаем заполнение формы!",
        reply_markup=MainKb(['Первый вопрос']).get_keyboard()
    )
