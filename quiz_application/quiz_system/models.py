"""Data models for the Quiz Application."""

from dataclasses import dataclass, asdict, field
from typing import List


@dataclass
class Question:
    id: str
    category: str
    question: str
    options: List[str]
    answer_index: int          # index into `options` of the correct answer
    difficulty: str = "medium"

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(data: dict) -> "Question":
        options = list(data["options"])
        answer_index = int(data["answer_index"])
        if not (0 <= answer_index < len(options)):
            raise ValueError(f"answer_index out of range for question {data.get('id')}")
        return Question(
            id=str(data["id"]),
            category=str(data["category"]),
            question=str(data["question"]),
            options=options,
            answer_index=answer_index,
            difficulty=str(data.get("difficulty", "medium")),
        )

    @property
    def correct_answer(self) -> str:
        return self.options[self.answer_index]


@dataclass
class LeaderboardEntry:
    name: str
    category: str
    score: float
    correct: int
    wrong: int
    unanswered: int
    total_questions: int
    timestamp: str = field(default="")

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(data: dict) -> "LeaderboardEntry":
        return LeaderboardEntry(
            name=str(data["name"]),
            category=str(data["category"]),
            score=float(data["score"]),
            correct=int(data["correct"]),
            wrong=int(data["wrong"]),
            unanswered=int(data["unanswered"]),
            total_questions=int(data["total_questions"]),
            timestamp=str(data.get("timestamp", "")),
        )
