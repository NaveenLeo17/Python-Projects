"""JSON file persistence with atomic writes."""
import json
import os
import tempfile

from .accounts import ACCOUNT_TYPES


class JsonStorage:
    def __init__(self, path):
        self.path = path

    def load(self):
        if not os.path.exists(self.path):
            return {}
        with open(self.path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        accounts = {}
        for item in raw.get("accounts", []):
            cls = ACCOUNT_TYPES[item["account_type"]]
            acc = cls.from_dict(item)
            accounts[acc.account_number] = acc
        return accounts

    def save(self, accounts):
        folder = os.path.dirname(os.path.abspath(self.path))
        os.makedirs(folder, exist_ok=True)
        payload = {"accounts": [a.to_dict() for a in accounts.values()]}
        fd, tmp = tempfile.mkstemp(dir=folder, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2)
            os.replace(tmp, self.path)  # atomic swap
        except BaseException:
            if os.path.exists(tmp):
                os.remove(tmp)
            raise
