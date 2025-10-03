from aiogram import F, Router
from aiogram.types import Message
from aiogram.filters import CommandStart, CommandObject
from aiogram.fsm.context import FSMContext

from keyboard.reply_kb import MainKb
from utils.handlers_util import send_voice_message, get_form_id
from utils.constants import (INSTRUCTION_TEXT, HELP_TEXT, PRIVACY_TEXT,
                             FORM_EXAMPLE, PLEASE_COMPLETE,
                             REQUIRED_FIELD, BUTTONS, COMPANY,
                             OK, NOT_OK, BEGIN, QUESTION_OK,
                             SAY_NO, SAY_YES, OUTPUT)
from services.forms import ya_forms
from services.models import FormItem
from utils.form_utils import (FormNavigation,
                              format_question_text,
                              format_confirmation_message,
                              get_keyboard_for_question,
                              get_intro_form_header,
                              is_required)
from states.states import FormFilling

# from pprint import pprint
from datetime import datetime
import re


router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, command: CommandObject):
    # if command.args:
        # form_id = command.args
        # await get_form_handler(form_id)

    await send_voice_message(message, HELP_TEXT,
                             'help.wav', BUTTONS['start'])


@router.message(FormFilling.waiting_for_answers, F.text == 'Назад')
async def handle_change_answer_button(message: Message, state: FSMContext):
    await change_previous_answer(message, state)


router.message.register(handle_change_answer_button,
                        FormFilling.waiting_for_answers,
                        F.text == 'Назад')


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

    # Инициализируем навигацию по форме
    form_nav = FormNavigation(form_data)
    current_question = form_nav.get_current_question()

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

    keyboard = get_keyboard_for_question(is_first=True, is_last=False)

    await send_voice_message(
        message, BEGIN + question_text,
        'begin.wav', keyboard
    )

    # await message.answer(
    #     text=f"🚀 Начинаем заполнение формы!\n\n{question_text}",
    #     reply_markup=MainKb(keyboard).get_keyboard()
    # )


@router.message(FormFilling.waiting_for_answers, F.text)
async def process_answer(message: Message, state: FSMContext):
    data = await state.get_data()
    form_data = data.get('form_data')
    answers = data.get('answers', {})
    nav_data = data.get('form_navigation', {})

    current_index = nav_data.get('current_index', 0)
    total_questions = nav_data.get('total_questions', 0)
    question_ids = nav_data.get('question_ids', [])

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
        # pprint(answers)

        await send_voice_message(
            message, QUESTION_OK + question_text,
            f'{current_index}.wav',
            keyboard
        )

        # await message.answer(
        #     text=f"✅ Ответ сохранен!\n\n{question_text}",
        #     reply_markup=MainKb(keyboard).get_keyboard()
        # )

    else:
        # Все вопросы пройдены, показываем подтверждение
        await state.set_state(FormFilling.confirmation)

        confirmation_text = await format_confirmation_message(
            form_data, answers
        )
        pprint(answers)
        await send_voice_message(
            message, confirmation_text,
            'done.wav',
            BUTTONS['submit']
        )
        # await message.answer(
        #     text=confirmation_text,
        #     reply_markup=MainKb(['Отправить', 'Начать заново']).get_keyboard()
        # )


async def process_user_answer(user_input: str, question: FormItem):
    """Обрабатывает и валидирует ответ пользователя"""

    # Вопрос с выбором варианта (enum)
    if question.type == 'enum' and question.items:
        return await _process_enum_answer(user_input, question)

    # Булевый вопрос (флажок)
    elif question.type == 'boolean':
        return await _process_boolean_answer(user_input, question)

    elif question.type == 'date':
        return await _process_date_answer(user_input, question)

    # Текстовый вопрос
    elif question.type == 'string':
        return user_input.strip()

    # Для других типов вопросов можно добавить обработку
    return user_input


async def _process_date_answer(user_input: str, question: FormItem):
    """Обрабатывает ответ на вопрос с датой"""
    try:
        # Пробуем разные форматы дат
        date_formats = [
            '%d.%m.%Y',  # 01.01.2023
            '%d/%m/%Y',  # 01/01/2023
            '%d-%m-%Y',  # 01-01-2023
            '%Y-%m-%d',  # 2023-01-01 (ISO format)
        ]

        user_input = user_input.strip()

        for date_format in date_formats:
            try:
                parsed_date = datetime.strptime(user_input, date_format)
                return parsed_date.strftime('%Y-%m-%d')
            except ValueError:
                continue

        return None

    except Exception:
        return None



async def _process_enum_answer(user_input: str, question: FormItem):
    """Обрабатывает ответ на вопрос с выбором варианта"""
    try:
        # Для radio-кнопок (одиночный выбор)
        if question.widget == 'radio':
            choice_index = int(user_input) - 1
            if 0 <= choice_index < len(question.items):
                return [question.items[choice_index].id]
            else:
                return None

        # Для checkbox (множественный выбор) или по умолчанию
        else:
            # Разделяем ввод по пробелам, запятым или другим разделителям
            choices = re.findall(r'\d+', user_input)
            selected_ids = []

            for choice_str in choices:
                choice_index = int(choice_str) - 1
                if 0 <= choice_index < len(question.items):
                    selected_ids.append(question.items[choice_index].id)

            # Если выбраны варианты, возвращаем их
            if selected_ids:
                return selected_ids
            else:
                return None

    except ValueError:
        return None


async def _process_boolean_answer(user_input: str, question: FormItem):
    """Обрабатывает ответ на булевый вопрос (флажок)"""
    user_input_lower = user_input.lower().strip()
    if user_input_lower in SAY_YES:
        return True
    elif user_input_lower in SAY_NO:
        return False
    else:
        # Если ввод не распознан, пытаемся интерпретировать как число
        try:
            return bool(int(user_input))
        except ValueError:
            return None


@router.message(FormFilling.waiting_for_answers, F.text == 'Назад')
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
    form_id = data.get('form_id')

    try:
        # Отправляем ответы в Яндекс Формы
        success = await ya_forms.fill_the_form(str(form_id),
                                               answers)

        if success:
            await send_voice_message(
                message, OK,
                'OK.wav', BUTTONS['start']
            )

    except Exception as e:
            await send_voice_message(
                message, NOT_OK + str(e),
                'NOT_OK.wav', BUTTONS['start']
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


@router.message(F.text == 'Отчет')
async def export_report_handler(message: Message, state: FSMContext):
    """Обработчик для выгрузки отчета"""
    data = await state.get_data()
    form_id = data.get('form_id')

    if not form_id:
        await message.answer(OUTPUT['OPEN'])
        return

    try:
        # Показываем сообщение о начале выгрузки
        wait_msg = await message.answer(OUTPUT['WAIT'])

        # Выгружаем результаты в формате xlsx
        report_data = await ya_forms.export_results(
            survey_id=str(form_id),
            format='xlsx'
        )

        if report_data:
            # Создаем файл для отправки
            from aiogram.types import BufferedInputFile

            # Получаем название формы для имени файла
            form_data = data.get('form_data')
            form_name = form_data.name if form_data else 'report'
            filename = f"{form_name}_отчет.xlsx"

            # Создаем объект файла
            report_file = BufferedInputFile(report_data, filename=filename)

            # Удаляем сообщение "ожидание"
            await wait_msg.delete()

            # Отправляем файл пользователю
            await message.answer_document(
                document=report_file,
                caption=OUTPUT['OK'] + form_name
            )
        else:
            await wait_msg.delete()
            await message.answer(OUTPUT['GG'])

    except Exception as e:
        # Удаляем сообщение "ожидание" если было
        try:
            await wait_msg.delete()
        except:
            pass

        error_msg = OUTPUT['GG2'] + str(e)
        await message.answer(error_msg)
