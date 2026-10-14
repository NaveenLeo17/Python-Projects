"""
Student Management System
--------------------------
A console-based CRUD app with admin login, JSON/CSV storage,
sorting, searching, and report generation.

Run with:  python main.py
"""

from student_management.manager import StudentManager
from student_management.storage import Storage
from student_management import reports, auth
from student_management.exceptions import (
    StudentManagementError,
    AuthenticationError,
)

MENU = """
==============================
 STUDENT MANAGEMENT SYSTEM
==============================
1. Add student
2. Update student
3. Delete student
4. View all students
5. Search student
6. Sort by name
7. Sort by marks
8. Generate report
9. Export to CSV
10. Change admin password
0. Exit
==============================
"""


def print_students(students) -> None:
    if not students:
        print("No records found.")
        return
    print(f"{'ID':<8}{'Name':<20}{'Age':<5}{'Course':<15}{'Marks':<6}")
    print("-" * 54)
    for s in students:
        print(f"{s.student_id:<8}{s.name:<20}{s.age:<5}{s.course:<15}{s.marks:<6}")


def prompt_student_fields(existing=None):
    name = input(f"Name [{existing.name if existing else ''}]: ").strip() or (
        existing.name if existing else ""
    )
    age = input(f"Age [{existing.age if existing else ''}]: ").strip() or (
        existing.age if existing else ""
    )
    course = input(f"Course [{existing.course if existing else ''}]: ").strip() or (
        existing.course if existing else ""
    )
    marks = input(f"Marks [{existing.marks if existing else ''}]: ").strip() or (
        existing.marks if existing else ""
    )
    return name, age, course, marks


def main() -> None:
    print("Admin login required.")
    try:
        auth.login()
    except AuthenticationError as exc:
        print(f"Login failed: {exc}")
        return

    print("Login successful.\n")
    manager = StudentManager(Storage())

    while True:
        print(MENU)
        choice = input("Select an option: ").strip()

        try:
            if choice == "1":
                sid = input("Student ID: ").strip()
                name, age, course, marks = prompt_student_fields()
                student = manager.add_student(sid, name, age, course, marks)
                print(f"Added: {student}")

            elif choice == "2":
                sid = input("Student ID to update: ").strip()
                existing = manager.get_student(sid)
                name, age, course, marks = prompt_student_fields(existing)
                student = manager.update_student(
                    sid, name=name, age=age, course=course, marks=marks
                )
                print(f"Updated: {student}")

            elif choice == "3":
                sid = input("Student ID to delete: ").strip()
                manager.delete_student(sid)
                print("Deleted.")

            elif choice == "4":
                print_students(manager.all_students())

            elif choice == "5":
                keyword = input("Search keyword (ID/name/course): ").strip()
                print_students(manager.search(keyword))

            elif choice == "6":
                order = input("Descending? (y/N): ").strip().lower() == "y"
                print_students(manager.sort_by_name(descending=order))

            elif choice == "7":
                order = input("Ascending? (y/N): ").strip().lower() != "y"
                print_students(manager.sort_by_marks(descending=order))

            elif choice == "8":
                print(reports.full_report(manager.all_students()))

            elif choice == "9":
                path = manager.storage.export_csv(manager.all_students())
                print(f"Exported to {path}")

            elif choice == "10":
                new_pw = input("New admin password: ").strip()
                if not new_pw:
                    print("Password cannot be empty.")
                else:
                    auth.change_password(new_pw)
                    print("Password updated.")

            elif choice == "0":
                print("Goodbye.")
                break

            else:
                print("Invalid option, please choose again.")

        except StudentManagementError as exc:
            # Catches InvalidInputError, StudentNotFoundError,
            # DuplicateStudentError, StorageError, etc.
            print(f"Error: {exc}")
        except Exception as exc:  # final safety net for unexpected input issues
            print(f"Unexpected error: {exc}")


if __name__ == "__main__":
    main()
