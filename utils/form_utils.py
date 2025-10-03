from typing import Dict, List, Tuple
from services.models import FormData, FormItem, Validation
# from aiogram.fsm.context import FSMContext


class FormNavigation:
    def __init__(self, form_data: FormData):
        self.form_data = form_data
        self.visible_questions = self._get_visible_questions()
        self.current_question_index = 0

    def _get_visible_questions(self) -> List[Tuple[int, int, FormItem]]:
        """
        Возвращает список видимых вопросов
        в формате (page_index, item_index, item)
        """
        visible_questions = []
        for page_idx, page in enumerate(self.form_data.pages):
            for item_idx, item in enumerate(page.items):
                if not item.hidden:
                    visible_questions.append((page_idx, item_idx, item))
        return visible_questions

    def get_current_question(self) -> Tuple[int, int, FormItem]:
        """Возвращает текущий вопрос"""
        if self.current_question_index < len(self.visible_questions):
            return self.visible_questions[self.current_question_index]
        return None

    def get_next_question(self) -> Tuple[int, int, FormItem]:
        """Переходит к следующему вопросу и возвращает его"""
        if self.current_question_index < len(self.visible_questions) - 1:
            self.current_question_index += 1
            return self.visible_questions[self.current_question_index]
        return None

    def get_previous_question(self) -> Tuple[int, int, FormItem]:
        """Переходит к предыдущему вопросу и возвращает его"""
        if self.current_question_index > 0:
            self.current_question_index -= 1
            return self.visible_questions[self.current_question_index]
        return None

    def get_question_by_index(self, index: int) -> Tuple[int, int, FormItem]:
        """Возвращает вопрос по индексу"""
        if 0 <= index < len(self.visible_questions):
            self.current_question_index = index
            return self.visible_questions[index]
        return None

    def is_last_question(self) -> bool:
        """Проверяет, является ли текущий вопрос последним"""
        return self.current_question_index == len(self.visible_questions) - 1

    def get_total_questions(self) -> int:
        """Возвращает общее количество вопросов"""
        return len(self.visible_questions)


def is_required(validations: list[Validation]) -> bool:
    return any(item.type == 'required' for item in validations)


def format_question_text(question: FormItem, question_number: int,
                         total_questions: int) -> str:
    """Форматирует текст вопроса"""
    is_required = any(validation.type == 'required' for validation in (
        question.validations or []))

    question_text = f"Вопрос {question_number}/{total_questions}"
    if is_required:
        question_text += " (обязательный вопрос)"
    question_text += f"\n{question.label}\n"

    if question.comment:
        question_text += f"<i>{question.comment}</i>\n"

    if question.type == 'enum' and question.items:
        question_text += "\nВарианты ответов:\n"
        for i, option in enumerate(question.items, 1):
            question_text += f"{i}. {option.label}\n"
        question_text += "\nНапишите номер выбранного варианта"

    elif question.type == 'string':
        if question.multiline:
            question_text += "\n(введите текст, можно несколько строк)"
        else:
            question_text += "\n(введите текст)"

    return question_text


def create_answer_structure(form_data: FormData, answers: Dict) -> Dict:
    """Создает структуру ответов для отправки в Яндекс.Формы"""
    result = {}

    for page in form_data.pages:
        for item in page.items:
            if not item.hidden and item.id in answers:
                if item.type == 'enum':
                    result[item.id] = {"choices": answers[item.id]}
                else:
                    result[item.id] = {"text": answers[item.id]}
    return result


async def format_confirmation_message(form_data: FormData, answers: Dict) -> str:
    """Форматирует сообщение с подтверждением ответов"""
    message = "✅ Все вопросы пройдены!\n\n"
    message += "Проверьте ваши ответы:\n\n"

    question_number = 1
    for page in form_data.pages:
        for item in page.items:
            if not item.hidden:
                answer = answers.get(item.id, "Не отвечено")
                if item.type == 'enum' and item.items and isinstance(answer, list):
                    option_labels = []
                    for choice_id in answer:
                        option = next((opt for opt in item.items if opt.id == choice_id), None)
                        if option:
                            option_labels.append(option.label)
                    answer = ", ".join(option_labels) if option_labels else "Не выбрано"

                message += f"{question_number}. {item.label}: {answer}\n"
                question_number += 1

    message += "\nВы можете отправить результаты прямо сейчас.\n"
    message += "Если хотите заполнить форму заново, выберите опцию \"Начать заново\"."

    return message


def get_keyboard_for_question(is_first: bool, is_last: bool) -> list:
    """Возвращает клавиатуру для вопроса"""
    if is_first:
        return ['Заполнить форму']
    elif is_last:
        return ['Изменить прошлый ответ', 'Показать все ответы']
    else:
        return ['Изменить прошлый ответ']


def get_intro_form_header(title: str, company: str, questions_count: int):
    return (
        f"📋 Вы открыли форму \"{title}\"\n"
        f"🏢 Отправитель: {company}'\n"
        f"❓ Количество вопросов: {questions_count}\n"
        f"\nВопросы:\n"
    )
