"""Console UI for the quiz: category selection, per-question countdown timer,
negative marking, and leaderboard display."""

import sys
import time
from typing import List, Optional

from .engine import QuizEngine, Scorer
from .leaderboard import Leaderboard
from .models import Question
from .exceptions import QuizError

DEFAULT_TIME_PER_QUESTION = 15  # seconds

try:
    import select
    _HAS_SELECT = hasattr(select, "select") and sys.platform != "win32"
except ImportError:
    _HAS_SELECT = False


def _input_with_timeout_posix(prompt: str, timeout: int) -> Optional[str]:
    """POSIX version: uses select() on stdin, so no thread is left dangling
    after a timeout — the next question's read starts on a clean stdin."""
    print(prompt, end="", flush=True)
    ready, _, _ = select.select([sys.stdin], [], [], timeout)
    if not ready:
        print("\n⏰ Time's up!")
        return None
    line = sys.stdin.readline()
    if line == "":  # EOF
        return None
    return line.rstrip("\n")


def _input_with_timeout_threaded(prompt: str, timeout: int) -> Optional[str]:
    """Fallback for platforms without select() on stdin (e.g. Windows).
    Note: if the timer runs out, the background thread stays blocked on
    input() until the user types something; that keystroke will simply be
    swallowed rather than double-counted for the next question."""
    import queue
    import threading

    result_q: "queue.Queue[Optional[str]]" = queue.Queue()

    def worker():
        try:
            result_q.put(input(prompt))
        except EOFError:
            result_q.put(None)

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()

    try:
        return result_q.get(timeout=timeout)
    except queue.Empty:
        print("\n⏰ Time's up!")
        return None


def _input_with_timeout(prompt: str, timeout: int) -> Optional[str]:
    """Read a line from stdin, giving up after `timeout` seconds.
    Returns None if the timer runs out before the user answers."""
    if _HAS_SELECT:
        return _input_with_timeout_posix(prompt, timeout)
    return _input_with_timeout_threaded(prompt, timeout)


def _ask_question(question: Question, index: int, total: int, time_limit: int) -> Optional[int]:
    print(f"\nQuestion {index + 1}/{total}  [{question.category}]  ({time_limit}s)")
    print(question.question)
    for i, opt in enumerate(question.options):
        print(f"  {i + 1}. {opt}")

    answer = _input_with_timeout(f"Your answer (1-{len(question.options)}, blank to skip): ", time_limit)
    if answer is None:
        return None
    answer = answer.strip()
    if not answer:
        return None
    try:
        choice = int(answer) - 1
    except ValueError:
        print("Not a valid option number — counted as unanswered.")
        return None
    if not (0 <= choice < len(question.options)):
        print("Out of range — counted as unanswered.")
        return None
    return choice


def run_quiz(
    engine: QuizEngine,
    leaderboard: Leaderboard,
    player_name: str,
    category: Optional[str],
    num_questions: int,
    time_limit: int = DEFAULT_TIME_PER_QUESTION,
) -> dict:
    questions = engine.select_questions(num_questions, category)
    responses: List[Optional[int]] = []

    start = time.time()
    for i, q in enumerate(questions):
        choice = _ask_question(q, i, len(questions), time_limit)
        responses.append(choice)
    elapsed = round(time.time() - start, 1)

    result = engine.grade(responses, questions)
    result["elapsed_seconds"] = elapsed

    leaderboard.add_result(
        name=player_name,
        category=category or "Mixed",
        score=result["score"],
        correct=result["correct"],
        wrong=result["wrong"],
        unanswered=result["unanswered"],
        total_questions=result["total_questions"],
    )
    return result


def print_result(result: dict, scorer: Scorer) -> None:
    print("\n" + "=" * 40)
    print(" QUIZ RESULT")
    print("=" * 40)
    print(f"Correct     : {result['correct']} (+{scorer.correct_marks} each)")
    print(f"Wrong       : {result['wrong']} ({scorer.wrong_marks} each)")
    print(f"Unanswered  : {result['unanswered']} ({scorer.unanswered_marks} each)")
    print(f"Total score : {result['score']} / {result['total_questions'] * scorer.correct_marks}")
    print(f"Time taken  : {result['elapsed_seconds']}s")
    print("=" * 40)


def print_leaderboard(entries) -> None:
    if not entries:
        print("Leaderboard is empty.")
        return
    print(f"\n{'Rank':<6}{'Name':<15}{'Category':<18}{'Score':<8}{'Correct':<9}{'Wrong':<7}")
    print("-" * 63)
    for rank, e in enumerate(entries, start=1):
        print(f"{rank:<6}{e.name:<15}{e.category:<18}{e.score:<8}{e.correct:<9}{e.wrong:<7}")


def main() -> None:
    storage_engine = QuizEngine()
    scorer = storage_engine.scorer
    board = Leaderboard(storage_engine.storage)

    print("=" * 40)
    print(" QUIZ APPLICATION (console mode)")
    print("=" * 40)
    print(f"Marking scheme: correct +{scorer.correct_marks}, wrong {scorer.wrong_marks}, "
          f"unanswered {scorer.unanswered_marks}\n")

    while True:
        print("\n1. Take a quiz\n2. View leaderboard\n0. Exit")
        choice = input("Select an option: ").strip()

        try:
            if choice == "1":
                cats = storage_engine.categories()
                print("Categories: " + ", ".join(cats) + " (or leave blank for mixed)")
                category = input("Category: ").strip() or None
                name = input("Your name: ").strip() or "Anonymous"
                count_in = input("Number of questions: ").strip()
                count = int(count_in) if count_in else 5
                time_in = input(f"Seconds per question [{DEFAULT_TIME_PER_QUESTION}]: ").strip()
                time_limit = int(time_in) if time_in else DEFAULT_TIME_PER_QUESTION

                result = run_quiz(storage_engine, board, name, category, count, time_limit)
                print_result(result, scorer)

            elif choice == "2":
                cat_filter = input("Filter by category (blank for all): ").strip() or None
                print_leaderboard(board.top(10, cat_filter))

            elif choice == "0":
                print("Goodbye.")
                break

            else:
                print("Invalid option, please choose again.")

        except QuizError as exc:
            print(f"Error: {exc}")
        except ValueError:
            print("Please enter a valid number.")
        except Exception as exc:
            print(f"Unexpected error: {exc}")


if __name__ == "__main__":
    main()
