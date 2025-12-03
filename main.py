import streamlit as st
import json
import os
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime
import pandas as pd
from schemas import Test, QuestionType, TestResult
import random


# Конфигурация страницы
st.set_page_config(
    page_title="Подготовка к тестам",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Константы
EXAM_FOLDER = Path("exam")


# Функции для работы с тестами
def load_test_from_file(filepath: Path) -> Test:
    """Загрузить тест из JSON файла"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return Test(**data)
    except Exception as e:
        st.error(f"Ошибка загрузки теста {filepath.name}: {str(e)}")
        raise


def load_all_tests() -> Dict[str, Test]:
    """Загрузить все тесты из папки exam"""
    tests = {}
    
    if not EXAM_FOLDER.exists():
        EXAM_FOLDER.mkdir()
        st.warning(f"Папка {EXAM_FOLDER} создана. Добавьте туда JSON файлы с тестами.")
    
    json_files = list(EXAM_FOLDER.glob("*.json"))
    
    for filepath in json_files:
        try:
            test = load_test_from_file(filepath)
            tests[test.name] = test
        except Exception as e:
            st.error(f"Не удалось загрузить тест из {filepath.name}")
    
    return tests


def calculate_results(
    test: Test, 
    user_answers: Dict[int, List[int]]
) -> TestResult:
    """Рассчитать результаты теста"""
    score = 0
    max_score = len(test.questions)
    detailed_answers = []
    
    for i, question in enumerate(test.questions):
        user_answer = user_answers.get(i, [])
        is_correct = False
        
        if question.type == QuestionType.SINGLE:
            if len(user_answer) == 1:
                is_correct = user_answer[0] in question.correct_answers
        else:  # MULTIPLE
            if set(user_answer) == set(question.correct_answers):
                is_correct = True
        
        if is_correct:
            score += 1
        
        detailed_answers.append({
            "question_text": question.text,
            "question_type": question.type,
            "user_answer": user_answer,
            "correct_answer": question.correct_answers,
            "is_correct": is_correct,
            "explanation": question.explanation
        })
    
    percentage = (score / max_score) * 100 if max_score > 0 else 0
    passed = percentage >= test.passing_score
    
    return TestResult(
        test_name=test.name,
        score=score,
        max_score=max_score,
        percentage=percentage,
        passed=passed,
        answers=detailed_answers,
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )


def display_question(question, question_index: int, user_answers: Dict[int, List[int]]):
    """Отобразить вопрос и варианты ответов"""
    st.subheader(f"Вопрос {question_index + 1}")
    st.markdown(f"**{question.text}**")
    
    if question.type == QuestionType.SINGLE:
        st.caption("Выберите ОДИН правильный ответ")
    else:
        st.caption("Выберите ВСЕ правильные ответы")
    
    # Создаем ключ для текущего вопроса
    answer_key = f"q_{question_index}"
    
    # Инициализируем ответ, если его еще нет
    if answer_key not in st.session_state:
        st.session_state[answer_key] = []
    
    # Отображаем варианты ответов
    options = question.options
    
    if question.type == QuestionType.SINGLE:
        selected_option = st.radio(
            "Ваш ответ:",
            options=options,
            key=f"radio_{question_index}",
            index=None if not st.session_state[answer_key] else st.session_state[answer_key][0]
        )
        
        if selected_option:
            selected_index = options.index(selected_option)
            st.session_state[answer_key] = [selected_index]
            user_answers[question_index] = [selected_index]
    else:  # MULTIPLE
        selected_indices = []
        for i, option in enumerate(options):
            checkbox_key = f"check_{question_index}_{i}"
            
            # Инициализируем состояние чекбокса
            if checkbox_key not in st.session_state:
                st.session_state[checkbox_key] = False
            
            is_checked = st.checkbox(
                option,
                key=checkbox_key,
                value=st.session_state[checkbox_key]
            )
            
            if is_checked:
                selected_indices.append(i)
        
        st.session_state[answer_key] = selected_indices
        user_answers[question_index] = selected_indices
    
    return user_answers


def show_results(result: TestResult, test: Test):
    """Показать результаты теста"""
    st.balloons() if result.passed else st.snow()
    
    st.header("📊 Результаты теста")
    
    # Отображение основной статистики
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Правильных ответов", f"{result.score}/{result.max_score}")
    
    with col2:
        st.metric("Процент", f"{result.percentage:.1f}%")
    
    with col3:
        st.metric("Проходной балл", f"{test.passing_score}%")
    
    with col4:
        if result.passed:
            st.success("✅ Тест сдан!")
        else:
            st.error("❌ Тест не сдан")
    
    # Детализация по вопросам
    st.subheader("Детализация ответов")
    
    for i, answer_detail in enumerate(result.answers):
        with st.expander(f"Вопрос {i+1}: {answer_detail['question_text'][:100]}...", 
                        expanded=(i == 0)):
            col_a, col_b = st.columns(2)
            
            with col_a:
                st.write("**Ваш ответ:**")
                user_answer_indices = answer_detail['user_answer']
                if user_answer_indices:
                    user_answers_text = []
                    for idx in user_answer_indices:
                        user_answers_text.append(test.questions[i].options[idx])
                    st.write(", ".join(user_answers_text))
                else:
                    st.write("❌ Нет ответа")
            
            with col_b:
                st.write("**Правильный ответ:**")
                correct_answers_text = []
                for idx in test.questions[i].correct_answers:
                    correct_answers_text.append(test.questions[i].options[idx])
                st.write(", ".join(correct_answers_text))
            
            # Статус ответа
            if answer_detail['is_correct']:
                st.success("✅ Правильно")
            else:
                st.error("❌ Неправильно")
            
            # Пояснение к ответу, если есть
            if answer_detail.get('explanation'):
                st.info(f"💡 **Пояснение:** {answer_detail['explanation']}")
    
    # Кнопки действий
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        if st.button("🔄 Пройти тест еще раз", type="primary", use_container_width=True):
            st.session_state.test_started = False
            st.session_state.current_test = None
            st.session_state.current_question = 0
            st.session_state.user_answers = {}
            st.rerun()


# Инициализация состояния сессии
def init_session_state():
    """Инициализировать состояние сессии"""
    defaults = {
        'tests': {},
        'current_test': None,
        'test_started': False,
        'test_completed': False,
        'current_question': 0,
        'user_answers': {},
        'test_results': [],
        'shuffle_questions': False,
        'show_explanations': True
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


# Загрузка тестов
@st.cache_data
def load_tests_cached():
    """Кэшированная загрузка тестов"""
    return load_all_tests()


# Главная функция приложения
def main():
    init_session_state()
    
    # Заголовок приложения
    st.title("📚 Система подготовки к экзаменам")
    st.markdown("---")
    
    # Загрузка тестов
    st.session_state.tests = load_tests_cached()
    
    if not st.session_state.tests:
        st.warning("""
        Тесты не найдены в папке `/exam`. 
        
        **Пример формата файла теста (test_name.json):**
        ```json
        {
            "name": "Основы Python",
            "description": "Тест по основам программирования на Python",
            "passing_score": 70,
            "questions": [
                {
                    "text": "Какой тип данных является неизменяемым в Python?",
                    "type": "single",
                    "options": ["Список", "Словарь", "Кортеж", "Множество"],
                    "correct_answers": [2],
                    "explanation": "Кортеж (tuple) является неизменяемым типом данных"
                },
                {
                    "text": "Какие из перечисленных операторов используются для циклов?",
                    "type": "multiple",
                    "options": ["for", "while", "loop", "repeat"],
                    "correct_answers": [0, 1],
                    "explanation": "В Python используются операторы for и while"
                }
            ]
        }
        ```
        """)
        return
    
    # Боковая панель
    with st.sidebar:
        st.header("Навигация")
        
        if not st.session_state.test_started:
            menu = st.radio(
                "Выберите раздел:",
                ["🏠 Главная", "🧪 Пройти тест", "📈 История результатов"]
            )
        else:
            menu = "🧪 Пройти тест"
        
        st.markdown("---")
        
        if st.session_state.test_started:
            st.info("Тест в процессе")
            test = st.session_state.tests.get(st.session_state.current_test)
            if test:
                progress = (st.session_state.current_question) / len(test.questions)
                st.progress(progress)
                st.caption(f"Вопрос {st.session_state.current_question + 1} из {len(test.questions)}")
                
                if st.button("❌ Прервать тест"):
                    st.session_state.test_started = False
                    st.session_state.current_test = None
                    st.rerun()
        
        st.markdown("---")
        st.caption(f"Доступно тестов: {len(st.session_state.tests)}")
    
    # Главная страница
    if menu == "🏠 Главная" and not st.session_state.test_started:
        st.header("Добро пожаловать!")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("""
            ### О системе
            
            Эта система предназначена для подготовки к экзаменам и тестирования знаний.
            
            **Возможности:**
            - Прохождение тестов из папки `/exam`
            - Два типа вопросов: с одним и несколькими ответами
            - Детализированные результаты с пояснениями
            - История прохождения тестов
            
            **Как начать:**
            1. Перейдите в раздел "Пройти тест"
            2. Выберите тест из списка
            3. Ответьте на все вопросы
            4. Получите детализированный результат
            """)
        
        with col2:
            st.info("""
            **Формат файлов тестов:**
            - Файлы в формате JSON
            - Расположены в папке `/exam`
            - Поддерживают вопросы двух типов
            - Могут содержать пояснения
            """)
        
        # Список доступных тестов
        st.subheader("Доступные тесты")
        
        for test_name, test in st.session_state.tests.items():
            with st.expander(f"📘 {test_name}", expanded=False):
                st.write(f"**Описание:** {test.description}")
                st.write(f"**Количество вопросов:** {len(test.questions)}")
                st.write(f"**Проходной балл:** {test.passing_score}%")
                
                if test.time_limit:
                    st.write(f"**Ограничение по времени:** {test.time_limit} мин.")
    
    # Страница прохождения теста
    elif menu == "🧪 Пройти тест":
        if not st.session_state.test_started:
            # Выбор теста
            st.header("Выберите тест")
            
            test_names = list(st.session_state.tests.keys())
            selected_test = st.selectbox(
                "Доступные тесты:",
                test_names,
                format_func=lambda x: f"{x} ({len(st.session_state.tests[x].questions)} вопросов)"
            )
            
            if selected_test:
                test = st.session_state.tests[selected_test]
                
                st.subheader(f"Тест: {test.name}")
                st.write(test.description)
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Вопросов", len(test.questions))
                with col2:
                    st.metric("Проходной балл", f"{test.passing_score}%")
                with col3:
                    if test.time_limit:
                        st.metric("Время", f"{test.time_limit} мин")
                    else:
                        st.metric("Время", "Без ограничений")
                
                # Настройки теста
                st.subheader("Настройки теста")
                col1, col2 = st.columns(2)
                with col1:
                    shuffle = st.checkbox("Перемешать вопросы", value=False)
                with col2:
                    show_explanations = st.checkbox("Показывать пояснения", value=True)
                
                st.session_state.shuffle_questions = shuffle
                st.session_state.show_explanations = show_explanations
                
                if st.button("▶️ Начать тест", type="primary", use_container_width=True):
                    st.session_state.current_test = selected_test
                    st.session_state.test_started = True
                    st.session_state.current_question = 0
                    st.session_state.user_answers = {}
                    st.session_state.test_completed = False
                    
                    # Очистка состояний ответов
                    for key in list(st.session_state.keys()):
                        if key.startswith('q_') or key.startswith('radio_') or key.startswith('check_'):
                            del st.session_state[key]
                    
                    st.rerun()
        
        else:
            # Прохождение теста
            test = st.session_state.tests.get(st.session_state.current_test)
            
            if not test:
                st.error("Тест не найден")
                st.session_state.test_started = False
                st.rerun()
                return
            
            # Подготовка вопросов
            questions = test.questions.copy()
            if st.session_state.shuffle_questions:
                random.shuffle(questions)
            
            # Отображение текущего вопроса
            current_q = questions[st.session_state.current_question]
            
            # Отображение прогресса
            progress = st.session_state.current_question / len(questions)
            st.progress(progress)
            st.caption(f"Вопрос {st.session_state.current_question + 1} из {len(questions)}")
            
            # Отображение вопроса
            st.session_state.user_answers = display_question(
                current_q, 
                st.session_state.current_question,
                st.session_state.user_answers
            )
            
            # Навигация
            st.markdown("---")
            col1, col2, col3 = st.columns([1, 2, 1])
            
            with col1:
                if st.session_state.current_question > 0:
                    if st.button("← Назад", use_container_width=True):
                        st.session_state.current_question -= 1
                        st.rerun()
            
            with col2:
                if st.session_state.current_question < len(questions) - 1:
                    if st.button("Далее →", type="primary", use_container_width=True):
                        # Проверяем, ответил ли пользователь на текущий вопрос
                        current_key = f"q_{st.session_state.current_question}"
                        if current_key in st.session_state and st.session_state[current_key]:
                            st.session_state.current_question += 1
                            st.rerun()
                        else:
                            st.warning("Пожалуйста, выберите ответ перед переходом к следующему вопросу")
                else:
                    if st.button("Завершить тест ✅", type="primary", use_container_width=True):
                        # Проверяем, все ли вопросы отвечены
                        unanswered = []
                        for i in range(len(questions)):
                            if f"q_{i}" not in st.session_state or not st.session_state[f"q_{i}"]:
                                unanswered.append(i + 1)
                        
                        if unanswered:
                            st.warning(f"Не отвечены вопросы: {', '.join(map(str, unanswered))}")
                        else:
                            st.session_state.test_completed = True
                            st.rerun()
            
            with col3:
                if st.button("⏭️ Пропустить", use_container_width=True):
                    if st.session_state.current_question < len(questions) - 1:
                        st.session_state.current_question += 1
                        st.rerun()
    
    # Страница истории результатов
    elif menu == "📈 История результатов":
        st.header("История результатов")
        
        if not st.session_state.get('test_results'):
            st.info("Пока нет результатов тестов. Пройдите тест в разделе 'Пройти тест'.")
        else:
            # Отображение истории
            for result in st.session_state.test_results:
                with st.expander(f"📅 {result.timestamp} - {result.test_name}", expanded=False):
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Результат", f"{result.score}/{result.max_score}")
                    
                    with col2:
                        st.metric("Процент", f"{result.percentage:.1f}%")
                    
                    with col3:
                        if result.passed:
                            st.success("✅ Сдан")
                        else:
                            st.error("❌ Не сдан")
            
            # Общая статистика
            if st.session_state.test_results:
                st.subheader("Общая статистика")
                
                df = pd.DataFrame([
                    {
                        'Дата': r.timestamp,
                        'Тест': r.test_name,
                        'Результат': f"{r.score}/{r.max_score}",
                        'Процент': r.percentage,
                        'Статус': 'Сдан' if r.passed else 'Не сдан'
                    }
                    for r in st.session_state.test_results
                ])
                
                st.dataframe(df, use_container_width=True, hide_index=True)
    
    # Отображение результатов после завершения теста
    if st.session_state.test_completed and st.session_state.test_started:
        test = st.session_state.tests.get(st.session_state.current_test)
        
        if test:
            # Собираем все ответы
            final_answers = {}
            for i in range(len(test.questions)):
                key = f"q_{i}"
                if key in st.session_state:
                    final_answers[i] = st.session_state[key]
            
            # Рассчитываем результаты
            result = calculate_results(test, final_answers)
            
            # Сохраняем результат
            st.session_state.test_results.append(result)
            
            # Показываем результаты
            show_results(result, test)
            
            # Обновляем состояние
            st.session_state.test_completed = True
            st.session_state.test_started = False


if __name__ == "__main__":
    main()