import coinc


class TestAlias:
    def test_alias_empty_args(self, workflow, helpers, monkeypatch, capsys):
        monkeypatch.setattr("sys.argv", ["main.py", "alias"])
        coinc.alias(workflow)
        out = helpers.decode_json(capsys.readouterr().out)

        assert "Type the alias" in out["items"][0]["title"]

    def test_alias_too_many_args(self, workflow, helpers, monkeypatch, capsys):
        monkeypatch.setattr(
            "sys.argv", ["main.py", "alias", "some-alias", "currency", "something"]
        )
        coinc.alias(workflow)
        out = helpers.decode_json(capsys.readouterr().out)

        assert "Too many arguments" in out["items"][0]["title"]

    def test_alias_invalid_alias(self, workflow, helpers, monkeypatch, capsys):
        monkeypatch.setattr("sys.argv", ["main.py", "alias", "1"])
        coinc.alias(workflow)
        out = helpers.decode_json(capsys.readouterr().out)

        assert "Can't create alias with number in it" in out["items"][0]["title"]

    def test_alias_existed_alias(self, workflow, helpers, monkeypatch, capsys):
        monkeypatch.setattr("sys.argv", ["main.py", "alias", "$"])
        coinc.alias(workflow)
        out = helpers.decode_json(capsys.readouterr().out)

        assert "is already aliased" in out["items"][0]["title"]

    def test_alias_no_currency(self, workflow, helpers, monkeypatch, capsys):
        monkeypatch.setattr("sys.argv", ["main.py", "alias", "some-alias"])
        coinc.alias(workflow)
        out = helpers.decode_json(capsys.readouterr().out)

        RESULTS = ["search", "AED", "AFN", "ALL"]
        for result, item in zip(RESULTS, out["items"]):
            assert result in item["subtitle"]

    def test_alias_currency_prompt(self, workflow, helpers, monkeypatch, capsys):
        monkeypatch.setattr("sys.argv", ["main.py", "alias", "some-alias", "united"])
        coinc.alias(workflow)
        out = helpers.decode_json(capsys.readouterr().out)

        RESULTS = ["search", "AED", "USD"]
        for result, item in zip(RESULTS, out["items"]):
            assert result in item["subtitle"]

    def test_alias_currency_not_found(self, workflow, helpers, monkeypatch, capsys):
        monkeypatch.setattr("sys.argv", ["main.py", "alias", "some-alias", "ZZZ"])
        coinc.alias(workflow)
        out = helpers.decode_json(capsys.readouterr().out)

        assert "No currency found" in out["items"][0]["title"]

    def test_alias_valid(self, workflow, helpers, monkeypatch, capsys):
        monkeypatch.setattr("sys.argv", ["main.py", "alias", "some-alias", "USD"])
        coinc.alias(workflow)
        out = helpers.decode_json(capsys.readouterr().out)

        assert "SOME-ALIAS" in out["items"][0]["title"]
        assert "USD" in out["items"][0]["title"]
        assert "Confirm to save" in out["items"][0]["subtitle"]


class TestUnalias:
    def test_unalias_empty_args(self, workflow, helpers, monkeypatch, capsys):
        monkeypatch.setattr("sys.argv", ["main.py", "unalias"])
        coinc.unalias(workflow)
        out = helpers.decode_json(capsys.readouterr().out)

        RESULTS = ["'$'", "'AU$'", "'C$'", "'CA$'"]
        for result, item in zip(RESULTS, out["items"]):
            assert result in item["title"]

    def test_unalias_too_many_args(self, workflow, helpers, monkeypatch, capsys):
        monkeypatch.setattr(
            "sys.argv", ["main.py", "unalias", "some-alias", "something"]
        )
        coinc.unalias(workflow)
        out = helpers.decode_json(capsys.readouterr().out)

        assert "Too many arguments" in out["items"][0]["title"]

    def test_unalias_invalid_alias(self, workflow, helpers, monkeypatch, capsys):
        monkeypatch.setattr("sys.argv", ["main.py", "unalias", "some-alias"])
        coinc.unalias(workflow)
        out = helpers.decode_json(capsys.readouterr().out)

        assert "not found" in out["items"][0]["title"]

    def test_unalias_valid(self, workflow, helpers, monkeypatch, capsys):
        monkeypatch.setattr("sys.argv", ["main.py", "unalias", "$"])
        coinc.unalias(workflow)
        out = helpers.decode_json(capsys.readouterr().out)

        assert "$" in out["items"][0]["title"]
        assert "USD" in out["items"][0]["title"]
        assert "confirm unalias" in out["items"][0]["subtitle"]


class TestSaveAlias:
    def test_save_alias_create(self, workflow, helpers, monkeypatch, capsys):
        # TODO
        pass

    def test_save_alias_remove(self, workflow, helpers, monkeypatch, capsys):
        # TODO
        pass

    def test_save_alias_invalid(self, workflow, helpers, monkeypatch, capsys):
        # TODO
        pass
