# Bank Account Simulation (Python)

A command-line bank simulator using only the Python standard library (Python 3.8+).

## Run

    python main.py                       # start the app
    python -m unittest discover -s tests -v   # run the tests

## Features

| Requirement | Where / how |
|---|---|
| Multiple account types | `bank/accounts.py`: **Savings**, **Current**, **Fixed Deposit** (each with its own rules) |
| Transaction history with timestamps | Every deposit/withdrawal/transfer/interest credit is stored with an ISO timestamp, unique ID and running balance |
| Interest calculation | 4% (Savings) / 7% (FD) p.a., compounded monthly; view a projection or credit it |
| Secure PIN login | PBKDF2-HMAC-SHA256, 200k iterations, random salt per account, constant-time compare, weak-PIN rejection, lockout (3 wrong tries = 5 min), hidden PIN entry |
| Fund transfer | Between any two accounts; all checks run before any balance changes (atomic), PIN re-confirmation, recipient name masked |
| Export history | CSV, JSON, or printable TXT statement -> `exports/` |

## Account rules

- **Savings**: min opening/balance Rs. 500, 4% interest, max 5 withdrawals/transfers per calendar month.
- **Current**: no interest, Rs. 5,000 overdraft, unlimited transactions.
- **Fixed Deposit**: min Rs. 10,000, 7% interest, one opening deposit only, funds locked until the chosen term (30 days x months) ends.

## Project layout

    main.py              CLI menus
    bank/
      accounts.py        Account base class + 3 account types
      bank.py            Account creation, login/lockout, transfers
      security.py        PIN hashing / validation
      transactions.py    Transaction record
      money.py           Decimal-based money parsing/formatting
      storage.py         Atomic JSON persistence (data/bank_data.json)
      exporter.py        CSV / JSON / TXT export
      exceptions.py      Custom errors
    tests/test_bank.py   27 unit tests

## Notes

- Money uses `Decimal` (never float) so cents are always exact.
- Data is saved after every operation to `data/bank_data.json`. Delete that file to reset.
- Interest is applied on demand (menu > Interest > "simulate months passing") so you can see it without waiting.
- This is a learning simulation, not production banking software (no encryption at rest, single-user file storage).
