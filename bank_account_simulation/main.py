"""Bank Account Simulation - command line interface."""
import getpass
import os

from bank import Bank, JsonStorage
from bank.accounts import ACCOUNT_TYPES
from bank.exceptions import AuthenticationError, BankError, ValidationError
from bank.exporter import FORMATS, export_history
from bank.money import fmt, parse_amount
from bank.security import validate_pin_format

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "data", "bank_data.json")
EXPORT_DIR = os.path.join(BASE_DIR, "exports")


# ---------- small input helpers ----------
def read_pin(prompt):
    try:
        return getpass.getpass(prompt)
    except Exception:
        return input(prompt)


def ask(prompt):
    return input(prompt).strip()


def line(char="-", width=78):
    print(char * width)


def mask_name(name):
    return " ".join(w[0] + "*" * (len(w) - 1) for w in name.split())


# ---------- display ----------
def show_history(account, limit=None):
    txns = account.transactions[-limit:] if limit else account.transactions
    if not txns:
        print("No transactions yet.")
        return
    line("=")
    print(f"{'Date & Time':<20}{'ID':<10}{'Type':<14}{'Amount':>14}{'Balance':>14}")
    line()
    for t in txns:
        sign = "+" if t.is_credit else "-"
        amt = sign + format(t.amount, ",.2f")
        print(f"{t.timestamp.replace('T', ' '):<20}{t.txn_id:<10}{t.txn_type:<14}"
              f"{amt:>14}{format(t.balance_after, ',.2f'):>14}")
        if t.description:
            print(f"    {t.description}")
    line("=")


def show_info(account):
    line()
    print(f"Holder        : {account.holder_name}")
    print(f"Account No.   : {account.account_number}")
    print(f"Type          : {account.DISPLAY_NAME}  ({account.DESCRIPTION})")
    print(f"Opened        : {account.created_at.replace('T', ' ')}")
    print(f"Balance       : {fmt(account.balance)}")
    if hasattr(account, "maturity_date") and account.maturity_date:
        print(f"Matures on    : {account.maturity_date[:10]}  ({account.term_months} months)")
    line()


# ---------- actions ----------
def create_account_flow(bank):
    print("\nAccount types:")
    types = list(ACCOUNT_TYPES.values())
    for i, cls in enumerate(types, 1):
        print(f"  {i}. {cls.DISPLAY_NAME:<14} {cls.DESCRIPTION}")
    choice = ask("Choose type (number): ")
    if not choice.isdigit() or not 1 <= int(choice) <= len(types):
        raise ValidationError("Invalid choice.")
    cls = types[int(choice) - 1]

    name = ask("Full name: ")
    pin = read_pin("Choose a 4-6 digit PIN: ")
    validate_pin_format(pin)
    if read_pin("Confirm PIN: ") != pin:
        raise ValidationError("PINs do not match.")
    deposit = ask(f"Opening deposit (min {cls.MIN_OPENING_DEPOSIT:,.2f}): ")
    term = 12
    if cls.ACCOUNT_TYPE == "fixed_deposit":
        t = ask("Term in months (1-120) [12]: ") or "12"
        if not t.isdigit():
            raise ValidationError("Term must be a whole number.")
        term = int(t)

    account = bank.create_account(cls.ACCOUNT_TYPE, name, pin, deposit, term_months=term)
    print(f"\nAccount created! Your account number is: {account.account_number}")
    print("Keep it safe - you need it (and your PIN) to log in.")


def login_flow(bank):
    number = ask("Account number: ")
    pin = read_pin("PIN: ")
    account = bank.login(number, pin)
    print(f"\nWelcome, {account.holder_name}!")
    account_menu(bank, account)


def transfer_flow(bank, account):
    to = ask("Recipient account number: ")
    target = bank.get_account(to)
    print(f"Recipient: {mask_name(target.holder_name)} ({target.DISPLAY_NAME})")
    amount = parse_amount(ask("Amount: "))
    note = ask("Note (optional): ")
    if ask(f"Confirm transfer of {fmt(amount)}? (y/n): ").lower() != "y":
        print("Cancelled.")
        return
    if not account.verify_pin(read_pin("Re-enter PIN to authorise: ")):
        raise AuthenticationError("Incorrect PIN. Transfer cancelled.")
    bank.transfer(account, to, amount, note)
    print(f"Transferred {fmt(amount)}. New balance: {fmt(account.balance)}")



def interest_flow(bank, account):
    if account.INTEREST_RATE <= 0:
        print(f"{account.DISPLAY_NAME} accounts do not earn interest.")
        return
    print(f"Rate: {account.INTEREST_RATE * 100:.2f}% p.a., compounded monthly")
    print("  1. Show projection\n  2. Credit interest now (simulate months passing)")
    pick = ask("Choose: ")
    m = ask("Number of months (1-120): ")
    if not m.isdigit() or not 1 <= int(m) <= 120:
        raise ValidationError("Months must be a whole number from 1 to 120.")
    months = int(m)
    if pick == "1":
        line()
        print(f"{'Month':<8}{'Interest':>14}{'Balance':>18}")
        for mo, interest, bal in account.project_interest(months):
            print(f"{mo:<8}{interest:>14,.2f}{bal:>18,.2f}")
        line()
    elif pick == "2":
        total = bank.apply_interest(account, months)
        print(f"Credited {fmt(total)} interest. New balance: {fmt(account.balance)}")
    else:
        raise ValidationError("Invalid choice.")


def export_flow(account):
    print(f"Formats: {', '.join(FORMATS)}")
    ext = (ask("Format [csv]: ") or "csv").lower()
    path = export_history(account, ext, EXPORT_DIR)
    print(f"Exported {len(account.transactions)} transaction(s) to:\n  {path}")


def change_pin_flow(bank, account):
    old = read_pin("Current PIN: ")
    new = read_pin("New PIN: ")
    if read_pin("Confirm new PIN: ") != new:
        raise ValidationError("PINs do not match.")
    bank.change_pin(account, old, new)
    print("PIN changed successfully.")


def account_menu(bank, account):
    menu = """
---------------- ACCOUNT MENU ----------------
 1. Check balance          6. Interest
 2. Deposit                7. Export history
 3. Withdraw               8. Account details
 4. Transfer funds         9. Change PIN
 5. Transaction history    0. Logout
"""
    while True:
        print(menu)
        choice = ask("Choose: ")
        try:
            if choice == "1":
                print(f"Balance: {fmt(account.balance)}")
            elif choice == "2":
                bank.deposit(account, ask("Amount to deposit: "))
                print(f"Deposited. New balance: {fmt(account.balance)}")
            elif choice == "3":
                bank.withdraw(account, ask("Amount to withdraw: "))
                print(f"Withdrawn. New balance: {fmt(account.balance)}")
            elif choice == "4":
                transfer_flow(bank, account)
            elif choice == "5":
                show_history(account)
            elif choice == "6":
                interest_flow(bank, account)
            elif choice == "7":
                export_flow(account)
            elif choice == "8":
                show_info(account)
            elif choice == "9":
                change_pin_flow(bank, account)
            elif choice == "0":
                print("Logged out.")
                return
            else:
                print("Invalid option.")
        except BankError as e:
            print(f"Error: {e}")


def main():
    bank = Bank(JsonStorage(DATA_FILE))
    print("=" * 40)
    print("      BANK ACCOUNT SIMULATION")
    print("=" * 40)
    while True:
        print("\n1. Create account\n2. Login\n3. Exit")
        choice = ask("Choose: ")
        try:
            if choice == "1":
                create_account_flow(bank)
            elif choice == "2":
                login_flow(bank)
            elif choice == "3":
                print("Goodbye!")
                break
            else:
                print("Invalid option.")
        except BankError as e:
            print(f"Error: {e}")
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye!")
            break


if __name__ == "__main__":
    main()
