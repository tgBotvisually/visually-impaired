from aiogram import F, Router
from aiogram.types import Message
from aiogram.filters import CommandStart, CommandObject
from aiogram.fsm.context import FSMContext

from keyboard.reply_kb import MainKb
from utils.handlers_util import send_voice_message, get_form_id
from utils.constants import (INSTRUCTION_TEXT, HELP_TEXT, PRIVACY_TEXT,
                             FORM_EXAMPLE, PLEASE_COMPLETE,
                             REQUIRED_FIELD, BUTTONS, COMPANY)
from services.forms import ya_forms
from services.models import FormItem
from utils.form_utils import (FormNavigation,
                              format_question_text,
                              create_answer_structure,
                              format_confirmation_message,
                              get_keyboard_for_question,
                              get_intro_form_header,
                              is_required)
from states.states import FormFilling


router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, command: CommandObject):
    # if command.args:
        # form_id = command.args
        # await get_form_handler(form_id)

    await send_voice_message(message, HELP_TEXT,
                             'help.wav', BUTTONS['start'])


@router.message(F.text == 'Продолжить')
async def continue_handler(message: Message):
    await send_voice_message(message, INSTRUCTION_TEXT,
                             'instruction.wav', BUTTONS['forms'])


@router.message(F.text == 'Политика конфиденциальности')
async def privacy_handler(message: Message):
    await send_voice_message(message, PRIVACY_TEXT,
                             'privacy.wav', BUTTONS['forms'])


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
    await message.answer(text=FORM_EXAMPLE)


@router.message(F.text == 'Открыть форму')
async def get_form_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    form_id = data.get('form_id')
    form_data = await ya_forms.get_form_data(str(form_id))
    form_nav = FormNavigation(form_data)

    response_text = get_intro_form_header(
        title=form_data.name,
        company=COMPANY,
        questions_count=form_nav.get_total_questions()
    )

    question_number = 1
    for page in form_data.pages:
        for item in page.items:
            if not item.hidden:
                response_text += f'{question_number}. {item.label}'
                if item.validations and is_required(item.validations):
                    response_text += REQUIRED_FIELD
                response_text += '\n'
                if item.comment:
                    response_text += f'<i>{item.comment}</i>\n'
                response_text += '\n'
                question_number += 1
    response_text += PLEASE_COMPLETE
    await state.update_data(form_data=form_data)

    await send_voice_message(
        message, response_text,
        f'{form_data.name}.wav',
        BUTTONS['form_intro']
    )


@router.message(F.text == 'Заполнить форму')
async def start_form_filling(message: Message, state: FSMContext):
    # Получаем данные формы
    data = await state.get_data()
    form_data = data.get('form_data')

    if not form_data:
        await message.answer("Ошибка: данные формы не найдены")
        return

    # Инициализируем навигацию по форме
    form_nav = FormNavigation(form_data)
    current_question = form_nav.get_current_question()

    if not current_question:
        await message.answer("В форме нет вопросов для заполнения")
        return

    page_idx, item_idx, question_item = current_question

    # Инициализируем словарь для ответов
    await state.update_data(
        answers={},
        form_navigation={
            'current_index': 0,
            'total_questions': form_nav.get_total_questions(),
            'question_ids': [q[2].id for q in form_nav.visible_questions]
        }
    )

    await state.set_state(FormFilling.waiting_for_answers)

    question_text = format_question_text(
        question_item,
        1,
        form_nav.get_total_questions()
    )

    keyboard = get_keyboard_for_question(True, False)

    await message.answer(
        text=f"🚀 Начинаем заполнение формы!\n\n{question_text}",
        reply_markup=MainKb(keyboard).get_keyboard()
    )


@router.message(FormFilling.waiting_for_answers, F.text)
async def process_answer(message: Message, state: FSMContext):
    data = await state.get_data()
    form_data = data.get('form_data')
    answers = data.get('answers', {})
    nav_data = data.get('form_navigation', {})

    current_index = nav_data.get('current_index', 0)
    total_questions = nav_data.get('total_questions', 0)
    question_ids = nav_data.get('question_ids', [])

    if current_index >= len(question_ids):
        await message.answer("Ошибка: индекс вопроса вне диапазона")
        return

    # Получаем текущий вопрос
    current_question_id = question_ids[current_index]
    current_question = None
    for page in form_data.pages:
        for item in page.items:
            if item.id == current_question_id:
                current_question = item
                break
        if current_question:
            break

    if not current_question:
        await message.answer("Ошибка: вопрос не найден")
        return

    # Обрабатываем ответ
    processed_answer = await process_user_answer(message.text,
                                                 current_question)
    if processed_answer is None:
        # Ответ невалидный, остаемся на том же вопросе
        return

    # Сохраняем ответ
    answers[current_question_id] = processed_answer

    # Переходим к следующему вопросу или завершаем
    next_index = current_index + 1
    await state.update_data(answers=answers)

    if next_index < total_questions:
        # Показываем следующий вопрос
        nav_data['current_index'] = next_index
        await state.update_data(form_navigation=nav_data)

        next_question_id = question_ids[next_index]
        next_question = None
        for page in form_data.pages:
            for item in page.items:
                if item.id == next_question_id:
                    next_question = item
                    break
            if next_question:
                break

        question_text = format_question_text(
            next_question,
            next_index + 1,
            total_questions
        )

        is_last = next_index == total_questions - 1
        keyboard = get_keyboard_for_question(False, is_last)

        await message.answer(
            text=f"✅ Ответ сохранен!\n\n{question_text}",
            reply_markup=MainKb(keyboard).get_keyboard()
        )

    else:
        # Все вопросы пройдены, показываем подтверждение
        await state.set_state(FormFilling.confirmation)

        confirmation_text = await format_confirmation_message(
            form_data, answers
        )

        await message.answer(
            text=confirmation_text,
            reply_markup=MainKb(['Отправить', 'Начать заново']).get_keyboard()
        )


async def process_user_answer(user_input: str, question: FormItem):
    """Обрабатывает и валидирует ответ пользователя"""
    if question.type == 'enum' and question.items:
        # Вопрос с выбором варианта
        try:
            choice_index = int(user_input) - 1
            if 0 <= choice_index < len(question.items):
                return [question.items[choice_index].id]
            else:
                return None
        except ValueError:
            return None

    elif question.type == 'string':
        # Текстовый вопрос
        return user_input.strip()

    # Для других типов вопросов можно добавить обработку
    return user_input


@router.message(FormFilling.waiting_for_answers, F.text == 'Изменить прошлый ответ')
async def change_previous_answer(message: Message, state: FSMContext):
    data = await state.get_data()
    nav_data = data.get('form_navigation', {})

    current_index = nav_data.get('current_index', 0)
    total_questions = nav_data.get('total_questions', 0)
    question_ids = nav_data.get('question_ids', [])

    if current_index > 0:
        nav_data['current_index'] = current_index - 1
        await state.update_data(form_navigation=nav_data)

        form_data = data.get('form_data')
        prev_question_id = question_ids[current_index - 1]
        prev_question = None

        for page in form_data.pages:
            for item in page.items:
                if item.id == prev_question_id:
                    prev_question = item
                    break
            if prev_question:
                break

        question_text = format_question_text(
            prev_question,
            current_index,  # Текущий индекс теперь предыдущий
            total_questions
        )

        is_last = current_index - 1 == total_questions - 1
        keyboard = get_keyboard_for_question(current_index - 1 == 0, is_last)

        await message.answer(
            text=f"↩️ Возвращаемся к предыдущему вопросу:\n\n{question_text}",
            reply_markup=MainKb(keyboard).get_keyboard()
        )
    else:
        await message.answer("Это первый вопрос, нельзя вернуться назад")


@router.message(FormFilling.waiting_for_answers, F.text == 'Показать все ответы')
async def show_all_answers_preview(message: Message, state: FSMContext):
    data = await state.get_data()
    form_data = data.get('form_data')
    answers = data.get('answers', {})

    confirmation_text = await format_confirmation_message(form_data, answers)

    await message.answer(
        text=confirmation_text,
        reply_markup=MainKb(['Продолжить заполнение', 'Начать заново']).get_keyboard()
    )


@router.message(FormFilling.waiting_for_answers, F.text == 'Продолжить заполнение')
async def continue_filling(message: Message, state: FSMContext):
    data = await state.get_data()
    nav_data = data.get('form_navigation', {})
    form_data = data.get('form_data')

    current_index = nav_data.get('current_index', 0)
    total_questions = nav_data.get('total_questions', 0)
    question_ids = nav_data.get('question_ids', [])

    current_question_id = question_ids[current_index]
    current_question = None

    for page in form_data.pages:
        for item in page.items:
            if item.id == current_question_id:
                current_question = item
                break
        if current_question:
            break

    question_text = format_question_text(
        current_question,
        current_index + 1,
        total_questions
    )

    is_last = current_index == total_questions - 1
    keyboard = get_keyboard_for_question(False, is_last)

    await message.answer(
        text=f"Продолжаем заполнение:\n\n{question_text}",
        reply_markup=MainKb(keyboard).get_keyboard()
    )


@router.message(FormFilling.confirmation, F.text == 'Отправить')
async def send_results(message: Message, state: FSMContext):
    data = await state.get_data()
    answers = data.get('answers', {})
    form_data = data.get('form_data')
    form_id = data.get('form_id')

    try:
        # Создаем структуру ответов для Яндекс.Форм
        structured_answers = create_answer_structure(form_data, answers)

        # Отправляем ответы в Яндекс Формы
        success = await ya_forms.fill_the_form(str(form_id),
                                               structured_answers)

        if success:
            await message.answer(
                "✅ Форма успешно отправлена!",
                reply_markup=MainKb(BUTTONS['start']).get_keyboard()
            )
        else:
            await message.answer(
                "❌ Ошибка при отправке формы",
                reply_markup=MainKb(BUTTONS['start']).get_keyboard()
            )

    except Exception as e:
        await message.answer(
            f"❌ Ошибка при отправке: {str(e)}",
            reply_markup=MainKb(BUTTONS['start']).get_keyboard()
        )

    finally:
        await state.clear()


@router.message(FormFilling.confirmation, F.text == 'Начать заново')
async def restart_form(message: Message, state: FSMContext):
    # Очищаем ответы и начинаем заново
    await state.update_data(answers={})

    data = await state.get_data()
    form_data = data.get('form_data')

    # Сбрасываем навигацию
    form_nav = FormNavigation(form_data)
    current_question = form_nav.get_current_question()

    page_idx, item_idx, question_item = current_question

    await state.update_data(
        form_navigation={
            'current_index': 0,
            'total_questions': form_nav.get_total_questions(),
            'question_ids': [q[2].id for q in form_nav.visible_questions]
        }
    )

    await state.set_state(FormFilling.waiting_for_answers)

    question_text = format_question_text(
        question_item,
        1,
        form_nav.get_total_questions()
    )

    await message.answer(
        text=f"🔄 Начинаем заполнение формы заново!\n\n{question_text}",
        reply_markup=MainKb(['Заполнить форму']).get_keyboard()
    )
