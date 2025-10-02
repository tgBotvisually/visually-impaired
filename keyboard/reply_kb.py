from aiogram.utils.keyboard import (
    ReplyKeyboardBuilder,
    KeyboardButton,
    ReplyKeyboardMarkup
)


class ReplyBuilder:
    """Динамическая клавиатура билдер."""
    def __init__(self):
        self.keyboard = ReplyKeyboardBuilder()

    def add_buttons(self, buttons: list[str] | tuple[str]) -> None:
        for button in buttons:
            self.keyboard.add(KeyboardButton(text=button))


    def get_keyboard(self, row: int = 1, is_one_time: bool = True) -> ReplyKeyboardMarkup:
        return self.keyboard.adjust(row).as_markup(
            resize_keyboard=True,
            input_field_place_holder='меню',
            one_time_keyboard=is_one_time
        )

class MainKb(ReplyBuilder):
    def __init__(self, spec_buttons):
        super().__init__()
        self.add_buttons(spec_buttons)
