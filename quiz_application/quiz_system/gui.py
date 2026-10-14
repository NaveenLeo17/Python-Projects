"""Optional Tkinter GUI for the Quiz Application.

Run with:  python main.py --gui
(falls back to the console UI if Tkinter isn't available on this system)
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Optional

from .engine import QuizEngine, Scorer
from .leaderboard import Leaderboard
from .models import Question
from .exceptions import QuizError

DEFAULT_TIME_PER_QUESTION = 15


class QuizGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Quiz Application")
        self.geometry("560x420")
        self.resizable(False, False)

        self.engine = QuizEngine()
        self.scorer: Scorer = self.engine.scorer
        self.board = Leaderboard(self.engine.storage)

        # quiz-in-progress state
        self.questions: List[Question] = []
        self.responses: List[Optional[int]] = []
        self.current_index = 0
        self.time_left = DEFAULT_TIME_PER_QUESTION
        self.time_limit = DEFAULT_TIME_PER_QUESTION
        self.timer_job = None
        self.player_name = "Anonymous"
        self.category: Optional[str] = None
        self.selected_option = tk.IntVar(value=-1)

        self.container = ttk.Frame(self, padding=20)
        self.container.pack(fill="both", expand=True)

        self._build_start_screen()

    # ---------- screen management ----------
    def _clear(self) -> None:
        for widget in self.container.winfo_children():
            widget.destroy()

    # ---------- start screen ----------
    def _build_start_screen(self) -> None:
        self._clear()
        ttk.Label(self.container, text="Quiz Application", font=("Helvetica", 18, "bold")).pack(pady=(0, 15))

        form = ttk.Frame(self.container)
        form.pack(fill="x")

        ttk.Label(form, text="Your name:").grid(row=0, column=0, sticky="w", pady=5)
        self.name_entry = ttk.Entry(form)
        self.name_entry.grid(row=0, column=1, sticky="ew", pady=5)

        ttk.Label(form, text="Category:").grid(row=1, column=0, sticky="w", pady=5)
        categories = ["Mixed"] + self.engine.categories()
        self.category_combo = ttk.Combobox(form, values=categories, state="readonly")
        self.category_combo.current(0)
        self.category_combo.grid(row=1, column=1, sticky="ew", pady=5)

        ttk.Label(form, text="Number of questions:").grid(row=2, column=0, sticky="w", pady=5)
        self.count_entry = ttk.Entry(form)
        self.count_entry.insert(0, "5")
        self.count_entry.grid(row=2, column=1, sticky="ew", pady=5)

        ttk.Label(form, text="Seconds per question:").grid(row=3, column=0, sticky="w", pady=5)
        self.time_entry = ttk.Entry(form)
        self.time_entry.insert(0, str(DEFAULT_TIME_PER_QUESTION))
        self.time_entry.grid(row=3, column=1, sticky="ew", pady=5)

        form.columnconfigure(1, weight=1)

        ttk.Label(
            self.container,
            text=f"Marking: correct +{self.scorer.correct_marks}, "
                 f"wrong {self.scorer.wrong_marks}, unanswered {self.scorer.unanswered_marks}",
            foreground="gray",
        ).pack(pady=(15, 5))

        btns = ttk.Frame(self.container)
        btns.pack(pady=15)
        ttk.Button(btns, text="Start Quiz", command=self._start_quiz).pack(side="left", padx=5)
        ttk.Button(btns, text="View Leaderboard", command=self._build_leaderboard_screen).pack(side="left", padx=5)

    def _start_quiz(self) -> None:
        self.player_name = self.name_entry.get().strip() or "Anonymous"
        cat_choice = self.category_combo.get()
        self.category = None if cat_choice == "Mixed" else cat_choice

        try:
            count = int(self.count_entry.get().strip())
            self.time_limit = int(self.time_entry.get().strip())
            self.questions = self.engine.select_questions(count, self.category)
        except ValueError:
            messagebox.showerror("Invalid input", "Number of questions and time must be whole numbers.")
            return
        except QuizError as exc:
            messagebox.showerror("Cannot start quiz", str(exc))
            return

        self.responses = [None] * len(self.questions)
        self.current_index = 0
        self._build_question_screen()

    # ---------- question screen ----------
    def _build_question_screen(self) -> None:
        self._clear()
        self._cancel_timer()

        question = self.questions[self.current_index]
        self.selected_option.set(-1)

        header = ttk.Frame(self.container)
        header.pack(fill="x")
        ttk.Label(
            header,
            text=f"Question {self.current_index + 1}/{len(self.questions)}  [{question.category}]",
            font=("Helvetica", 12, "bold"),
        ).pack(side="left")
        self.timer_label = ttk.Label(header, text="", font=("Helvetica", 12, "bold"), foreground="red")
        self.timer_label.pack(side="right")

        ttk.Label(
            self.container, text=question.question, wraplength=500, font=("Helvetica", 13)
        ).pack(pady=(15, 10), anchor="w")

        for i, option in enumerate(question.options):
            ttk.Radiobutton(
                self.container, text=option, value=i, variable=self.selected_option
            ).pack(anchor="w", pady=3)

        btns = ttk.Frame(self.container)
        btns.pack(pady=20)
        is_last = self.current_index == len(self.questions) - 1
        ttk.Button(
            btns, text="Finish" if is_last else "Next",
            command=self._submit_current_answer,
        ).pack(side="left", padx=5)
        ttk.Button(btns, text="Skip", command=lambda: self._submit_current_answer(skip=True)).pack(side="left", padx=5)

        self.time_left = self.time_limit
        self._tick_timer()

    def _tick_timer(self) -> None:
        self.timer_label.config(text=f"⏱ {self.time_left}s")
        if self.time_left <= 0:
            self._submit_current_answer(timed_out=True)
            return
        self.time_left -= 1
        self.timer_job = self.after(1000, self._tick_timer)

    def _cancel_timer(self) -> None:
        if self.timer_job is not None:
            self.after_cancel(self.timer_job)
            self.timer_job = None

    def _submit_current_answer(self, skip: bool = False, timed_out: bool = False) -> None:
        self._cancel_timer()
        choice = self.selected_option.get()
        self.responses[self.current_index] = None if (skip or timed_out or choice < 0) else choice

        if self.current_index + 1 < len(self.questions):
            self.current_index += 1
            self._build_question_screen()
        else:
            self._finish_quiz()

    # ---------- result screen ----------
    def _finish_quiz(self) -> None:
        self._cancel_timer()
        result = self.engine.grade(self.responses, self.questions)
        self.board.add_result(
            name=self.player_name,
            category=self.category or "Mixed",
            score=result["score"],
            correct=result["correct"],
            wrong=result["wrong"],
            unanswered=result["unanswered"],
            total_questions=result["total_questions"],
        )
        self._build_result_screen(result)

    def _build_result_screen(self, result: dict) -> None:
        self._clear()
        ttk.Label(self.container, text="Quiz Complete!", font=("Helvetica", 18, "bold")).pack(pady=(0, 15))

        max_score = result["total_questions"] * self.scorer.correct_marks
        lines = [
            f"Player       : {self.player_name}",
            f"Category     : {self.category or 'Mixed'}",
            f"Correct      : {result['correct']}",
            f"Wrong        : {result['wrong']}",
            f"Unanswered   : {result['unanswered']}",
            f"Final score  : {result['score']} / {max_score}",
        ]
        for line in lines:
            ttk.Label(self.container, text=line, font=("Helvetica", 12)).pack(anchor="w", pady=2)

        btns = ttk.Frame(self.container)
        btns.pack(pady=20)
        ttk.Button(btns, text="Play Again", command=self._build_start_screen).pack(side="left", padx=5)
        ttk.Button(btns, text="View Leaderboard", command=self._build_leaderboard_screen).pack(side="left", padx=5)

    # ---------- leaderboard screen ----------
    def _build_leaderboard_screen(self) -> None:
        self._clear()
        ttk.Label(self.container, text="Leaderboard", font=("Helvetica", 18, "bold")).pack(pady=(0, 15))

        columns = ("rank", "name", "category", "score", "correct", "wrong")
        tree = ttk.Treeview(self.container, columns=columns, show="headings", height=10)
        headers = {"rank": "#", "name": "Name", "category": "Category", "score": "Score",
                   "correct": "Correct", "wrong": "Wrong"}
        widths = {"rank": 30, "name": 100, "category": 130, "score": 60, "correct": 60, "wrong": 60}
        for col in columns:
            tree.heading(col, text=headers[col])
            tree.column(col, width=widths[col], anchor="center")
        tree.pack(fill="both", expand=True)

        for rank, entry in enumerate(self.board.top(10), start=1):
            tree.insert("", "end", values=(rank, entry.name, entry.category, entry.score, entry.correct, entry.wrong))

        ttk.Button(self.container, text="Back", command=self._build_start_screen).pack(pady=15)


def main() -> None:
    app = QuizGUI()
    app.mainloop()


if __name__ == "__main__":
    main()
