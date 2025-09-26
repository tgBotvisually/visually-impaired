from aiogram import F, Router
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.filters import CommandStart

cmd_router = Router()


@cmd_router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(
        'Привет,этот бот помогает заполнять анкеты'
    )