"""Track 05 — assert the Embedded client + estate match the live Tray schema.

Ground truth was captured by read-only introspection against tray.io/graphql
(2026-07-23). These tests pin the corrections so the spec-assumed shapes cannot
silently regress.
"""
import asyncio
from typing import Any

import pytest

from app.services.tray import embedded as emb
from app.services.tray.estate import _instance, _users


class FakeEmbedded(emb.EmbeddedOperationsMixin):
    """Records the (query, variables, token) of each _graphql call and returns
    a canned payload, so we can assert what the real methods build/extract
    without any network."""

    def __init__(self, canned: dict[str, Any] | None = None):
        self.master_token = "MASTER"
        self.calls: list[tuple[str, dict, str]] = []
        self._canned = canned or {}

    async def _graphql(self, query, variables, *, token):
        self.calls.append((query, variables, token))
        return self._canned

    @property
    def last(self):
        return self.calls[-1]


def run(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


# --- read queries -----------------------------------------------------------

def test_solutions_query_is_viewer_scoped_and_uses_title():
    q = emb.SOLUTIONS_QUERY
    assert "viewer {" in q
    assert "title" in q
    assert "name" not in q  # Solution has no `name` field


def test_instances_query_fetches_config_and_auth_values():
    q = emb.SOLUTION_INSTANCES_QUERY
    assert "viewer {" in q
    assert "configValues" in q and "authValues" in q


def test_external_users_reads_root_users_connection():
    c = FakeEmbedded({"users": {"edges": [
        {"node": {"id": "u1", "name": "n", "externalUserId": "e1"}},
    ]}})
    rows = run(c.external_users("MASTER"))
    assert emb.EXTERNAL_USERS_QUERY.strip().startswith("query")
    assert "users(" in emb.EXTERNAL_USERS_QUERY
    assert rows and rows[0]["externalUserId"] == "e1"


def test_solutions_extraction_navigates_viewer():
    c = FakeEmbedded({"viewer": {"solutions": {"edges": [
        {"node": {"id": "s1", "title": "Sol"}},
    ]}}})
    rows = run(c.solutions("MASTER"))
    assert rows and rows[0]["id"] == "s1" and rows[0]["title"] == "Sol"


# --- write mutations (names + input field shapes) ---------------------------

def test_delete_uses_remove_solution_instance():
    assert "removeSolutionInstance" in emb.DELETE_SOLUTION_INSTANCE_MUTATION
    assert "deleteSolutionInstance" not in emb.DELETE_SOLUTION_INSTANCE_MUTATION
    c = FakeEmbedded({"removeSolutionInstance": {"clientMutationId": None}})
    out = run(c.delete_solution_instance("inst-1", user_token="USER"))
    _q, variables, _t = c.last
    assert variables["input"]["solutionInstanceId"] == "inst-1"
    assert out.get("deleted") is True


def test_update_instance_input_uses_instanceName():
    c = FakeEmbedded({"updateSolutionInstance": {"solutionInstance": {"id": "i"}}})
    run(c.update_solution_instance("inst-1", name="Renamed", user_token="USER"))
    _q, variables, _t = c.last
    assert variables["input"]["instanceName"] == "Renamed"
    assert "name" not in variables["input"]


def test_create_instance_input_uses_instanceName():
    c = FakeEmbedded({"createSolutionInstance": {"solutionInstance": {"id": "i"}}})
    run(c.create_solution_instance("sol-1", "New", user_token="USER"))
    _q, variables, _t = c.last
    assert variables["input"]["instanceName"] == "New"
    assert "name" not in variables["input"]


def test_external_user_mutations_exist_and_shape():
    assert hasattr(FakeEmbedded, "update_external_user")
    assert hasattr(FakeEmbedded, "remove_external_user")
    c = FakeEmbedded({"updateExternalUser": {"userId": "u1"}})
    run(c.update_external_user("u1", name="Bob"))
    _q, variables, _t = c.last
    assert variables["input"]["userId"] == "u1"
    assert variables["input"]["name"] == "Bob"
    c2 = FakeEmbedded({"removeExternalUser": {"clientMutationId": None}})
    out = run(c2.remove_external_user("u1"))
    assert c2.last[1]["input"]["userId"] == "u1"
    assert out.get("deleted") is True


# --- estate read model ------------------------------------------------------

def test_user_with_zero_instances_still_appears():
    """The old derive-from-instances model dropped every user with no
    instances. End users are first-class — all must appear."""
    users = [
        {"id": "u1", "name": "has-one", "externalUserId": "e1"},
        {"id": "u2", "name": "has-none", "externalUserId": "e2"},
    ]
    instances = [_instance({
        "id": "i1", "name": "inst", "enabled": True,
        "externalUserId": "e1", "userId": "u1",
    })]
    dtos = _users(users, instances)
    by_ext = {d.external_user_id: d for d in dtos}
    assert set(by_ext) == {"e1", "e2"}
    assert by_ext["e1"].instance_count == 1
    assert by_ext["e2"].instance_count == 0
    assert by_ext["e2"].name == "has-none"


def test_instance_maps_config_and_auth_values_into_slots():
    dto = _instance({
        "id": "i1", "name": "inst", "enabled": True,
        "configValues": [{"externalId": "external_employee_id", "value": "1234"}],
        "authValues": [{"externalId": "external_workday", "authId": "a1"}],
    })
    assert dto.config_slots and dto.config_slots[0]["externalId"] == "external_employee_id"
    assert dto.auth_slots and dto.auth_slots[0]["authId"] == "a1"
