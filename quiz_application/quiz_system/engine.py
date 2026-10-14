"""Core quiz logic: random question selection (optionally by category)
and a scorer that supports negative marking."""

import random
from typing import List, Optional

from .models import Question
from .storage import Storage
from .exceptions import NotEnoughQuestionsError, InvalidInputError


class Scorer:
    """Encapsulates the marking scheme so it's easy to tune or swap out."""

    def __init__(self, correct_marks: float = 4.0, wrong_marks: float = -1.0, unanswered_marks: float = 0.0):
        self.correct_marks = correct_marks
        self.wrong_marks = wrong_marks
        self.unanswered_marks = unanswered_marks

    def score_for(self, is_correct: Optional[bool]) -> float:
        """is_correct: True / False / None (unanswered)."""
        if is_correct is None:
            return self.unanswered_marks
        return self.correct_marks if is_correct else self.wrong_marks


class QuizEngine:
    def __init__(self, storage: Optional[Storage] = None, scorer: Optional[Scorer] = None):
        self.storage = storage or Storage()
        self.scorer = scorer or Scorer()
        self.questions: List[Question] = self.storage.load_questions()

    def categories(self) -> List[str]:
        return sorted({q.category for q in self.questions})

    def select_questions(self, count: int, category: Optional[str] = None) -> List[Question]:
        pool = self.questions
        if category:
            pool = [q for q in pool if q.category.lower() == category.lower()]
            if not pool:
                raise InvalidInputError(f"No questions found in category '{category}'.")

        if count <= 0:
            raise InvalidInputError("Number of questions must be greater than zero.")
        if count > len(pool):
            raise NotEnoughQuestionsError(
                f"Requested {count} questions but only {len(pool)} available."
            )

        return random.sample(pool, count)

    def grade(self, responses: List[Optional[int]], questions: List[Question]) -> dict:
        """responses[i] is the chosen option index for questions[i], or None if unanswered."""
        if len(responses) != len(questions):
            raise InvalidInputError("Responses and questions must be the same length.")

        correct = wrong = unanswered = 0
        total_score = 0.0

        for response, question in zip(responses, questions):
            if response is None:
                unanswered += 1
                total_score += self.scorer.score_for(None)
                continue
            is_correct = response == question.answer_index
            if is_correct:
                correct += 1
            else:
                wrong += 1
            total_score += self.scorer.score_for(is_correct)

        return {
            "correct": correct,
            "wrong": wrong,
            "unanswered": unanswered,
            "total_questions": len(questions),
            "score": round(total_score, 2),
        }
