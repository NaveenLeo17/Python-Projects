"""Export transaction history to CSV, JSON or a printable text statement."""
import csv
import json
import os
from datetime import datetime

from .exceptions import ValidationError
from .money import fmt

FORMATS = ("csv", "json", "txt")
_HEADERS = ["Timestamp", "Transaction ID", "Type", "Amount", "Balance After", "Description"]


def default_filename(account, ext):
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"statement_{account.account_number}_{stamp}.{ext}"


def export_history(account, ext, directory="exports", filename=None):
    """Write the history and return the full file path."""
    ext = ext.lower().lstrip(".")
    if ext not in FORMATS:
        raise ValidationError(f"Unsupported format. Choose from: {', '.join(FORMATS)}")
    os.makedirs(directory, exist_ok=True)
    path = os.path.join(directory, filename or default_filename(account, ext))
    {"csv": _write_csv, "json": _write_json, "txt": _write_txt}[ext](account, path)
    return path


def _write_csv(account, path):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(_HEADERS)
        for t in account.transactions:
            w.writerow([t.timestamp.replace("T", " "), t.txn_id, t.txn_type,
                        f"{t.signed_amount:.2f}", f"{t.balance_after:.2f}", t.description])


def _write_json(account, path):
    data = {
        "account_number": account.account_number,
        "holder_name": account.holder_name,
        "account_type": account.DISPLAY_NAME,
        "current_balance": str(account.balance),
        "exported_at": datetime.now().isoformat(timespec="seconds"),
        "transactions": [t.to_dict() for t in account.transactions],
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def _write_txt(account, path):
    lines = [
        "=" * 96,
        f"ACCOUNT STATEMENT - {account.DISPLAY_NAME.upper()} ACCOUNT",
        f"Holder : {account.holder_name}",
        f"Account: {account.account_number}",
        f"Printed: {datetime.now():%Y-%m-%d %H:%M:%S}",
        "=" * 96,
        f"{'Date & Time':<20}{'ID':<10}{'Type':<14}{'Amount':>16}{'Balance':>16}  Description",
        "-" * 96,
    ]
    for t in account.transactions:
        sign = "+" if t.is_credit else "-"
        amt = sign + format(t.amount, ",.2f")
        bal = format(t.balance_after, ",.2f")
        lines.append(
            f"{t.timestamp.replace('T', ' '):<20}{t.txn_id:<10}{t.txn_type:<14}"
            f"{amt:>16}{bal:>16}  {t.description}")
    lines += ["-" * 96, f"Closing balance: {fmt(account.balance)}", "=" * 96]
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
