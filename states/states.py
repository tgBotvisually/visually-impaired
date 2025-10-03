from aiogram.fsm.state import State, StatesGroup


class FormFilling(StatesGroup):
    waiting_for_answers = State()
    confirmation = State()
