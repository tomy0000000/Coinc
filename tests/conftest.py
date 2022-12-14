import json

import pytest
from pytest_mock import MockFixture

from workflow import Workflow3


class Helpers:
    WORKFLOW_INIT_KWARGS = dict(
        default_settings={"favorites": ["EUR", "CNY", "JPY", "GBP"]},
        update_settings={"github_slug": "tomy0000000/Coinc", "frequency": 7},
        help_url="https://github.com/tomy0000000/Coinc/wiki/User-Guide",
    )

    @staticmethod
    def decode_json(data: str) -> dict:
        try:
            return json.loads(data)
        except json.JSONDecodeError:
            raise ValueError("result is not JSON-decodable")


@pytest.fixture
def helpers():
    return Helpers


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
    mocker.patch("coinc.utils.load_rates", return_value=mocked_rates)


@pytest.fixture
def workflow(helpers, config, settings, rates) -> Workflow3:
    return Workflow3(**helpers.WORKFLOW_INIT_KWARGS)
