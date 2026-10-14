"""Report generation: topper, average, pass/fail breakdown, grade distribution."""

from typing import List, Dict
from statistics import mean, median

from .models import Student
from .exceptions import InvalidInputError

PASS_MARK = 40.0


def _require_students(students: List[Student]) -> None:
    if not students:
        raise InvalidInputError("No student records available to generate a report.")


def topper(students: List[Student]) -> Student:
    _require_students(students)
    return max(students, key=lambda s: s.marks)


def lowest_scorer(students: List[Student]) -> Student:
    _require_students(students)
    return min(students, key=lambda s: s.marks)


def average_marks(students: List[Student]) -> float:
    _require_students(students)
    return round(mean(s.marks for s in students), 2)


def median_marks(students: List[Student]) -> float:
    _require_students(students)
    return round(median(s.marks for s in students), 2)


def pass_fail_counts(students: List[Student]) -> Dict[str, int]:
    _require_students(students)
    passed = sum(1 for s in students if s.marks >= PASS_MARK)
    failed = len(students) - passed
    return {"passed": passed, "failed": failed}


def grade(marks: float) -> str:
    if marks >= 90:
        return "A+"
    if marks >= 80:
        return "A"
    if marks >= 70:
        return "B"
    if marks >= 60:
        return "C"
    if marks >= PASS_MARK:
        return "D"
    return "F"


def grade_distribution(students: List[Student]) -> Dict[str, int]:
    _require_students(students)
    dist: Dict[str, int] = {}
    for s in students:
        g = grade(s.marks)
        dist[g] = dist.get(g, 0) + 1
    return dist


def full_report(students: List[Student]) -> str:
    """Build a human-readable multi-line report string."""
    _require_students(students)
    top = topper(students)
    low = lowest_scorer(students)
    avg = average_marks(students)
    med = median_marks(students)
    pf = pass_fail_counts(students)
    dist = grade_distribution(students)

    lines = [
        "=" * 40,
        " STUDENT PERFORMANCE REPORT",
        "=" * 40,
        f"Total students : {len(students)}",
        f"Average marks  : {avg}",
        f"Median marks   : {med}",
        f"Topper         : {top.name} ({top.student_id}) - {top.marks} marks",
        f"Lowest scorer  : {low.name} ({low.student_id}) - {low.marks} marks",
        f"Passed / Failed: {pf['passed']} / {pf['failed']} (pass mark = {PASS_MARK})",
        "Grade distribution:",
    ]
    for g in ["A+", "A", "B", "C", "D", "F"]:
        if g in dist:
            lines.append(f"  {g}: {dist[g]}")
    lines.append("=" * 40)
    return "\n".join(lines)
