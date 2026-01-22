import logging
from aiogram import types
from aiogram.dispatcher import FSMContext
from bot import dp
from data import db
from bot.states import TestPassing
from bot.keyboards.inlineKeyboards import (
    get_categories_keyboard, get_tests_keyboard,
    get_answers_keyboard, get_test_results_keyboard,
    get_detailed_results_keyboard, get_main_menu_keyboard
)

logger = logging.getLogger(__name__)


# Выбор категории
@dp.callback_query_handler(lambda c: c.data == 'take_test', state='*')
async def choose_category(callback_query: types.CallbackQuery, state: FSMContext):
    """Выбор категории для теста"""
    await callback_query.answer()

    categories = db.Categories.getAllCategories()
    if not categories:
        await callback_query.message.edit_text(
            "❌ К сожалению, пока нет доступных категорий тестов.\n\n"
            "Попробуйте позже или обратитесь к администратору.",
            reply_markup=get_main_menu_keyboard()
        )
        return

    await callback_query.message.edit_text(
        "📂 Выберите категорию теста:",
        reply_markup=get_categories_keyboard(categories)
    )

    await TestPassing.choosing_category.set()


# Выбор категории из списка
@dp.callback_query_handler(lambda c: c.data.startswith('category_'), state=TestPassing.choosing_category)
async def select_category(callback_query: types.CallbackQuery, state: FSMContext):
    """Выбор конкретной категории"""
    await callback_query.answer()

    category_id = int(callback_query.data.split('_')[1])
    category = db.Categories.getCategoryById(category_id)

    if not category:
        await callback_query.message.edit_text(
            "❌ Категория не найдена.",
            reply_markup=get_main_menu_keyboard()
        )
        await state.finish()
        return

    # Сохраняем выбранную категорию
    await state.update_data(selected_category_id=category_id)

    # Получаем тесты в этой категории
    tests = db.Tests.getTestsByCategory(category_id)
    if not tests:
        await callback_query.message.edit_text(
            f"❌ В категории '{category['name']}' пока нет тестов.\n\n"
            "Выберите другую категорию:",
            reply_markup=get_categories_keyboard(db.Categories.getAllCategories())
        )
        return

    await callback_query.message.edit_text(
        f"📋 Тесты в категории '{category['name']}':\n\n"
        "Выберите тест для прохождения:",
        reply_markup=get_tests_keyboard(tests)
    )

    await TestPassing.choosing_test.set()


# Выбор теста
@dp.callback_query_handler(lambda c: c.data.startswith('test_'), state=TestPassing.choosing_test)
async def select_test(callback_query: types.CallbackQuery, state: FSMContext):
    """Выбор конкретного теста"""
    await callback_query.answer()

    test_id = int(callback_query.data.split('_')[1])
    test = db.Tests.getTestById(test_id)

    if not test:
        await callback_query.message.edit_text(
            "❌ Тест не найден.",
            reply_markup=get_main_menu_keyboard()
        )
        await state.finish()
        return

    # Получаем вопросы теста
    questions = db.Questions.getQuestionsByTest(test_id)
    if not questions:
        await callback_query.message.edit_text(
            f"❌ В тесте '{test['title']}' пока нет вопросов.\n\n"
            "Выберите другой тест:",
            reply_markup=get_tests_keyboard(db.Tests.getTestsByCategory(test['category_id']))
        )
        return

    # Сохраняем данные о тесте и начинаем прохождение
    await state.update_data(
        test_id=test_id,
        test_title=test['title'],
        questions=questions,
        current_question_index=0,
        answers_data=[],
        start_time=callback_query.message.date
    )

    # Показываем первый вопрос
    await show_question(callback_query.message, questions[0], state)


async def show_question(message: types.Message, question, state):
    """Показать вопрос пользователю"""
    answers = db.Answers.getAnswersByQuestion(question['id'])

    if not answers:
        await message.edit_text(
            "❌ У этого вопроса нет вариантов ответа.\n\n"
            "Обратитесь к администратору.",
            reply_markup=get_main_menu_keyboard()
        )
        await state.finish()
        return

    text = f"❓ Вопрос {question['question_order']}:\n\n" \
           f"{question['question_text']}"

    # Если есть изображение, добавляем его
    if question.get('image_path'):
        # Здесь можно добавить отправку изображения
        pass

    await message.edit_text(
        text,
        reply_markup=get_answers_keyboard(answers, question['id'])
    )

    await TestPassing.answering_question.set()


# Обработка ответа на вопрос
@dp.callback_query_handler(lambda c: c.data.startswith('answer_'), state=TestPassing.answering_question)
async def process_answer(callback_query: types.CallbackQuery, state: FSMContext):
    """Обработка ответа пользователя"""
    await callback_query.answer()

    # Парсим callback data: answer_{question_id}_{answer_id}
    parts = callback_query.data.split('_')
    question_id = int(parts[1])
    selected_answer_id = int(parts[2])

    # Получаем данные состояния
    state_data = await state.get_data()
    questions = state_data['questions']
    current_index = state_data['current_question_index']
    answers_data = state_data['answers_data']

    # Проверяем правильность ответа
    correct_answer = db.Answers.getCorrectAnswer(question_id)
    is_correct = correct_answer and correct_answer['id'] == selected_answer_id

    # Сохраняем ответ
    answers_data.append({
        'question_id': question_id,
        'selected_answer_id': selected_answer_id,
        'is_correct': is_correct
    })

    # Обновляем состояние
    await state.update_data(answers_data=answers_data)

    # Проверяем, есть ли следующий вопрос
    next_index = current_index + 1
    if next_index < len(questions):
        # Показываем следующий вопрос
        await state.update_data(current_question_index=next_index)
        await show_question(callback_query.message, questions[next_index], state)
    else:
        # Тест завершен, показываем результаты
        await show_test_results(callback_query, state)


async def show_test_results(callback_query: types.CallbackQuery, state: FSMContext):
    """Показать результаты теста"""
    state_data = await state.get_data()
    answers_data = state_data['answers_data']
    test_title = state_data['test_title']
    test_id = state_data['test_id']

    # Подсчитываем результаты
    correct_answers = sum(1 for answer in answers_data if answer['is_correct'])
    total_questions = len(answers_data)
    score = int((correct_answers / total_questions) * 100) if total_questions > 0 else 0

    # Сохраняем результаты в БД
    result_id = db.TestResults.saveResult(
        callback_query.from_user.id,
        test_id,
        score,
        total_questions,
        correct_answers
    )

    if result_id:
        db.TestResults.saveUserAnswers(result_id, answers_data)

        # Отправляем уведомление админам
        await notify_admins_about_test_completion(
            callback_query.from_user.id,
            test_title,
            score,
            correct_answers,
            total_questions
        )

    text = f"🎉 Тест '{test_title}' завершен!\n\n" \
           f"📊 Ваш результат:\n" \
           f"✅ Правильных ответов: {correct_answers}/{total_questions}\n" \
           f"📈 Процент правильности: {score}%\n\n" \
           "Что вы хотите сделать дальше?"

    await callback_query.message.edit_text(
        text,
        reply_markup=get_test_results_keyboard()
    )

    await TestPassing.showing_results.set()


async def notify_admins_about_test_completion(user_id, test_title, score, correct_answers, total_questions):
    """Отправить уведомление админам о завершении теста"""
    from bot import bot
    from data.config import logsGroupID

    user_info = db.Users.getUserFullInfo(user_id)
    user_name = f"{user_info['firstName']} {user_info['lastName']}" if user_info and user_info.get('firstName') else f"ID: {user_id}"

    text = f"🔔 Новый результат теста!\n\n" \
           f"👤 Пользователь: {user_name}\n" \
           f"📋 Тест: {test_title}\n" \
           f"📊 Результат: {score}% ({correct_answers}/{total_questions} правильных ответов)"

    try:
        if logsGroupID and logsGroupID != 0:
            await bot.send_message(logsGroupID, text)
    except Exception as e:
        logger.error(f"Failed to send admin notification: {e}")


# Просмотр детальных результатов
@dp.callback_query_handler(lambda c: c.data == 'view_detailed_results', state=TestPassing.showing_results)
async def view_detailed_results(callback_query: types.CallbackQuery, state: FSMContext):
    """Показать детальные результаты"""
    await callback_query.answer()

    state_data = await state.get_data()
    test_id = state_data['test_id']

    # Получаем последний результат пользователя
    results = db.TestResults.getUserResults(callback_query.from_user.id, limit=1)
    if not results:
        await callback_query.message.edit_text(
            "❌ Результаты не найдены.",
            reply_markup=get_main_menu_keyboard()
        )
        await state.finish()
        return

    result = results[0]
    detailed_answers = db.TestResults.getDetailedUserAnswers(result['id'])

    text = f"📊 Детальные результаты теста '{result['test_title']}'\n\n" \
           f"📈 Общий балл: {result['score']}%\n" \
           f"✅ Правильных ответов: {result['correct_answers']}/{result['total_questions']}\n\n" \
           "📝 Ваши ответы:\n\n"

    for i, answer in enumerate(detailed_answers, 1):
        status = "✅" if answer['is_correct'] else "❌"
        text += f"{i}. {status} {answer['question_text'][:50]}...\n"
        text += f"   Ваш ответ: {answer['selected_answer']}\n"
        text += f"   Правильный: {answer['correct_answer']}\n\n"

    await callback_query.message.edit_text(
        text,
        reply_markup=get_detailed_results_keyboard()
    )


# Повторное прохождение теста
@dp.callback_query_handler(lambda c: c.data == 'retake_test', state=TestPassing.showing_results)
async def retake_test(callback_query: types.CallbackQuery, state: FSMContext):
    """Повторное прохождение теста"""
    await callback_query.answer()

    state_data = await state.get_data()
    test_id = state_data['test_id']

    # Сбрасываем состояние и начинаем тест заново
    await state.update_data(
        current_question_index=0,
        answers_data=[],
        start_time=callback_query.message.date
    )

    test = db.Tests.getTestById(test_id)
    questions = db.Questions.getQuestionsByTest(test_id)

    if questions:
        await show_question(callback_query.message, questions[0], state)
    else:
        await callback_query.message.edit_text(
            "❌ Тест недоступен.",
            reply_markup=get_main_menu_keyboard()
        )
        await state.finish()


# Прохождение другого теста
@dp.callback_query_handler(lambda c: c.data == 'take_another_test', state='*')
async def take_another_test(callback_query: types.CallbackQuery, state: FSMContext):
    """Прохождение другого теста"""
    await callback_query.answer()

    categories = db.Categories.getAllCategories()
    if not categories:
        await callback_query.message.edit_text(
            "❌ К сожалению, пока нет доступных категорий тестов.",
            reply_markup=get_main_menu_keyboard()
        )
        return

    await callback_query.message.edit_text(
        "📂 Выберите категорию для нового теста:",
        reply_markup=get_categories_keyboard(categories)
    )

    await TestPassing.choosing_category.set()


# Возврат к категориям
@dp.callback_query_handler(lambda c: c.data == 'back_to_categories', state=TestPassing.choosing_test)
async def back_to_categories(callback_query: types.CallbackQuery, state: FSMContext):
    """Возврат к выбору категорий"""
    await callback_query.answer()

    categories = db.Categories.getAllCategories()
    await callback_query.message.edit_text(
        "📂 Выберите категорию теста:",
        reply_markup=get_categories_keyboard(categories)
    )

    await TestPassing.choosing_category.set()
