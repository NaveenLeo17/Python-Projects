# Library Management System

A console-based Library Management System in Python.

## Features
- Add/manage book records (ISBN, title, author, copy counts) and member records
- Issue a book to a member with automatic due-date tracking (default 14-day loan)
- Return a book with automatic late-fine calculation (default ₹5/day late)
- Search books by title or author
- View available books, issued books, and overdue loans at a glance
- Per-member borrowing history
- Backup the entire data directory to a timestamped folder, and restore from any backup
- Custom exceptions for invalid input, missing records, duplicates, and storage errors

## Structure
```
main.py                        # CLI entry point
library_system/
    models.py                  # Book, Member, Transaction dataclasses
    storage.py                 # JSON load/save + backup/restore
    manager.py                 # Issue/return, fines, search, availability
    exceptions.py               # Custom exception hierarchy
data/                          # Created automatically on first run
    books.json
    members.json
    transactions.json
backups/                       # Created automatically; holds timestamped backups
```

## Run it
```
python main.py
```

## How it works
- **Issuing**: pick a book by ISBN and a member ID. If copies are available, a transaction
  is created with `issue_date` and `due_date` (issue_date + 14 days), and `available_copies`
  is decremented.
- **Returning**: pick the open transaction ID. If returned after the due date, a fine of
  `late_days × ₹5` is recorded on the transaction, and the copy becomes available again.
- **Fine preview**: option 9 lets you check what the fine *would be* for an open loan as of
  today (or a given date) without actually returning the book.
- **Backup**: copies `data/` into `backups/backup_<timestamp>/`.
- **Restore**: lists existing backups, and copies the chosen one's files back into `data/`,
  then reloads the in-memory state.

## Notes / things you may want to tune
- `LOAN_PERIOD_DAYS` and `FINE_PER_DAY` are constants at the top of `library_system/manager.py`.
- Dates are entered as `YYYY-MM-DD`; leave blank to default to today.
- A book can only be removed once every issued copy has been returned.
