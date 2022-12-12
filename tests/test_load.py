from pprint import pprint

import coinc


class TestLoad:
    def test_load_all(self, workflow, helpers, monkeypatch, capsys):
        monkeypatch.setattr("sys.argv", ["main.py", "load", "all"])
        coinc.load(workflow)
        out = helpers.decode_json(capsys.readouterr().out)

        EXPECTED_CURRENCIES = ["TWD", "KRW", "HKD", "SGD", "CAD", "AUD", "NZD", "CHF"]
        UNEXPECTED_CURRENCIES = ["EUR", "CNY", "JPY", "GBP"]

        appear = {currency: False for currency in EXPECTED_CURRENCIES}
        for item in out["items"]:
            currency = item["subtitle"]
            assert currency not in UNEXPECTED_CURRENCIES  # No unexpected currencies
            if currency in EXPECTED_CURRENCIES:
                appear[currency] = True

        # All expected currencies should appear
        assert all(appear.values())

    def test_load_all_sgd(self, workflow, helpers, monkeypatch, capsys):
        monkeypatch.setattr("sys.argv", ["main.py", "load", "all", "singapore"])
        coinc.load(workflow)
        out = helpers.decode_json(capsys.readouterr().out)

        EXPECTED_CURRENCIES = ["SGD"]
        UNEXPECTED_CURRENCIES = [
            "EUR",
            "CNY",
            "JPY",
            "GBP",
            "TWD",
            "KRW",
            "HKD",
            "CAD",
            "AUD",
            "NZD",
            "CHF",
        ]

        appear = {currency: False for currency in EXPECTED_CURRENCIES}
        for item in out["items"]:
            currency = item["subtitle"]
            assert currency not in UNEXPECTED_CURRENCIES  # No unexpected currencies
            if currency in EXPECTED_CURRENCIES:
                appear[currency] = True

    def test_load_all_none(self, workflow, helpers, monkeypatch, capsys):
        monkeypatch.setattr("sys.argv", ["main.py", "load", "all", "!@#$%^&*"])
        coinc.load(workflow)
        out = helpers.decode_json(capsys.readouterr().out)

        UNEXPECTED_CURRENCIES = [
            "EUR",
            "CNY",
            "JPY",
            "GBP",
            "TWD",
            "KRW",
            "HKD",
            "SGD",
            "CAD",
            "AUD",
            "NZD",
            "CHF",
        ]

        for item in out["items"]:
            currency = item["subtitle"]
            assert currency not in UNEXPECTED_CURRENCIES  # No unexpected currencies

    def test_load_favorites(self, workflow, helpers, monkeypatch, capsys):
        monkeypatch.setattr("sys.argv", ["main.py", "load", "favorites"])
        coinc.load(workflow)
        out = helpers.decode_json(capsys.readouterr().out)

        EXPECTED_CURRENCIES = ["EUR", "CNY", "JPY", "GBP"]

        appear = {currency: False for currency in EXPECTED_CURRENCIES}
        for item in out["items"]:
            currency = item["subtitle"]
            if currency in EXPECTED_CURRENCIES:
                appear[currency] = True

        # All expected currencies should appear
        assert all(appear.values())
