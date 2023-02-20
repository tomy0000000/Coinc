import json
from pathlib import Path

import pytest
from pytest_mock import MockFixture

from workflow import Workflow3

with open(Path(__file__).parent.parent / "src" / "default_settings.json", "r") as file:
    DEFAULT_SETTINGS = json.load(file)


class Helpers:
    WORKFLOW_INIT_KWARGS = dict(
        default_settings=DEFAULT_SETTINGS,
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
def settings(mocker: MockFixture):
    mocker.patch(
        "workflow.workflow.Settings",
        return_value=DEFAULT_SETTINGS,
    )
    mocker.patch(
        "coinc.persisted_data",
        return_value=DEFAULT_SETTINGS["alias"],
    )
    mocker.patch(
        "coinc.utils.persisted_data",
        return_value=DEFAULT_SETTINGS["alias"],
    )


@pytest.fixture
def rates(mocker: MockFixture):
    with open("../tests/test_rates.json") as file:
        mocked_rates = json.load(file)
    mocker.patch("coinc.query.load_rates", return_value=mocked_rates)
    mocker.patch("coinc.utils.load_rates", return_value=mocked_rates)


@pytest.fixture
def workflow(helpers, settings, rates) -> Workflow3:
    return Workflow3(**helpers.WORKFLOW_INIT_KWARGS)
