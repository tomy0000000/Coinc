import json

import pytest
from pytest_mock import MockFixture

import coinc
from workflow import Workflow3

WORKFLOW_INIT_KWARGS = dict(
    default_settings={"favorites": ["EUR", "CNY", "JPY", "GBP"]},
    update_settings={"github_slug": "tomy0000000/Coinc", "frequency": 7},
    help_url="https://github.com/tomy0000000/Coinc/wiki/User-Guide",
)


@pytest.fixture(autouse=True)
def test_dir(monkeypatch):
    monkeypatch.chdir("src")


@pytest.fixture()
def config(monkeypatch):
    monkeypatch.setenv("APP_ID", "app_id")
    monkeypatch.setenv("BASE", "USD")
    monkeypatch.setenv("EXPIRE", "300")
    monkeypatch.setenv("LOCALE", "en_us")
    monkeypatch.setenv("ORIENTAION", "DEFAULT")
    monkeypatch.setenv("PRECISION", "3")


@pytest.fixture()
def settings(mocker: MockFixture):
    mocker.patch(
        "workflow.workflow.Settings",
        return_value={
            "__workflow_last_version": "2.0.0",
            "favorites": ["EUR", "CNY", "JPY", "GBP"],
        },
    )


@pytest.fixture
def rates(mocker: MockFixture):
    with open("../tests/test_rates.json") as file:
        mocked_rates = json.load(file)
    mocker.patch("coinc.query.load_rates", return_value=mocked_rates)


@pytest.fixture
def workflow(config, settings, rates) -> Workflow3:
    return Workflow3(**WORKFLOW_INIT_KWARGS)


def decode_json(data: str) -> dict:
    try:
        return json.loads(data)
    except json.JSONDecodeError:
        raise ValueError("result is not JSON-decodable")


class TestConvert:
    def test_cur(self, workflow, monkeypatch, capsys):
        monkeypatch.setattr("sys.argv", ["main.py", "convert"])
        coinc.convert(workflow)
        out = decode_json(capsys.readouterr().out)

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

    def test_cur_200(self, workflow, monkeypatch, capsys):
        monkeypatch.setattr("sys.argv", ["main.py", "convert", "200"])
        coinc.convert(workflow)
        out = decode_json(capsys.readouterr().out)

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

    def test_cur_GBP(self, workflow, monkeypatch, capsys):
        monkeypatch.setattr("sys.argv", ["main.py", "convert", "GBP"])
        coinc.convert(workflow)
        out = decode_json(capsys.readouterr().out)

        RESULTS = ["1.230 USD", "0.813 GBP", "Last Update"]
        for result, item in zip(RESULTS, out["items"]):
            assert result in item["title"]

    def test_cur_5_GBP(self, workflow, monkeypatch, capsys):
        monkeypatch.setattr("sys.argv", ["main.py", "convert", "5", "GBP"])
        coinc.convert(workflow)
        out = decode_json(capsys.readouterr().out)

        RESULTS = ["6.150 USD", "4.065 GBP", "Last Update"]
        for result, item in zip(RESULTS, out["items"]):
            assert result in item["title"]

    def test_cur_GBP_TWD(self, workflow, monkeypatch, capsys):
        monkeypatch.setattr("sys.argv", ["main.py", "convert", "GBP", "TWD"])
        coinc.convert(workflow)
        out = decode_json(capsys.readouterr().out)

        RESULTS = ["37.580 TWD", "0.027 GBP", "Last Update"]
        for result, item in zip(RESULTS, out["items"]):
            assert result in item["title"]

    def test_cur_5_GBP_TWD(self, workflow, monkeypatch, capsys):
        monkeypatch.setattr("sys.argv", ["main.py", "convert", "5", "GBP", "TWD"])
        coinc.convert(workflow)
        out = decode_json(capsys.readouterr().out)

        RESULTS = ["187.900 TWD", "0.133 GBP", "Last Update"]
        for result, item in zip(RESULTS, out["items"]):
            assert result in item["title"]

    def test_config_app_id_empty(self, config, monkeypatch, capsys):
        monkeypatch.delenv("APP_ID")
        workflow = Workflow3(**WORKFLOW_INIT_KWARGS)
        monkeypatch.setattr("sys.argv", ["main.py", "convert"])
        coinc.convert(workflow)
        out = decode_json(capsys.readouterr().out)

        assert "APP_ID" in out["items"][0]["title"]

    def test_config_base_invalid(self, config, rates, monkeypatch, capsys):
        monkeypatch.setenv("BASE", "CURRENCY")
        workflow = Workflow3(**WORKFLOW_INIT_KWARGS)
        monkeypatch.setattr("sys.argv", ["main.py", "convert"])
        coinc.convert(workflow)
        out = decode_json(capsys.readouterr().out)

        assert "Invalid" in out["items"][0]["title"]
        assert "CURRENCY" in out["items"][0]["title"]

    def test_config_base(self, config, rates, monkeypatch, mocker, capsys):
        monkeypatch.setenv("BASE", "TWD")
        mocker.patch(
            "workflow.workflow.Settings",
            return_value={
                "__workflow_last_version": "2.0.0",
                "favorites": ["USD"],
            },
        )
        workflow = Workflow3(**WORKFLOW_INIT_KWARGS)
        monkeypatch.setattr("sys.argv", ["main.py", "convert"])
        coinc.convert(workflow)
        out = decode_json(capsys.readouterr().out)

        RESULTS = ["30.553 TWD", "0.033 USD", "Last Update"]
        for result, item in zip(RESULTS, out["items"]):
            assert result in item["title"]

    def test_config_locale_invalid(self, config, rates, monkeypatch, capsys):
        monkeypatch.setenv("LOCALE", "language_country")
        workflow = Workflow3(**WORKFLOW_INIT_KWARGS)
        monkeypatch.setattr("sys.argv", ["main.py", "convert"])
        coinc.convert(workflow)
        out = decode_json(capsys.readouterr().out)

        assert "Invalid" in out["items"][0]["title"]
        assert "language_country" in out["items"][0]["title"]

    def test_config_locale(self, config, rates, monkeypatch, mocker, capsys):
        monkeypatch.setenv("LOCALE", "fr_fr")
        mocker.patch(
            "workflow.workflow.Settings",
            return_value={
                "__workflow_last_version": "2.0.0",
                "favorites": ["EUR"],
            },
        )
        workflow = Workflow3(**WORKFLOW_INIT_KWARGS)
        monkeypatch.setattr("sys.argv", ["main.py", "convert"])
        coinc.convert(workflow)
        out = decode_json(capsys.readouterr().out)

        RESULTS = ["1,054 USD", "0,949 EUR", "Last Update"]
        for result, item in zip(RESULTS, out["items"]):
            assert result in item["title"]

    def test_config_orientation_invalid(self, config, rates, monkeypatch, capsys):
        monkeypatch.setenv("ORIENTATION", "orientation")
        workflow = Workflow3(**WORKFLOW_INIT_KWARGS)
        monkeypatch.setattr("sys.argv", ["main.py", "convert"])
        coinc.convert(workflow)
        out = decode_json(capsys.readouterr().out)

        assert "Invalid" in out["items"][0]["title"]
        assert "orientation" in out["items"][0]["title"]

    def test_config_orientation_from(self, config, rates, monkeypatch, mocker, capsys):
        monkeypatch.setenv("ORIENTATION", "FROM_FAV")
        workflow = Workflow3(**WORKFLOW_INIT_KWARGS)
        monkeypatch.setattr("sys.argv", ["main.py", "convert"])
        coinc.convert(workflow)
        out = decode_json(capsys.readouterr().out)

        RESULTS = ["1.054 USD", "0.142 USD", "0.007 USD", "1.230 USD", "Last Update"]
        for result, item in zip(RESULTS, out["items"]):
            assert result in item["title"]

    def test_config_orientation_to(self, config, rates, monkeypatch, mocker, capsys):
        monkeypatch.setenv("ORIENTATION", "TO_FAV")
        workflow = Workflow3(**WORKFLOW_INIT_KWARGS)
        monkeypatch.setattr("sys.argv", ["main.py", "convert"])
        coinc.convert(workflow)
        out = decode_json(capsys.readouterr().out)

        RESULTS = ["0.949 EUR", "7.025 CNY", "134.315 JPY", "0.813 GBP", "Last Update"]
        for result, item in zip(RESULTS, out["items"]):
            assert result in item["title"]

    def test_config_precision_invalid(self, config, rates, monkeypatch, capsys):
        monkeypatch.setenv("PRECISION", "precision")
        workflow = Workflow3(**WORKFLOW_INIT_KWARGS)
        monkeypatch.setattr("sys.argv", ["main.py", "convert"])
        coinc.convert(workflow)
        out = decode_json(capsys.readouterr().out)

        assert "Invalid" in out["items"][0]["title"]
        assert "precision" in out["items"][0]["title"]

    def test_config_precision(self, config, rates, monkeypatch, mocker, capsys):
        monkeypatch.setenv("PRECISION", "10")
        mocker.patch(
            "workflow.workflow.Settings",
            return_value={
                "__workflow_last_version": "2.0.0",
                "favorites": ["EUR"],
            },
        )
        workflow = Workflow3(**WORKFLOW_INIT_KWARGS)
        monkeypatch.setattr("sys.argv", ["main.py", "convert"])
        coinc.convert(workflow)
        out = decode_json(capsys.readouterr().out)

        RESULTS = ["1.0537496628 USD", "0.9489920000 EUR", "Last Update"]
        for result, item in zip(RESULTS, out["items"]):
            assert result in item["title"]
