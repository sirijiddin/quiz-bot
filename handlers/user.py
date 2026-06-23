from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext

from states import TakeTest
from database import get_all_questions

router = Router()


def build_keyboard(q_index: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="A", callback_data=f"ans:{q_index}:a"),
        InlineKeyboardButton(text="B", callback_data=f"ans:{q_index}:b"),
        InlineKeyboardButton(text="C", callback_data=f"ans:{q_index}:c"),
        InlineKeyboardButton(text="D", callback_data=f"ans:{q_index}:d"),
    ]])


def format_question(q: tuple, index: int, total: int) -> str:
    _, text, a, b, c, d, _ = q
    return (
        f"📝 Savol {index + 1}/{total}\n\n"
        f"{text}\n\n"
        f"A) {a}\n"
        f"B) {b}\n"
        f"C) {c}\n"
        f"D) {d}"
    )


@router.message(Command("myid"))
async def cmd_myid(message: Message):
    await message.answer(f"Sening ID'ing: `{message.from_user.id}`")


@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(
        "Salom! Test botga xush kelibsiz.\n\n"
        "/test — testni boshlash"
    )


@router.message(Command("test"))
async def cmd_test(message: Message, state: FSMContext):
    questions = get_all_questions()
    if not questions:
        await message.answer("Hozircha savollar yo'q. Admin qo'shishini kuting.")
        return

    await state.set_state(TakeTest.answering)
    await state.update_data(questions=questions, current=0, score=0)

    await message.answer(
        format_question(questions[0], 0, len(questions)),
        reply_markup=build_keyboard(0),
    )


@router.callback_query(TakeTest.answering, F.data.startswith("ans:"))
async def answer_handler(callback: CallbackQuery, state: FSMContext):
    _, q_index_str, user_answer = callback.data.split(":")
    q_index = int(q_index_str)

    data = await state.get_data()
    questions = data["questions"]
    current = data["current"]
    score = data["score"]

    if q_index != current:
        await callback.answer("Bu savol o'tib ketdi.", show_alert=True)
        return

    q = questions[current]
    _, text, a, b, c, d, correct = q
    options = {"a": a, "b": b, "c": c, "d": d}

    if user_answer == correct:
        score += 1
        result = (
            f"✅ To'g'ri! (+1 ball)\n"
            f"Javob: {correct.upper()}) {options[correct]}"
        )
    else:
        result = (
            f"❌ Noto'g'ri!\n"
            f"Sizning javob: {user_answer.upper()}) {options[user_answer]}\n"
            f"To'g'ri javob: {correct.upper()}) {options[correct]}"
        )

    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(result)
    await callback.answer()

    next_index = current + 1

    if next_index >= len(questions):
        total = len(questions)
        percentage = round(score / total * 100)
        await state.clear()
        await callback.message.answer(
            f"🏁 Test yakunlandi!\n\n"
            f"✅ To'g'ri: {score}/{total}\n"
            f"❌ Noto'g'ri: {total - score}/{total}\n"
            f"📊 Natija: {percentage}%"
        )
    else:
        await state.update_data(current=next_index, score=score)
        next_q = questions[next_index]
        await callback.message.answer(
            format_question(next_q, next_index, len(questions)),
            reply_markup=build_keyboard(next_index),
        )
