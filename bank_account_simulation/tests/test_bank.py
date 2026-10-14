import csv
import json
import os
import shutil
import sys
import tempfile
import unittest
from datetime import datetime, timedelta
from decimal import Decimal

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bank import Bank, JsonStorage
from bank.exceptions import (AccountLockedError, AccountNotFoundError,
                             AuthenticationError, InsufficientFundsError,
                             TransactionNotAllowedError, ValidationError)
from bank.exporter import export_history
from bank.security import hash_pin, verify_pin


class BankTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.path = os.path.join(self.tmp, "bank.json")
        self.bank = Bank(JsonStorage(self.path))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def savings(self, deposit="1000", pin="2580"):
        return self.bank.create_account("savings", "Asha Verma", pin, deposit)

    def current(self, deposit="0", pin="2580"):
        return self.bank.create_account("current", "Ravi Shah", pin, deposit)


class TestAccountTypes(BankTestCase):
    def test_savings_min_balance(self):
        a = self.savings("1000")
        a.withdraw("500")
        with self.assertRaises(InsufficientFundsError):
            a.withdraw("1")

    def test_savings_opening_minimum(self):
        with self.assertRaises(ValidationError):
            self.savings("100")

    def test_savings_monthly_limit(self):
        a = self.savings("10000")
        for _ in range(5):
            a.withdraw("10")
        with self.assertRaises(TransactionNotAllowedError):
            a.withdraw("10")

    def test_current_overdraft(self):
        a = self.current("100")
        a.withdraw("5100")
        self.assertEqual(a.balance, Decimal("-5000.00"))
        with self.assertRaises(InsufficientFundsError):
            a.withdraw("0.01")

    def test_fixed_deposit_rules(self):
        fd = self.bank.create_account("fixed_deposit", "Meera K", "2580", "10000", term_months=6)
        with self.assertRaises(TransactionNotAllowedError):
            fd.withdraw("100")
        with self.assertRaises(TransactionNotAllowedError):
            fd.deposit("100")
        matured = datetime.now() + timedelta(days=200)
        fd.withdraw("100", now=matured)
        self.assertEqual(fd.balance, Decimal("9900.00"))

    def test_fixed_deposit_minimum(self):
        with self.assertRaises(ValidationError):
            self.bank.create_account("fixed_deposit", "X Y", "2580", "5000")

    def test_unknown_type(self):
        with self.assertRaises(ValidationError):
            self.bank.create_account("gold", "X Y", "2580", "1000")


class TestAmounts(BankTestCase):
    def test_invalid_amounts(self):
        a = self.savings()
        for bad in ["abc", "-5", "0", "1.234", "nan", "inf", ""]:
            with self.assertRaises(ValidationError, msg=bad):
                a.deposit(bad)

    def test_decimal_precision(self):
        a = self.savings("1000")
        a.deposit("0.10")
        a.deposit("0.20")
        self.assertEqual(a.balance, Decimal("1000.30"))


class TestTransactions(BankTestCase):
    def test_history_has_timestamps(self):
        a = self.savings("1000")
        a.deposit("50")
        a.withdraw("20")
        self.assertEqual(len(a.transactions), 3)
        for t in a.transactions:
            datetime.fromisoformat(t.timestamp)
        self.assertEqual(a.transactions[-1].balance_after, a.balance)

    def test_transfer_success(self):
        a, b = self.savings("2000"), self.current("0")
        self.bank.transfer(a, b.account_number, "300", "rent")
        self.assertEqual(a.balance, Decimal("1700.00"))
        self.assertEqual(b.balance, Decimal("300.00"))
        self.assertEqual(a.transactions[-1].txn_type, "TRANSFER_OUT")
        self.assertEqual(b.transactions[-1].txn_type, "TRANSFER_IN")

    def test_transfer_failure_changes_nothing(self):
        a, b = self.savings("600"), self.current("0")
        with self.assertRaises(InsufficientFundsError):
            self.bank.transfer(a, b.account_number, "300")
        self.assertEqual(a.balance, Decimal("600.00"))
        self.assertEqual(b.balance, Decimal("0.00"))
        self.assertEqual(len(b.transactions), 0)

    def test_transfer_to_locked_fd_is_atomic(self):
        a = self.savings("5000")
        fd = self.bank.create_account("fixed_deposit", "Meera K", "2580", "10000")
        with self.assertRaises(TransactionNotAllowedError):
            self.bank.transfer(a, fd.account_number, "100")
        self.assertEqual(a.balance, Decimal("5000.00"))

    def test_transfer_errors(self):
        a = self.savings("2000")
        with self.assertRaises(AccountNotFoundError):
            self.bank.transfer(a, "0000000000", "10")
        with self.assertRaises(TransactionNotAllowedError):
            self.bank.transfer(a, a.account_number, "10")


class TestInterest(BankTestCase):
    def test_savings_monthly_compounding(self):
        a = self.savings("12000")
        total = a.apply_interest(2)
        # 12000 * 0.04/12 = 40.00 ; 12040 * 0.04/12 = 40.13
        self.assertEqual(total, Decimal("80.13"))
        self.assertEqual(a.balance, Decimal("12080.13"))
        self.assertEqual(sum(t.txn_type == "INTEREST" for t in a.transactions), 2)

    def test_projection_does_not_change_balance(self):
        a = self.savings("12000")
        rows = a.project_interest(3)
        self.assertEqual(len(rows), 3)
        self.assertEqual(a.balance, Decimal("12000.00"))

    def test_current_has_no_interest(self):
        with self.assertRaises(TransactionNotAllowedError):
            self.current("1000").apply_interest(1)

    def test_bad_months(self):
        with self.assertRaises(ValidationError):
            self.savings().apply_interest(0)


class TestSecurity(BankTestCase):
    def test_pin_is_hashed(self):
        a = self.savings(pin="2580")
        self.assertNotIn("2580", a.pin_hash)
        self.assertTrue(a.verify_pin("2580"))
        self.assertFalse(a.verify_pin("2581"))
        with open(self.path) as f:
            self.assertNotIn('"2580"', f.read())

    def test_unique_salts(self):
        self.assertNotEqual(hash_pin("2580")[0], hash_pin("2580")[0])
        s, h = hash_pin("2580")
        self.assertTrue(verify_pin("2580", s, h))

    def test_weak_pins_rejected(self):
        for pin in ["123", "1234567", "abcd", "1111", "1234", "4321", "12 4", ""]:
            with self.assertRaises(ValidationError, msg=pin):
                self.savings(pin=pin)

    def test_login_success_and_failure(self):
        a = self.savings(pin="2580")
        self.assertIs(self.bank.login(a.account_number, "2580"), a)
        with self.assertRaises(AuthenticationError):
            self.bank.login(a.account_number, "9999")
        with self.assertRaises(AuthenticationError):
            self.bank.login("nope", "2580")

    def test_lockout_and_expiry(self):
        a = self.savings(pin="2580")
        now = datetime.now()
        for _ in range(2):
            with self.assertRaises(AuthenticationError):
                self.bank.login(a.account_number, "0000", now=now)
        with self.assertRaises(AccountLockedError):
            self.bank.login(a.account_number, "0000", now=now)
        with self.assertRaises(AccountLockedError):  # correct PIN still blocked
            self.bank.login(a.account_number, "2580", now=now + timedelta(minutes=1))
        self.assertIs(self.bank.login(a.account_number, "2580",
                                      now=now + timedelta(minutes=6)), a)

    def test_change_pin(self):
        a = self.savings(pin="2580")
        self.bank.change_pin(a, "2580", "7391")
        self.assertTrue(a.verify_pin("7391"))
        with self.assertRaises(ValidationError):
            self.bank.change_pin(a, "wrong", "7391")


class TestPersistenceAndExport(BankTestCase):
    def test_round_trip(self):
        a = self.savings("1000")
        b = self.bank.create_account("fixed_deposit", "Meera K", "2580", "10000", term_months=6)
        self.bank.deposit(a, "250.50")
        self.bank.transfer(a, self.current().account_number, "100")
        reloaded = Bank(JsonStorage(self.path))
        ra = reloaded.accounts[a.account_number]
        self.assertEqual(ra.balance, a.balance)
        self.assertEqual(len(ra.transactions), len(a.transactions))
        self.assertTrue(ra.verify_pin("2580"))
        rb = reloaded.accounts[b.account_number]
        self.assertEqual((rb.term_months, rb.maturity_date), (6, b.maturity_date))

    def test_lockout_persists(self):
        a = self.savings(pin="2580")
        for _ in range(3):
            with self.assertRaises((AuthenticationError, AccountLockedError)):
                self.bank.login(a.account_number, "0000")
        reloaded = Bank(JsonStorage(self.path))
        with self.assertRaises(AccountLockedError):
            reloaded.login(a.account_number, "2580")

    def test_export_formats(self):
        a = self.savings("1000")
        a.deposit("100")
        a.withdraw("50")
        out = os.path.join(self.tmp, "exports")

        p = export_history(a, "csv", out)
        with open(p, newline="") as f:
            rows = list(csv.reader(f))
        self.assertEqual(len(rows), 4)
        self.assertEqual(rows[0][0], "Timestamp")
        self.assertEqual(rows[-1][3], "-50.00")

        p = export_history(a, "json", out)
        with open(p) as f:
            data = json.load(f)
        self.assertEqual(len(data["transactions"]), 3)
        self.assertEqual(data["current_balance"], "1050.00")

        p = export_history(a, "txt", out)
        with open(p) as f:
            self.assertIn("Closing balance", f.read())

        with self.assertRaises(ValidationError):
            export_history(a, "pdf", out)


if __name__ == "__main__":
    unittest.main()
