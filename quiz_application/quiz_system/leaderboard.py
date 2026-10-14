"""Leaderboard: record quiz results and rank them."""

from datetime import datetime
from typing import List, Optional

from .models import LeaderboardEntry
from .storage import Storage


class Leaderboard:
    def __init__(self, storage: Optional[Storage] = None):
        self.storage = storage or Storage()
        self.entries: List[LeaderboardEntry] = self.storage.load_leaderboard()

    def add_result(
        self,
        name: str,
        category: str,
        score: float,
        correct: int,
        wrong: int,
        unanswered: int,
        total_questions: int,
    ) -> LeaderboardEntry:
        entry = LeaderboardEntry(
            name=name.strip() or "Anonymous",
            category=category,
            score=round(score, 2),
            correct=correct,
            wrong=wrong,
            unanswered=unanswered,
            total_questions=total_questions,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )
        self.entries.append(entry)
        self.storage.save_leaderboard(self.entries)
        return entry

    def top(self, n: int = 10, category: Optional[str] = None) -> List[LeaderboardEntry]:
        pool = self.entries
        if category:
            pool = [e for e in pool if e.category.lower() == category.lower()]
        return sorted(pool, key=lambda e: e.score, reverse=True)[:n]
