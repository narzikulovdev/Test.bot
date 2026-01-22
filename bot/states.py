from aiogram.dispatcher.filters.state import State, StatesGroup


class UserRegistration(StatesGroup):
    """States для регистрации пользователя"""
    waiting_for_first_name = State()
    waiting_for_last_name = State()
    waiting_for_middle_name = State()
    waiting_for_phone = State()


class TestPassing(StatesGroup):
    """States для прохождения тестов"""
    choosing_category = State()
    choosing_test = State()
    answering_question = State()
    showing_results = State()


class AdminPanel(StatesGroup):
    """States для админ-панели"""
    main_menu = State()

    # Управление категориями
    adding_category_name = State()
    adding_category_description = State()

    # Управление тестами
    choosing_category_for_test = State()
    adding_test_title = State()
    adding_test_description = State()

    # Управление вопросами
    choosing_test_for_question = State()
    adding_question_text = State()
    adding_question_image = State()

    # Управление ответами
    choosing_question_for_answer = State()
    adding_answer_text = State()
    marking_correct_answer = State()

    # Рассылка
    writing_broadcast_message = State()

    # Блокировка пользователей
    entering_user_phone_for_block = State()

    # Статистика
    viewing_stats = State()

