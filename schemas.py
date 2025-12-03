from pydantic import BaseModel, Field, validator
from typing import List, Literal, Optional
from enum import Enum


class QuestionType(str, Enum):
    SINGLE = "single"
    MULTIPLE = "multiple"


class Question(BaseModel):
    text: str = Field(..., description="Текст вопроса")
    type: QuestionType = Field(..., description="Тип вопроса: single или multiple")
    options: List[str] = Field(..., min_items=2, description="Варианты ответов")
    correct_answers: List[int] = Field(
        ..., 
        description="Индексы правильных ответов (начиная с 0)"
    )
    explanation: Optional[str] = Field(None, description="Пояснение к ответу")

    @validator('correct_answers')
    def validate_correct_answers(cls, v, values):
        if 'options' in values:
            if not v:
                raise ValueError('Должен быть хотя бы один правильный ответ')
            
            max_index = len(values['options']) - 1
            for idx in v:
                if idx < 0 or idx > max_index:
                    raise ValueError(f'Индекс {idx} выходит за пределы вариантов ответов')
            
            if values.get('type') == QuestionType.SINGLE and len(v) != 1:
                raise ValueError('Для типа "single" должен быть ровно один правильный ответ')
        
        return v


class Test(BaseModel):
    name: str = Field(..., description="Название теста")
    description: str = Field(..., description="Описание теста")
    questions: List[Question] = Field(..., min_items=1, description="Список вопросов")
    time_limit: Optional[int] = Field(None, description="Ограничение по времени в минутах")
    passing_score: int = Field(80, ge=0, le=100, description="Проходной балл в процентах")


class TestResult(BaseModel):
    test_name: str
    score: int
    max_score: int
    percentage: float
    passed: bool
    answers: List[dict]
    timestamp: str