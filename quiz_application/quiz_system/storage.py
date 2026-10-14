"""Persistence layer: load the question bank from JSON, load/save the leaderboard."""

import json
import os
from typing import List

from .models import Question, LeaderboardEntry
from .exceptions import QuestionBankError, StorageError

DATA_DIR = "data"
QUESTIONS_FILE = os.path.join(DATA_DIR, "questions.json")
LEADERBOARD_FILE = os.path.join(DATA_DIR, "leaderboard.json")

# A small seed bank so the app works out of the box.
_SAMPLE_QUESTIONS = [
    {
        "id": "q1", "category": "General Knowledge",
        "question": "What is the capital of France?",
        "options": ["Berlin", "Madrid", "Paris", "Rome"],
        "answer_index": 2, "difficulty": "easy",
    },
    {
        "id": "q2", "category": "General Knowledge",
        "question": "Which planet is known as the Red Planet?",
        "options": ["Venus", "Mars", "Jupiter", "Saturn"],
        "answer_index": 1, "difficulty": "easy",
    },
    {
        "id": "q3", "category": "General Knowledge",
        "question": "Who wrote 'Romeo and Juliet'?",
        "options": ["Charles Dickens", "Mark Twain", "William Shakespeare", "Leo Tolstoy"],
        "answer_index": 2, "difficulty": "medium",
    },
    {
        "id": "q4", "category": "Science",
        "question": "What gas do plants primarily absorb for photosynthesis?",
        "options": ["Oxygen", "Nitrogen", "Carbon Dioxide", "Hydrogen"],
        "answer_index": 2, "difficulty": "easy",
    },
    {
        "id": "q5", "category": "Science",
        "question": "What is the chemical symbol for gold?",
        "options": ["Go", "Gd", "Au", "Ag"],
        "answer_index": 2, "difficulty": "medium",
    },
    {
        "id": "q6", "category": "Science",
        "question": "How many bones are in the adult human body?",
        "options": ["186", "206", "226", "246"],
        "answer_index": 1, "difficulty": "hard",
    },
    {
        "id": "q7", "category": "Programming",
        "question": "Which keyword defines a function in Python?",
        "options": ["func", "def", "function", "lambda"],
        "answer_index": 1, "difficulty": "easy",
    },
    {
        "id": "q8", "category": "Programming",
        "question": "What data structure uses LIFO order?",
        "options": ["Queue", "Stack", "Array", "Linked List"],
        "answer_index": 1, "difficulty": "medium",
    },
    {
        "id": "q9", "category": "Programming",
        "question": "What does 'JSON' stand for?",
        "options": [
            "JavaScript Object Notation", "Java Standard Object Notation",
            "JavaScript Oriented Network", "Joined Syntax Object Notation",
        ],
        "answer_index": 0, "difficulty": "medium",
    },
    {
        "id": "q10", "category": "Programming",
        "question": "Which of these is NOT a Python built-in data type?",
        "options": ["list", "dict", "tuple", "array"],
        "answer_index": 3, "difficulty": "hard",
    },
    {
        "id": "q11", "category": "History",
        "question": "In which year did World War II end?",
        "options": ["1943", "1945", "1947", "1950"],
        "answer_index": 1, "difficulty": "easy",
    },
    {
        "id": "q12", "category": "History",
        "question": "Who was the first President of the United States?",
        "options": ["Thomas Jefferson", "Abraham Lincoln", "George Washington", "John Adams"],
        "answer_index": 2, "difficulty": "easy",
    },
]


class Storage:
    def __init__(self, data_dir: str = DATA_DIR):
        self.data_dir = data_dir
        self.questions_path = os.path.join(data_dir, "questions.json")
        self.leaderboard_path = os.path.join(data_dir, "leaderboard.json")
        os.makedirs(self.data_dir, exist_ok=True)

        if not os.path.exists(self.questions_path):
            self._write_json(self.questions_path, _SAMPLE_QUESTIONS)
        if not os.path.exists(self.leaderboard_path):
            self._write_json(self.leaderboard_path, [])

    @staticmethod
    def _write_json(path: str, records: list) -> None:
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(records, f, indent=2)
        except OSError as exc:
            raise StorageError(f"Could not write to {path}: {exc}") from exc

    @staticmethod
    def _read_json(path: str) -> list:
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            return []
        except json.JSONDecodeError as exc:
            raise StorageError(f"Data file is corrupted: {path}: {exc}") from exc
        except OSError as exc:
            raise StorageError(f"Could not read {path}: {exc}") from exc

    # ---------- questions ----------
    def load_questions(self) -> List[Question]:
        raw = self._read_json(self.questions_path)
        if not raw:
            raise QuestionBankError("The question bank is empty.")
        questions = []
        for item in raw:
            try:
                questions.append(Question.from_dict(item))
            except (KeyError, ValueError, TypeError) as exc:
                # Skip malformed entries rather than crashing the app
                continue
        if not questions:
            raise QuestionBankError("No valid questions could be loaded.")
        return questions

    # ---------- leaderboard ----------
    def load_leaderboard(self) -> List[LeaderboardEntry]:
        raw = self._read_json(self.leaderboard_path)
        entries = []
        for item in raw:
            try:
                entries.append(LeaderboardEntry.from_dict(item))
            except (KeyError, ValueError, TypeError):
                continue
        return entries

    def save_leaderboard(self, entries: List[LeaderboardEntry]) -> None:
        self._write_json(self.leaderboard_path, [e.to_dict() for e in entries])
