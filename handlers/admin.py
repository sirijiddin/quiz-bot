from io import BytesIO

import openpyxl
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from states import AddQuestion, UploadQuestions
from database import add_question, get_question_count, get_all_questions, get_questions_page, delete_question, clear_all_questions
from config import ADMIN_IDS

router = Router()


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


@router.message(Command("add_question"))
async def cmd_add_question(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.set_state(AddQuestion.question)
    await message.answer("📝 Savol matnini yozing:")


@router.message(AddQuestion.question)
async def add_q_question(message: Message, state: FSMContext):
    await state.update_data(question=message.text)
    await state.set_state(AddQuestion.option_a)
    await message.answer("A) variant:")


@router.message(AddQuestion.option_a)
async def add_q_a(message: Message, state: FSMContext):
    await state.update_data(option_a=message.text)
    await state.set_state(AddQuestion.option_b)
    await message.answer("B) variant:")


@router.message(AddQuestion.option_b)
async def add_q_b(message: Message, state: FSMContext):
    await state.update_data(option_b=message.text)
    await state.set_state(AddQuestion.option_c)
    await message.answer("C) variant:")


@router.message(AddQuestion.option_c)
async def add_q_c(message: Message, state: FSMContext):
    await state.update_data(option_c=message.text)
    await state.set_state(AddQuestion.option_d)
    await message.answer("D) variant:")


@router.message(AddQuestion.option_d)
async def add_q_d(message: Message, state: FSMContext):
    await state.update_data(option_d=message.text)
    await state.set_state(AddQuestion.correct)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="A", callback_data="correct:a"),
        InlineKeyboardButton(text="B", callback_data="correct:b"),
        InlineKeyboardButton(text="C", callback_data="correct:c"),
        InlineKeyboardButton(text="D", callback_data="correct:d"),
    ]])
    await message.answer("To'g'ri javob qaysi?", reply_markup=keyboard)


@router.callback_query(AddQuestion.correct, F.data.startswith("correct:"))
async def add_q_correct(callback: CallbackQuery, state: FSMContext):
    correct = callback.data.split(":")[1]
    data = await state.get_data()
    add_question(
        data["question"],
        data["option_a"],
        data["option_b"],
        data["option_c"],
        data["option_d"],
        correct,
    )
    await state.clear()
    count = get_question_count()
    await callback.message.edit_text(f"✅ Savol qo'shildi! Jami: {count} ta savol.")
    await callback.answer()


@router.message(Command("upload_questions"))
async def cmd_upload_questions(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.set_state(UploadQuestions.waiting_file)
    await message.answer(
        "📂 Excel (.xlsx) faylini yuboring.\n\n"
        "Fayl formati (sarlavhasiz):\n"
        "A — Savol matni\n"
        "B — A variant\n"
        "C — B variant\n"
        "D — C variant\n"
        "E — D variant\n"
        "F — To'g'ri javob (a / b / c / d)"
    )


@router.message(UploadQuestions.waiting_file, F.document)
async def handle_excel_upload(message: Message, state: FSMContext):
    file_name = message.document.file_name or ""
    if not file_name.endswith(".xlsx"):
        await message.answer("Faqat .xlsx fayl qabul qilinadi.")
        return

    await message.answer("⏳ Fayl o'qilmoqda...")

    file_bytes = BytesIO()
    await message.bot.download(message.document, destination=file_bytes)
    file_bytes.seek(0)

    wb = openpyxl.load_workbook(file_bytes)
    ws = wb.active

    added = 0
    skipped = 0

    for row in ws.iter_rows(values_only=True):
        if len(row) < 6:
            skipped += 1
            continue
        question, a, b, c, d, correct = row[:6]
        if not all([question, a, b, c, d, correct]):
            skipped += 1
            continue
        correct_str = str(correct).strip().lower()
        if correct_str not in ("a", "b", "c", "d"):
            skipped += 1
            continue
        add_question(str(question), str(a), str(b), str(c), str(d), correct_str)
        added += 1

    await state.clear()
    total = get_question_count()
    await message.answer(
        f"✅ {added} ta savol qo'shildi.\n"
        f"⚠️ {skipped} ta qator o'tkazib yuborildi.\n"
        f"📊 Jami savollar: {total} ta"
    )


@router.message(UploadQuestions.waiting_file)
async def handle_not_document(message: Message):
    await message.answer("Iltimos, .xlsx faylini yuboring.")


PAGE_SIZE = 20


def build_questions_text(page: int) -> tuple[str, InlineKeyboardMarkup | None]:
    total = get_question_count()
    if total == 0:
        return "Hozircha savollar yo'q.", None

    offset = page * PAGE_SIZE
    questions = get_questions_page(offset, PAGE_SIZE)
    total_pages = (total + PAGE_SIZE - 1) // PAGE_SIZE

    lines = [f"📋 Savollar ({page + 1}/{total_pages} sahifa, jami: {total}):\n"]
    for q in questions:
        id_, text, *_, correct = q
        short = text[:40] + ("..." if len(text) > 40 else "")
        lines.append(f"#{id_} {short} | ✅{correct.upper()}")

    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(text="⬅️ Oldingi", callback_data=f"qpage:{page - 1}"))
    if page < total_pages - 1:
        nav_buttons.append(InlineKeyboardButton(text="Keyingi ➡️", callback_data=f"qpage:{page + 1}"))

    keyboard = InlineKeyboardMarkup(inline_keyboard=[nav_buttons]) if nav_buttons else None
    return "\n".join(lines), keyboard


@router.message(Command("questions"))
async def cmd_questions(message: Message):
    if not is_admin(message.from_user.id):
        return
    text, keyboard = build_questions_text(0)
    await message.answer(text, reply_markup=keyboard)


@router.callback_query(F.data.startswith("qpage:"))
async def questions_page(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer()
        return
    page = int(callback.data.split(":")[1])
    text, keyboard = build_questions_text(page)
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.message(Command("clear_questions"))
async def cmd_clear_questions(message: Message):
    if not is_admin(message.from_user.id):
        return
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Ha, o'chir", callback_data="confirm_clear"),
        InlineKeyboardButton(text="❌ Yo'q", callback_data="cancel_clear"),
    ]])
    await message.answer("Barcha savollar o'chirilsinmi?", reply_markup=keyboard)


@router.callback_query(F.data == "confirm_clear")
async def confirm_clear(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    clear_all_questions()
    await callback.message.edit_text("✅ Barcha savollar o'chirildi.")
    await callback.answer()


@router.callback_query(F.data == "cancel_clear")
async def cancel_clear(callback: CallbackQuery):
    await callback.message.edit_text("Bekor qilindi.")
    await callback.answer()


@router.message(Command("delete_question"))
async def cmd_delete_question(message: Message):
    if not is_admin(message.from_user.id):
        return
    parts = message.text.split()
    if len(parts) != 2 or not parts[1].isdigit():
        await message.answer("Ishlatish: /delete_question <id>")
        return
    delete_question(int(parts[1]))
    await message.answer(f"Savol #{parts[1]} o'chirildi.")
