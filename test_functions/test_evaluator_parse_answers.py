import litellm

from crm_sandbox.env.env import Evaluator


class _DummyMessage:
    def __init__(self, content: str) -> None:
        self.content = content


class _DummyChoice:
    def __init__(self, content: str) -> None:
        self.message = _DummyMessage(content)


class _DummyResponse:
    def __init__(self, content: str) -> None:
        self.choices = [_DummyChoice(content)]


def _fake_completion_factory(content: str):
    def _fake_completion(*_args, **_kwargs):
        return _DummyResponse(content)

    return _fake_completion


def test_parse_answers_accepts_json_list(monkeypatch):
    monkeypatch.setattr(litellm, "completion", _fake_completion_factory('["ID1","ID2"]'))
    evaluator = Evaluator(model="dummy", provider="dummy")
    assert evaluator.parse_answers("irrelevant", "top_issue_identification") == ["ID1", "ID2"]


def test_parse_answers_accepts_json_object(monkeypatch):
    monkeypatch.setattr(
        litellm,
        "completion",
        _fake_completion_factory('{"extracted_answers": ["ID1"]}'),
    )
    evaluator = Evaluator(model="dummy", provider="dummy")
    assert evaluator.parse_answers("irrelevant", "top_issue_identification") == ["ID1"]


def test_parse_answers_falls_back_to_raw_value(monkeypatch):
    monkeypatch.setattr(litellm, "completion", _fake_completion_factory("ID123"))
    evaluator = Evaluator(model="dummy", provider="dummy")
    assert evaluator.parse_answers("irrelevant", "top_issue_identification") == ["ID123"]


def test_parse_answers_defaults_to_none_on_empty(monkeypatch):
    monkeypatch.setattr(litellm, "completion", _fake_completion_factory("   "))
    evaluator = Evaluator(model="dummy", provider="dummy")
    assert evaluator.parse_answers("irrelevant", "top_issue_identification") == ["None"]


def test_parse_answers_defaults_to_none_on_none_string(monkeypatch):
    monkeypatch.setattr(litellm, "completion", _fake_completion_factory("None"))
    evaluator = Evaluator(model="dummy", provider="dummy")
    assert evaluator.parse_answers("irrelevant", "top_issue_identification") == ["None"]
