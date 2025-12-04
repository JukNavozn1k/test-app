import streamlit as st
import json
from pathlib import Path
from datetime import datetime
import pandas as pd
from schemas import Test, QuestionType, TestResult
import random


# Конфигурация страницы
st.set_page_config(
    page_title="Подготовка к тестам",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="collapsed"
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


def load_all_tests() -> dict[str, Test]:
    """Загрузить все тесты из папки exam"""
    tests = {}
    
    if not EXAM_FOLDER.exists():
        EXAM_FOLDER.mkdir()
        # Создаем пример теста при первом запуске
        example_test = {
            "name": "Пример теста",
            "description": "Это пример теста для демонстрации работы приложения",
            "passing_score": 70,
            "questions": [
                {
                    "text": "Какой оператор используется для возведения в степень в Python?",
                    "type": "single",
                    "options": ["^", "**", "pow", "^^"],
                    "correct_answers": [1],
                    "explanation": "Оператор ** используется для возведения в степень в Python"
                },
                {
                    "text": "Какие из перечисленных типов являются встроенными в Python?",
                    "type": "multiple",
                    "options": ["list", "array", "dict", "tuple", "vector"],
                    "correct_answers": [0, 2, 3],
                    "explanation": "list, dict и tuple - встроенные типы. array и vector требуют импорта модулей"
                }
            ]
        }
        
        with open(EXAM_FOLDER / "example.json", "w", encoding="utf-8") as f:
            json.dump(example_test, f, ensure_ascii=False, indent=2)
        
        st.info(f"Создана папка {EXAM_FOLDER}. Добавлен пример теста.")
    
    json_files = list(EXAM_FOLDER.glob("*.json"))
    
    for filepath in json_files:
        try:
            test = load_test_from_file(filepath)
            tests[test.name] = test
        except Exception as e:
            st.warning(f"Не удалось загрузить тест из {filepath.name}: {str(e)}")
    
    return tests


def calculate_results(test: Test, user_answers: dict[int, list[int]]) -> TestResult:
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


def show_results(result: TestResult, test: Test):
    """Показать результаты теста"""
    # Показываем анимацию в зависимости от результата
    if result.passed:
        st.balloons()
    else:
        st.snow()
    
    st.header("📊 Результаты теста")
    
    # Отображение основной статистики
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Правильных ответов", f"{result.score}/{result.max_score}")
    
    with col2:
        st.metric("Процент", f"{result.percentage:.1f}%")
    
    with col3:
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
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Пройти еще раз", type="primary", use_container_width=True):
                # Полный сброс состояния
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()
        
        with col2:
            if st.button("📝 Выбрать другой тест", use_container_width=True):
                # Сброс состояния теста
                keys_to_delete = []
                for key in st.session_state.keys():
                    if key != 'tests':
                        keys_to_delete.append(key)
                
                for key in keys_to_delete:
                    del st.session_state[key]
                st.rerun()


# Главная функция приложения
def main():
    # Заголовок приложения
    st.title("📚 Система подготовки к экзаменам")
    
    # Инициализация состояния сессии
    if 'tests' not in st.session_state:
        st.session_state.tests = load_all_tests()
    
    if 'test_started' not in st.session_state:
        st.session_state.test_started = False
    
    if 'test_completed' not in st.session_state:
        st.session_state.test_completed = False
    
    if 'current_test' not in st.session_state:
        st.session_state.current_test = None
    
    if 'current_question' not in st.session_state:
        st.session_state.current_question = 0
    
    if 'user_answers' not in st.session_state:
        st.session_state.user_answers = {}
    
    if 'shuffled_indices' not in st.session_state:
        st.session_state.shuffled_indices = None
    
    # Навигация через табы
    if not st.session_state.test_started:
        tab1, tab2 = st.tabs(["🏠 Главная", "🧪 Пройти тест"])
    else:
        # Если тест начат, не показываем табы
        tab1, tab2 = None, None
    
    # Главная страница
    if not st.session_state.test_started:
        with tab1:
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
                - Поддержка перемешивания вопросов
                
                **Как начать:**
                1. Перейдите во вкладку "Пройти тест"
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
            st.subheader("📂 Доступные тесты")
            
            if not st.session_state.tests:
                st.warning("Нет доступных тестов. Проверьте папку `/exam`.")
            else:
                for test_name, test in st.session_state.tests.items():
                    with st.expander(f"📘 {test_name}", expanded=False):
                        st.write(f"**Описание:** {test.description}")
                        st.write(f"**Количество вопросов:** {len(test.questions)}")
                        st.write(f"**Проходной балл:** {test.passing_score}%")
                        
                        # Показываем количество вопросов с пояснениями
                        questions_with_explanation = sum(1 for q in test.questions if q.explanation)
                        if questions_with_explanation > 0:
                            st.write(f"**Вопросов с пояснениями:** {questions_with_explanation}")
    
    # Страница прохождения теста
    if not st.session_state.test_started and tab2:
        with tab2:
            st.header("Выберите тест")
            
            if not st.session_state.tests:
                st.warning("Нет доступных тестов. Добавьте JSON файлы в папку `/exam`.")
                return
            
            test_names = list(st.session_state.tests.keys())
            selected_test = st.selectbox(
                "Доступные тесты:",
                test_names,
                format_func=lambda x: f"{x} ({len(st.session_state.tests[x].questions)} вопросов)",
                key="test_selector"
            )
            
            if selected_test:
                test = st.session_state.tests[selected_test]
                
                st.subheader(f"Тест: {test.name}")
                st.write(test.description)
                
                # Статистика теста
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Вопросов", len(test.questions))
                with col2:
                    st.metric("Проходной балл", f"{test.passing_score}%")
                with col3:
                    questions_with_explanation = sum(1 for q in test.questions if q.explanation)
                    st.metric("С пояснениями", questions_with_explanation)
                
                # Настройки теста (только перемешивание)
                st.subheader("⚙️ Настройки теста")
                shuffle = st.checkbox("Перемешать вопросы", value=False, key="shuffle_checkbox")
                
                if st.button("▶️ Начать тест", type="primary", use_container_width=True):
                    # Инициализация теста
                    st.session_state.current_test = selected_test
                    st.session_state.test_started = True
                    st.session_state.test_completed = False
                    st.session_state.current_question = 0
                    st.session_state.user_answers = {}
                    
                    # Создаем shuffled_indices если нужно перемешивать
                    if shuffle:
                        indices = list(range(len(test.questions)))
                        random.shuffle(indices)
                        st.session_state.shuffled_indices = indices
                    else:
                        st.session_state.shuffled_indices = list(range(len(test.questions)))
                    
                    # Очистка старых состояний ответов
                    keys_to_delete = []
                    for key in st.session_state.keys():
                        if key.startswith('q_') or key.startswith('radio_') or key.startswith('check_'):
                            keys_to_delete.append(key)
                    
                    for key in keys_to_delete:
                        del st.session_state[key]
                    
                    st.rerun()
    
    # Прохождение теста (без табы)
    elif st.session_state.test_started and not st.session_state.test_completed:
        test = st.session_state.tests.get(st.session_state.current_test)
        
        if not test:
            st.error("Тест не найден")
            st.session_state.test_started = False
            st.rerun()
            return
        
        # Получаем текущий вопрос с учетом перемешивания
        current_original_index = st.session_state.shuffled_indices[st.session_state.current_question]
        current_q = test.questions[current_original_index]
        
        # Отображение прогресса
        progress = st.session_state.current_question / len(test.questions)
        st.progress(progress)
        
        col1, col2, col3 = st.columns([2, 3, 2])
        with col2:
            st.caption(f"Вопрос {st.session_state.current_question + 1} из {len(test.questions)}")
        
        # Отображение вопроса
        st.subheader(f"Вопрос {st.session_state.current_question + 1}")
        st.markdown(f"**{current_q.text}**")
        
        if current_q.type == QuestionType.SINGLE:
            st.caption("Выберите ОДИН правильный ответ")
        else:
            st.caption("Выберите ВСЕ правильные ответы")
        
        # Создаем ключ для текущего вопроса
        answer_key = f"q_{current_original_index}"
        
        # Инициализируем ответ, если его еще нет
        if answer_key not in st.session_state:
            st.session_state[answer_key] = []
        
        # Отображаем варианты ответов
        options = current_q.options
        
        if current_q.type == QuestionType.SINGLE:
            # Определяем индекс выбранного ответа, если он есть
            default_index = None
            if st.session_state[answer_key]:
                default_index = st.session_state[answer_key][0]
            
            selected_option = st.radio(
                "Ваш ответ:",
                options=options,
                key=f"radio_{current_original_index}",
                index=default_index
            )
            
            if selected_option:
                selected_index = options.index(selected_option)
                st.session_state[answer_key] = [selected_index]
                st.session_state.user_answers[current_original_index] = [selected_index]
            elif st.session_state[answer_key]:
                # Если ответ уже был выбран
                st.session_state.user_answers[current_original_index] = st.session_state[answer_key]
        else:  # MULTIPLE
            selected_indices = []
            for i, option in enumerate(options):
                checkbox_key = f"check_{current_original_index}_{i}"
                
                # Проверяем, был ли этот вариант уже выбран
                is_checked = i in st.session_state[answer_key]
                
                # Отображаем чекбокс с текущим состоянием
                if st.checkbox(option, key=checkbox_key, value=is_checked):
                    selected_indices.append(i)
            
            st.session_state[answer_key] = selected_indices
            st.session_state.user_answers[current_original_index] = selected_indices
        
        # Навигация
        st.markdown("---")
        col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
        
        with col1:
            if st.session_state.current_question > 0:
                if st.button("← Назад", use_container_width=True):
                    st.session_state.current_question -= 1
                    st.rerun()
        
        with col2:
            if st.button("🏠 Прервать", use_container_width=True):
                # Сброс состояния
                for key in list(st.session_state.keys()):
                    if key != 'tests':
                        del st.session_state[key]
                st.rerun()
        
        with col3:
            if st.session_state.current_question < len(test.questions) - 1:
                if st.button("Пропустить →", use_container_width=True):
                    st.session_state.current_question += 1
                    st.rerun()
        
        with col4:
            if st.session_state.current_question < len(test.questions) - 1:
                if st.button("Далее →", type="primary", use_container_width=True):
                    # Проверяем, ответил ли пользователь на текущий вопрос
                    if answer_key in st.session_state and st.session_state[answer_key]:
                        st.session_state.current_question += 1
                        st.rerun()
                    else:
                        st.warning("Пожалуйста, выберите ответ перед переходом к следующему вопросу")
            else:
                if st.button("Завершить тест ✅", type="primary", use_container_width=True):
                    # Проверяем, все ли вопросы отвечены
                    unanswered = []
                    for i in range(len(test.questions)):
                        key = f"q_{i}"
                        if key not in st.session_state or not st.session_state[key]:
                            unanswered.append(i + 1)
                    
                    if unanswered:
                        st.warning(f"Не отвечены вопросы: {', '.join(map(str, unanswered))}")
                    else:
                        st.session_state.test_completed = True
                        st.rerun()
    
    # Отображение результатов после завершения теста
    elif st.session_state.test_completed and st.session_state.test_started:
        test = st.session_state.tests.get(st.session_state.current_test)
        
        if test:
            # Рассчитываем результаты
            result = calculate_results(test, st.session_state.user_answers)
            
            # Показываем результаты
            show_results(result, test)


if __name__ == "__main__":
    main()