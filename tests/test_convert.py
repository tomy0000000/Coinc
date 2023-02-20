import coinc
from workflow import Workflow3


class TestConvert:
    def test_cur(self, workflow, helpers, monkeypatch, capsys):
        monkeypatch.setattr("sys.argv", ["main.py", "convert"])
        coinc.convert(workflow)
        out = helpers.decode_json(capsys.readouterr().out)

        RESULTS = [
            "1.054 USD",
            "0.949 EUR",
            "0.142 USD",
            "7.025 CNY",
            "0.007 USD",
            "134.315 JPY",
            "1.230 USD",
            "0.813 GBP",
            "Last Update",
        ]
        for result, item in zip(RESULTS, out["items"]):
            assert result in item["title"]

    def test_cur_200(self, workflow, helpers, monkeypatch, capsys):
        monkeypatch.setattr("sys.argv", ["main.py", "convert", "200"])
        coinc.convert(workflow)
        out = helpers.decode_json(capsys.readouterr().out)

        RESULTS = [
            "210.750 USD",
            "189.798 EUR",
            "28.471 USD",
            "1,404.940 CNY",
            "1.489 USD",
            "26,862.999 JPY",
            "246.000 USD",
            "162.602 GBP",
            "Last Update",
        ]
        for result, item in zip(RESULTS, out["items"]):
            assert result in item["title"]

    def test_cur_GBP(self, workflow, helpers, monkeypatch, capsys):
        monkeypatch.setattr("sys.argv", ["main.py", "convert", "GBP"])
        coinc.convert(workflow)
        out = helpers.decode_json(capsys.readouterr().out)

        RESULTS = ["1.230 USD", "0.813 GBP", "Last Update"]
        for result, item in zip(RESULTS, out["items"]):
            assert result in item["title"]

    def test_cur_5_GBP(self, workflow, helpers, monkeypatch, capsys):
        monkeypatch.setattr("sys.argv", ["main.py", "convert", "5", "GBP"])
        coinc.convert(workflow)
        out = helpers.decode_json(capsys.readouterr().out)

        RESULTS = ["6.150 USD", "4.065 GBP", "Last Update"]
        for result, item in zip(RESULTS, out["items"]):
            assert result in item["title"]

    def test_cur_GBP_TWD(self, workflow, helpers, monkeypatch, capsys):
        monkeypatch.setattr("sys.argv", ["main.py", "convert", "GBP", "TWD"])
        coinc.convert(workflow)
        out = helpers.decode_json(capsys.readouterr().out)

        RESULTS = ["37.580 TWD", "0.027 GBP", "Last Update"]
        for result, item in zip(RESULTS, out["items"]):
            assert result in item["title"]

    def test_cur_5_GBP_TWD(self, workflow, helpers, monkeypatch, capsys):
        monkeypatch.setattr("sys.argv", ["main.py", "convert", "5", "GBP", "TWD"])
        coinc.convert(workflow)
        out = helpers.decode_json(capsys.readouterr().out)

        RESULTS = ["187.900 TWD", "0.133 GBP", "Last Update"]
        for result, item in zip(RESULTS, out["items"]):
            assert result in item["title"]

    def test_config_app_id_empty(self, helpers, monkeypatch, capsys):
        monkeypatch.delenv("APP_ID")
        workflow = Workflow3(**helpers.WORKFLOW_INIT_KWARGS)
        monkeypatch.setattr("sys.argv", ["main.py", "convert"])
        coinc.convert(workflow)
        out = helpers.decode_json(capsys.readouterr().out)

        assert "APP_ID" in out["items"][0]["title"]

    def test_config_base_invalid(self, helpers, rates, monkeypatch, capsys):
        monkeypatch.setenv("BASE", "CURRENCY")
        workflow = Workflow3(**helpers.WORKFLOW_INIT_KWARGS)
        monkeypatch.setattr("sys.argv", ["main.py", "convert"])
        coinc.convert(workflow)
        out = helpers.decode_json(capsys.readouterr().out)

        assert "Invalid" in out["items"][0]["title"]
        assert "CURRENCY" in out["items"][0]["title"]

    def test_config_base(self, helpers, rates, monkeypatch, mocker, capsys):
        monkeypatch.setenv("BASE", "TWD")
        mocker.patch(
            "workflow.workflow.Settings",
            return_value={"favorites": ["USD"]},
        )
        workflow = Workflow3(**helpers.WORKFLOW_INIT_KWARGS)
        monkeypatch.setattr("sys.argv", ["main.py", "convert"])
        coinc.convert(workflow)
        out = helpers.decode_json(capsys.readouterr().out)

        RESULTS = ["30.553 TWD", "0.033 USD", "Last Update"]
        for result, item in zip(RESULTS, out["items"]):
            assert result in item["title"]

    def test_config_locale_invalid(self, helpers, rates, monkeypatch, capsys):
        monkeypatch.setenv("LOCALE", "language_country")
        workflow = Workflow3(**helpers.WORKFLOW_INIT_KWARGS)
        monkeypatch.setattr("sys.argv", ["main.py", "convert"])
        coinc.convert(workflow)
        out = helpers.decode_json(capsys.readouterr().out)

        assert "Invalid" in out["items"][0]["title"]
        assert "language_country" in out["items"][0]["title"]

    def test_config_locale(self, helpers, rates, monkeypatch, mocker, capsys):
        monkeypatch.setenv("LOCALE", "fr_fr")
        mocker.patch(
            "workflow.workflow.Settings",
            return_value={"favorites": ["EUR"]},
        )
        workflow = Workflow3(**helpers.WORKFLOW_INIT_KWARGS)
        monkeypatch.setattr("sys.argv", ["main.py", "convert"])
        coinc.convert(workflow)
        out = helpers.decode_json(capsys.readouterr().out)

        RESULTS = ["1,054 USD", "0,949 EUR", "Last Update"]
        for result, item in zip(RESULTS, out["items"]):
            assert result in item["title"]

    def test_config_orientation_invalid(self, helpers, rates, monkeypatch, capsys):
        monkeypatch.setenv("ORIENTATION", "orientation")
        workflow = Workflow3(**helpers.WORKFLOW_INIT_KWARGS)
        monkeypatch.setattr("sys.argv", ["main.py", "convert"])
        coinc.convert(workflow)
        out = helpers.decode_json(capsys.readouterr().out)

        assert "Invalid" in out["items"][0]["title"]
        assert "orientation" in out["items"][0]["title"]

    def test_config_orientation_from(
        self, helpers, settings, rates, monkeypatch, mocker, capsys
    ):
        monkeypatch.setenv("ORIENTATION", "FROM_FAV")
        workflow = Workflow3(**helpers.WORKFLOW_INIT_KWARGS)
        monkeypatch.setattr("sys.argv", ["main.py", "convert"])
        coinc.convert(workflow)
        out = helpers.decode_json(capsys.readouterr().out)

        RESULTS = ["1.054 USD", "0.142 USD", "0.007 USD", "1.230 USD", "Last Update"]
        for result, item in zip(RESULTS, out["items"]):
            assert result in item["title"]

    def test_config_orientation_to(
        self, helpers, settings, rates, monkeypatch, mocker, capsys
    ):
        monkeypatch.setenv("ORIENTATION", "TO_FAV")
        workflow = Workflow3(**helpers.WORKFLOW_INIT_KWARGS)
        monkeypatch.setattr("sys.argv", ["main.py", "convert"])
        coinc.convert(workflow)
        out = helpers.decode_json(capsys.readouterr().out)

        RESULTS = ["0.949 EUR", "7.025 CNY", "134.315 JPY", "0.813 GBP", "Last Update"]
        for result, item in zip(RESULTS, out["items"]):
            assert result in item["title"]

    def test_config_precision_invalid(self, helpers, rates, monkeypatch, capsys):
        monkeypatch.setenv("PRECISION", "precision")
        workflow = Workflow3(**helpers.WORKFLOW_INIT_KWARGS)
        monkeypatch.setattr("sys.argv", ["main.py", "convert"])
        coinc.convert(workflow)
        out = helpers.decode_json(capsys.readouterr().out)

        assert "Invalid" in out["items"][0]["title"]
        assert "precision" in out["items"][0]["title"]

    def test_config_precision(self, helpers, rates, monkeypatch, mocker, capsys):
        monkeypatch.setenv("PRECISION", "10")
        mocker.patch(
            "workflow.workflow.Settings",
            return_value={"favorites": ["EUR"]},
        )
        workflow = Workflow3(**helpers.WORKFLOW_INIT_KWARGS)
        monkeypatch.setattr("sys.argv", ["main.py", "convert"])
        coinc.convert(workflow)
        out = helpers.decode_json(capsys.readouterr().out)

        RESULTS = ["1.0537496628 USD", "0.9489920000 EUR", "Last Update"]
        for result, item in zip(RESULTS, out["items"]):
            assert result in item["title"]
