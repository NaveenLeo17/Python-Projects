# Student Management System

A console-based Student Management System in Python.

## Features
- Add, update, delete, and search student records
- Data persisted as JSON (`data/students.json`); export/import to CSV
- Sort records by name or marks (ascending/descending)
- Admin login (salted SHA-256 password hash, 3 attempts, changeable password)
- Reports: topper, lowest scorer, average, median, pass/fail counts, grade distribution
- Custom exceptions for invalid input, missing records, duplicates, and storage errors

## Structure
```
main.py                        # CLI entry point
student_management/
    models.py                  # Student dataclass
    storage.py                 # JSON load/save + CSV import/export
    manager.py                 # CRUD, search, sort, validation
    reports.py                 # Report calculations
    auth.py                    # Admin login / password management
    exceptions.py               # Custom exception hierarchy
data/                          # Created automatically on first run
    students.json
    admin.json
```

## Run it
```
python main.py
```

**Default admin login (first run only):**
- Username: `admin`
- Password: `admin123`

Change it immediately from the menu (option 10) — a fresh salted hash is generated and written to `data/admin.json`.

## Notes
- All CRUD operations save to `data/students.json` immediately.
- Marks must be 0–100 and age 1–119; invalid values raise `InvalidInputError` and are caught in the menu loop without crashing the app.
- Adding a duplicate `student_id` raises `DuplicateStudentError`.
- Acting on a nonexistent `student_id` raises `StudentNotFoundError`.
