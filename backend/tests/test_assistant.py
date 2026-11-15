"""Assistant validation, isolation, provider failures, and context provenance."""

import copy
import json

import httpx

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.main import app
from app.models.models import Astronaut, HealthAnalysis, SensorReading
from app.services.ai_adapter import AIAdapter, get_ai_adapter
from app.schemas.assistant import AssistantProviderRequest

PROFILE = {"astronaut_id": "AST-AI", "name": "Private fictional name",
           "mission_id": "MARS-SIM", "mission_role": "Engineer",
           "profile_metadata": {"private_note": "DO-NOT-FORWARD"}}
REQUEST = {"astronaut_id": "AST-AI", "question": "What does the prototype show?", "mode": "mock"}
URL = "/ai/assistant"


@pytest.fixture
def seeded(client):
    assert client.post("/astronauts", json=PROFILE).status_code == 201
    return client


@pytest.fixture
def configure_provider():
    def configure(provider):
        app.dependency_overrides[get_ai_adapter] = lambda: AIAdapter(provider)
    yield configure
    app.dependency_overrides.pop(get_ai_adapter, None)


def valid_response(payload):
    return {"astronaut_id": payload["astronaut_id"], "answer": "Provider test response.",
            "assistant_version": "test-provider-1", "is_mock": False,
            "limitations": ["Prototype test output; not a medical assessment."]}


def add_mock_analysis(client):
    client.post("/health/ingest", json={
        "astronaut_id": "AST-AI", "timestamp": "2026-11-14T10:00:00Z",
        "sensor_type": "smart_band", "measurement_type": "heart_rate", "value": 78,
        "unit": "beats/min", "source": "synthetic_example", "is_simulated": True,
    })
    response = client.post("/health/AST-AI/analyses", json={"mode": "mock", "source": "synthetic_example"})
    assert response.status_code == 201
    return response.json()


def test_mock_works_offline_without_provider(seeded, configure_provider):
    def forbidden(payload):
        pytest.fail("Mock mode must not invoke a provider")
    configure_provider(forbidden)
    response = seeded.post(URL, json=REQUEST)
    assert response.status_code == 200
    result = response.json()
    assert result["is_mock"] is True and result["status"] == "mock"
    assert result["data_source"] == "backend_mock"
    assert result["assistant_version"] == "backend-assistant-mock-1.0"
    assert "MOCK" in result["answer"]
    assert result["context"] == {"analysis": None}
    assert result["response_timestamp"].endswith("Z")
    assert "question" not in result
    assert "DO-NOT-FORWARD" not in response.text


def test_default_is_labelled_mock(seeded):
    payload = REQUEST.copy()
    payload.pop("mode")
    assert seeded.post(URL, json=payload).json()["is_mock"] is True


@pytest.mark.parametrize("changes", [
    {"question": ""}, {"question": "  "}, {"question": "q" * 2001},
    {"question": 123}, {"question": None}, {"mode": "cloud"},
    {"astronaut_id": "bad/id"}, {"analysis_id": 0}, {"analysis_id": True},
    {"analysis_id": "1"}, {"unexpected": "ignored?"},
])
def test_bad_request_rejected_before_provider(seeded, configure_provider, changes):
    def forbidden(payload):
        pytest.fail("Invalid request must not reach provider")
    configure_provider(forbidden)
    assert seeded.post(URL, json=REQUEST | changes).status_code == 422


def test_unknown_astronaut_and_analysis(seeded):
    assert seeded.post(URL, json=REQUEST | {"astronaut_id": "missing"}).status_code == 404
    assert seeded.post(URL, json=REQUEST | {"analysis_id": 999}).status_code == 404
    analysis = add_mock_analysis(seeded)
    seeded.post("/astronauts", json=PROFILE | {"astronaut_id": "OTHER"})
    response = seeded.post(URL, json=REQUEST | {"astronaut_id": "OTHER", "analysis_id": analysis["id"]})
    assert response.status_code == 404


def test_local_unconfigured_no_silent_mock(seeded):
    response = seeded.post(URL, json=REQUEST | {"mode": "local"})
    assert response.status_code == 503
    assert "answer" not in response.json()
    assert seeded.post(URL, json=REQUEST).status_code == 200
    assert seeded.get("/health").json() == {"status": "ok"}


def test_local_minimal_context_and_trimmed_question(seeded, configure_provider):
    # An existing analysis is deliberately NOT forwarded without explicit selection.
    add_mock_analysis(seeded)
    seen = []
    def provider(payload):
        seen.append(copy.deepcopy(payload))
        payload["context"]["analysis"] = {"mutated": True}
        return valid_response(payload)
    configure_provider(provider)
    response = seeded.post(URL, json=REQUEST | {"mode": "local", "question": "  Explain this.  "})
    assert response.status_code == 200
    assert seen == [{"astronaut_id": "AST-AI", "question": "Explain this.", "context": {"analysis": None}}]
    result = response.json()
    assert result["status"] == "completed" and result["is_mock"] is False
    assert result["data_source"] == "configured_local_provider"
    assert result["context"] == {"analysis": None}


def test_selected_mock_analysis_remains_labelled(seeded, configure_provider):
    analysis = add_mock_analysis(seeded)
    seen = []
    def provider(payload):
        seen.append(copy.deepcopy(payload))
        result = valid_response(payload)
        result["is_mock"] = True
        return result
    configure_provider(provider)
    response = seeded.post(URL, json=REQUEST | {"mode": "local", "analysis_id": analysis["id"]})
    assert response.status_code == 200
    result = response.json()
    context = seen[0]["context"]["analysis"]
    assert context["analysis_id"] == analysis["id"]
    assert context["is_mock"] is True and context["status"] == "mock"
    assert context["anomaly_detected"] is None and context["anomaly_score"] is None
    assert context["measurement_timestamp"] == analysis["measurement_timestamp"]
    assert result["is_mock"] is True and result["status"] == "mock"
    assert result["context"]["analysis"] == context
    assert "input_readings" not in str(seen)
    assert "prepared_input" not in str(seen)
    assert "private_note" not in str(seen)
    assert "Private fictional name" not in str(seen)


def test_real_analysis_uncertainty_preserved(seeded, configure_provider, database_engine):
    analysis = add_mock_analysis(seeded)
    with Session(database_engine) as session:
        record = session.get(HealthAnalysis, analysis["id"])
        result = copy.deepcopy(record.result)
        result.update(is_mock=False, status="insufficient_data", model_version="test-model",
                      ml_result={"data_quality": {"status": "partial", "errors": {"spo2": "missing"}},
                                 "anomaly": {"method": "personalized_baseline_deviation",
                                             "sensor_method": "personalized_baseline_deviation"}})
        record.result = result
        session.commit()
    configure_provider(valid_response)
    response = seeded.post(URL, json=REQUEST | {"mode": "local", "analysis_id": analysis["id"]})
    assert response.status_code == 200
    context = response.json()["context"]["analysis"]
    assert context["is_mock"] is False
    assert context["status"] == "insufficient_data" and context["anomaly_score"] is None
    assert context["data_quality"]["errors"] == {"spo2": "missing"}
    assert context["detector_method"] == "personalized_baseline_deviation"


@pytest.mark.parametrize("error,status", [(RuntimeError, 503), (TimeoutError, 504)])
def test_provider_failures_are_safe(seeded, configure_provider, error, status):
    def broken(payload):
        raise error("SECRET provider credentials and internal paths")
    configure_provider(broken)
    response = seeded.post(URL, json=REQUEST | {"mode": "local"})
    assert response.status_code == status
    assert "SECRET" not in response.text
    assert "answer" not in response.json()


@pytest.mark.parametrize("defect", ["empty", "identity", "missing", "flag", "extra", "nonfinite", "limits"])
def test_invalid_provider_output(seeded, configure_provider, defect):
    def broken(payload):
        response = valid_response(payload)
        if defect == "empty":
            response["answer"] = " "
        elif defect == "identity":
            response["astronaut_id"] = "OTHER"
        elif defect == "missing":
            response.pop("assistant_version")
        elif defect == "flag":
            response["is_mock"] = "false"
        elif defect == "extra":
            response["secret"] = "unexpected"
        elif defect == "nonfinite":
            response["secret"] = float("nan")
        else:
            response["limitations"] = []
        return response
    configure_provider(broken)
    response = seeded.post(URL, json=REQUEST | {"mode": "local"})
    assert response.status_code == 502
    assert "answer" not in response.json()


def test_no_database_writes(seeded, configure_provider, database_engine):
    def counts():
        with Session(database_engine) as session:
            return [session.scalar(select(func.count()).select_from(model))
                    for model in (Astronaut, SensorReading, HealthAnalysis)]
    before = counts()
    configure_provider(valid_response)
    assert seeded.post(URL, json=REQUEST).status_code == 200
    assert seeded.post(URL, json=REQUEST | {"mode": "local"}).status_code == 200
    assert counts() == before


def test_openapi_exposes_assistant(client):
    schema = client.get("/openapi.json")
    assert schema.status_code == 200
    assert "post" in schema.json()["paths"][URL]
    assert client.get("/docs").status_code == 200


def test_configured_member3_http_contract(monkeypatch):
    monkeypatch.setenv("AI_ASSISTANT_URL", "http://127.0.0.1:8002/api/v1/assistant/respond")
    monkeypatch.setenv("AEGIS_ASSISTANT_TIMEOUT_SECONDS", "2.5")
    seen = {}

    def handler(request):
        seen["url"] = str(request.url)
        seen["timeout"] = request.extensions["timeout"]
        seen["payload"] = json.loads(request.content)
        return httpx.Response(200, json=valid_response(seen["payload"]))

    client_type = httpx.Client
    monkeypatch.setattr("app.services.ai_adapter.httpx.Client", lambda **kwargs: client_type(
        transport=httpx.MockTransport(handler), **kwargs))
    adapter = get_ai_adapter()
    request = AssistantProviderRequest(
        astronaut_id="AST-AI", question="Explain this.", context={"analysis": None},
    )
    result = adapter.respond(request, "local")

    assert seen["url"] == "http://127.0.0.1:8002/api/v1/assistant/respond"
    assert seen["timeout"]["read"] == 2.5
    assert seen["payload"] == {
        "astronaut_id": "AST-AI", "question": "Explain this.", "context": {"analysis": None},
    }
    assert result.is_mock is False
    assert result.data_source == "configured_local_provider"


@pytest.mark.parametrize("failure,expected_status", [
    (httpx.ReadTimeout, 504),
    (httpx.ConnectError, 503),
])
def test_member3_http_failures_keep_distinct_statuses(client, monkeypatch, failure, expected_status):
    monkeypatch.setenv("AI_ASSISTANT_URL", "http://127.0.0.1:8002/api/v1/assistant/respond")
    def fail_request(*_args, **_kwargs):
        raise failure("request failed")
    client_type = httpx.Client
    monkeypatch.setattr("app.services.ai_adapter.httpx.Client", lambda **kwargs: client_type(
        transport=httpx.MockTransport(fail_request), **kwargs))
    client.post("/astronauts", json=PROFILE)
    response = client.post(URL, json=REQUEST | {"mode": "local"})
    assert response.status_code == expected_status
    assert "answer" not in response.json()
