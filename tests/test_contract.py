"""Conformance checks against the independently loaded saved target."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
from uuid import uuid4

from fastapi import FastAPI
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient
from jsonschema import Draft202012Validator, FormatChecker

from poker_tutor.api import create_app
from fastapi.openapi.utils import get_openapi


TARGET = json.loads((Path(__file__).resolve().parent.parent / "openapi-fullspec.json").read_text())


class ContractTests(unittest.TestCase):
    def test_native_generation_and_typed_metadata_cover_all_operations(self):
        app = create_app()
        generated = app.openapi()
        self.assertEqual(generated, get_openapi(title=app.title, version=app.version, routes=app.routes))
        self.assertNotIn("servers", generated)
        self.assertNotEqual(generated, TARGET)
        actual = {(r.path, method): r for r in app.routes if isinstance(r, APIRoute) for method in r.methods}
        for path, item in TARGET["paths"].items():
            for method, operation in item.items():
                route = actual[(path, method.upper())]
                self.assertEqual(type(route), APIRoute)
                self.assertIsNone(route.openapi_extra)
                self.assertEqual(route.operation_id, operation["operationId"])
                native = generated["paths"][path][method]
                self.assertEqual(set(native["responses"]), set(operation["responses"]))
                self.assertEqual("requestBody" in native, "requestBody" in operation)
                if "requestBody" in operation:
                    self.assertTrue(native["requestBody"]["required"])
                if operation["operationId"] in ("createSession", "createHand"):
                    header = next(p for p in native["parameters"] if p["name"] == "Idempotency-Key")
                    self.assertTrue(header["required"])
                if method != "delete":
                    self.assertIsNotNone(route.response_model)
        self.assertEqual(len(actual), 10)

    def test_generation_reflects_new_route_declarations(self):
        app = create_app()
        @app.get("/probe", response_model=list[int])
        def probe():
            return [1]
        spec = app.openapi()
        self.assertIn("/probe", spec["paths"])
        schema = spec["paths"]["/probe"]["get"]["responses"]["200"]["content"]["application/json"]["schema"]
        self.assertEqual(schema["items"]["type"], "integer")

    def test_every_live_operation_response_matches_saved_schema(self):
        with TemporaryDirectory() as temp, TestClient(create_app(Path(temp) / "contract.sqlite3")) as c:
            exercised = set()

            def call(method, template, concrete=None, **kwargs):
                response = c.request(method, concrete or template, **kwargs)
                operation = TARGET["paths"][template][method.lower()]
                self.assertIn(str(response.status_code), operation["responses"], response.text)
                expected = operation["responses"][str(response.status_code)]
                if "content" in expected:
                    self.assertEqual(response.headers["content-type"], "application/json")
                    schema = expected["content"]["application/json"]["schema"]
                    Draft202012Validator({**schema, "components": TARGET["components"]}, format_checker=FormatChecker()).validate(response.json())
                else:
                    self.assertEqual(response.content, b"")
                for header in expected.get("headers", {}):
                    self.assertIn(header, response.headers)
                exercised.add((template, method.lower()))
                return response

            call("GET", "/api/v1/sessions")
            call("POST", "/api/v1/sessions", json={})  # required creation header
            call("POST", "/api/v1/sessions", content="{", headers={"Content-Type": "application/json"})
            call("POST", "/api/v1/sessions", content="{}")
            session = call("POST", "/api/v1/sessions", json={}, headers={"Idempotency-Key": str(uuid4())}).json()
            sid = session["id"]
            base = f"/api/v1/sessions/{sid}"
            call("GET", "/api/v1/sessions/{session_id}", base)
            template = "/api/v1/sessions/{session_id}/hands"
            with patch("poker_tutor.api.prepare", side_effect=RuntimeError("analysis failure")):
                call("POST", template, base + "/hands", json={}, headers={"Idempotency-Key": str(uuid4())})
            hand = call("POST", template, base + "/hands", json={}, headers={"Idempotency-Key": str(uuid4())}).json()
            url = base + "/hands/" + hand["id"]
            template = "/api/v1/sessions/{session_id}/hands/{hand_id}"
            call("GET", template, url)
            call("GET", template + "/replay", url + "/replay")
            call("GET", template + "/replay", url + "/replay?step=-1")
            call("GET", template + "/replay", url + "/replay?step=99")
            for street in ("flop", "turn", "river"):
                call("POST", template + "/actions", url + "/actions", json={"action": "check", "street": street})
                call("POST", template + "/continue", url + "/continue", json={"street": street})
            call("POST", "/api/v1/sessions/{session_id}/end", base + "/end", json={})
            call("DELETE", "/api/v1/sessions/{session_id}", base)
            call("GET", template, url)
            self.assertEqual(exercised, {(p, m) for p, item in TARGET["paths"].items() for m in item})
            self.assertEqual(c.get("/openapi.json").json(), c.app.openapi())

    def test_route_contract_rejects_noncanonical_creation_uuid_and_invalid_query(self):
        with TemporaryDirectory() as temp, TestClient(create_app(Path(temp) / "inputs.sqlite3")) as c:
            for value in ("bad", uuid4().hex):
                response = c.post("/api/v1/sessions", json={}, headers={"Idempotency-Key": value})
                self.assertEqual(response.status_code, 422)
                self.assertEqual(response.json()["code"], "validation_error")
            self.assertEqual(c.get("/api/v1/sessions").json(), [])
