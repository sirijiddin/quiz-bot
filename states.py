from aiogram.fsm.state import State, StatesGroup


class AddQuestion(StatesGroup):
    question = State()
    option_a = State()
    option_b = State()
    option_c = State()
    option_d = State()
    correct = State()


class TakeTest(StatesGroup):
    answering = State()


class UploadQuestions(StatesGroup):
    waiting_file = State()
