"""
Library Management System
--------------------------
A console-based app for issuing/returning books, tracking due dates
and fines, searching, and managing backups.

Run with:  python main.py
"""

from library_system.manager import LibraryManager, LOAN_PERIOD_DAYS, FINE_PER_DAY
from library_system.storage import Storage
from library_system.exceptions import LibraryError

MENU = """
==============================
 LIBRARY MANAGEMENT SYSTEM
==============================
1. Add book
2. Add member
3. Issue book
4. Return book
5. Search books (title/author)
6. View available books
7. View issued books
8. View overdue books
9. Check fine for a transaction
10. View member history
11. Backup data
12. Restore data
0. Exit
==============================
"""


def print_books(books) -> None:
    if not books:
        print("No books found.")
        return
    print(f"{'ISBN':<14}{'Title':<25}{'Author':<20}{'Avail/Total':<12}")
    print("-" * 71)
    for b in books:
        print(f"{b.isbn:<14}{b.title:<25}{b.author:<20}{f'{b.available_copies}/{b.total_copies}':<12}")


def print_transactions(txns) -> None:
    if not txns:
        print("No transactions found.")
        return
    print(f"{'TxnID':<10}{'ISBN':<14}{'Member':<10}{'Issued':<12}{'Due':<12}{'Returned':<12}{'Fine':<6}")
    print("-" * 76)
    for t in txns:
        print(
            f"{t.transaction_id:<10}{t.isbn:<14}{t.member_id:<10}"
            f"{t.issue_date:<12}{t.due_date:<12}{(t.return_date or '-'):<12}{t.fine:<6}"
        )


def main() -> None:
    manager = LibraryManager(Storage())
    print(f"Loan period: {LOAN_PERIOD_DAYS} days | Fine: {FINE_PER_DAY}/day late\n")

    while True:
        print(MENU)
        choice = input("Select an option: ").strip()

        try:
            if choice == "1":
                isbn = input("ISBN: ").strip()
                title = input("Title: ").strip()
                author = input("Author: ").strip()
                copies = input("Number of copies: ").strip()
                book = manager.add_book(isbn, title, author, copies)
                print(f"Added: {book}")

            elif choice == "2":
                member_id = input("Member ID: ").strip()
                name = input("Name: ").strip()
                contact = input("Contact (phone/email): ").strip()
                member = manager.add_member(member_id, name, contact)
                print(f"Added: {member}")

            elif choice == "3":
                isbn = input("ISBN to issue: ").strip()
                member_id = input("Member ID: ").strip()
                date_in = input("Issue date (YYYY-MM-DD, blank = today): ").strip()
                txn = manager.issue_book(isbn, member_id, date_in or None)
                print(f"Issued. Transaction ID: {txn.transaction_id}, due {txn.due_date}")

            elif choice == "4":
                txn_id = input("Transaction ID to return: ").strip()
                date_in = input("Return date (YYYY-MM-DD, blank = today): ").strip()
                txn = manager.return_book(txn_id, date_in or None)
                if txn.fine > 0:
                    print(f"Returned. Late fine: {txn.fine}")
                else:
                    print("Returned on time. No fine.")

            elif choice == "5":
                keyword = input("Search title/author: ").strip()
                print_books(manager.search_books(keyword))

            elif choice == "6":
                print_books(manager.available_books())

            elif choice == "7":
                print_books(manager.issued_books())

            elif choice == "8":
                print_transactions(manager.overdue_transactions())

            elif choice == "9":
                txn_id = input("Transaction ID: ").strip()
                fine = manager.calculate_fine(txn_id)
                print(f"Fine: {fine}")

            elif choice == "10":
                member_id = input("Member ID: ").strip()
                print_transactions(manager.member_history(member_id))

            elif choice == "11":
                path = manager.storage.backup()
                print(f"Backup created at: {path}")

            elif choice == "12":
                backups = manager.storage.list_backups()
                if not backups:
                    print("No backups available.")
                else:
                    print("Available backups:")
                    for b in backups:
                        print(f"  {b}")
                    name = input("Enter backup name to restore: ").strip()
                    manager.storage.restore(name)
                    manager = LibraryManager(manager.storage)  # reload in-memory state
                    print("Restore complete. Data reloaded.")

            elif choice == "0":
                print("Goodbye.")
                break

            else:
                print("Invalid option, please choose again.")

        except LibraryError as exc:
            print(f"Error: {exc}")
        except Exception as exc:  # final safety net
            print(f"Unexpected error: {exc}")


if __name__ == "__main__":
    main()
