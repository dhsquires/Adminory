"""Official Tray Embedded GraphQL operations."""

from typing import Any


SOLUTIONS_QUERY = """
query Solutions {
  solutions {
    edges {
      node {
        id
        name
      }
    }
  }
}
"""

SOLUTION_INSTANCES_QUERY = """
query SolutionInstances {
  solutionInstances {
    edges {
      node {
        id
        name
        enabled
      }
    }
  }
}
"""

CREATE_EXTERNAL_USER_MUTATION = """
mutation CreateExternalUser($input: CreateExternalUserInput!) {
  createExternalUser(input: $input) {
    userId
  }
}
"""

AUTHORIZE_MUTATION = """
mutation Authorize($input: AuthorizeInput!) {
  authorize(input: $input) {
    accessToken
  }
}
"""

GENERATE_AUTHORIZATION_CODE_MUTATION = """
mutation GenerateAuthorizationCode($input: GenerateAuthorizationCodeInput!) {
  generateAuthorizationCode(input: $input) {
    authorizationCode
  }
}
"""

CREATE_SOLUTION_INSTANCE_MUTATION = """
mutation CreateSolutionInstance($input: CreateSolutionInstanceInput!) {
  createSolutionInstance(input: $input) {
    solutionInstance {
      id
      name
      enabled
    }
  }
}
"""

UPDATE_SOLUTION_INSTANCE_MUTATION = """
mutation UpdateSolutionInstance($input: UpdateSolutionInstanceInput!) {
  updateSolutionInstance(input: $input) {
    solutionInstance {
      id
      name
      enabled
    }
  }
}
"""

DELETE_SOLUTION_INSTANCE_MUTATION = """
mutation DeleteSolutionInstance($input: DeleteSolutionInstanceInput!) {
  deleteSolutionInstance(input: $input) {
    solutionInstanceId
  }
}
"""

# UNCONFIRMED wire name — see spec


def _with_source(value: dict[str, Any]) -> dict[str, Any]:
    return {**value, "source": "official"}


def _connection_items(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, list):
        items = value
    elif isinstance(value, dict) and isinstance(value.get("nodes"), list):
        items = value["nodes"]
    elif isinstance(value, dict) and isinstance(value.get("edges"), list):
        items = [
            edge.get("node")
            for edge in value["edges"]
            if isinstance(edge, dict) and isinstance(edge.get("node"), dict)
        ]
    elif isinstance(value, dict) and isinstance(value.get("items"), list):
        items = value["items"]
    else:
        items = []
    return [_with_source(item) for item in items if isinstance(item, dict)]


def _mutation_result(data: dict[str, Any], field: str, nested: str | None = None) -> Any:
    result = data.get(field, {})
    if nested is not None and isinstance(result, dict) and nested in result:
        return result[nested]
    return result


class EmbeddedOperationsMixin:
    """Methods added to TrayClient for the official Embedded API."""

    master_token: str

    async def _graphql(
        self,
        query: str,
        variables: dict[str, Any],
        *,
        token: str,
    ) -> dict[str, Any]:
        raise NotImplementedError

    async def solutions(self, token: str) -> list[dict[str, Any]]:
        data = await self._graphql(SOLUTIONS_QUERY, {}, token=token)
        return _connection_items(data.get("solutions"))

    async def solution_instances(self, token: str) -> list[dict[str, Any]]:
        data = await self._graphql(SOLUTION_INSTANCES_QUERY, {}, token=token)
        return _connection_items(data.get("solutionInstances"))

    async def create_external_user(
        self,
        name: str,
        external_user_id: str,
    ) -> dict[str, Any]:
        variables = {"input": {"name": name, "externalUserId": external_user_id}}
        data = await self._graphql(
            CREATE_EXTERNAL_USER_MUTATION,
            variables,
            token=self.master_token,
        )
        result = _mutation_result(data, "createExternalUser")
        return _with_source(result if isinstance(result, dict) else {})

    async def authorize(self, user_id: str) -> dict[str, Any]:
        data = await self._graphql(
            AUTHORIZE_MUTATION,
            {"input": {"userId": user_id}},
            token=self.master_token,
        )
        result = _mutation_result(data, "authorize")
        return _with_source(result if isinstance(result, dict) else {})

    async def generate_authorization_code(self, user_id: str) -> dict[str, Any]:
        data = await self._graphql(
            GENERATE_AUTHORIZATION_CODE_MUTATION,
            {"input": {"userId": user_id}},
            token=self.master_token,
        )
        result = _mutation_result(data, "generateAuthorizationCode")
        return _with_source(result if isinstance(result, dict) else {})

    async def create_solution_instance(
        self,
        solution_id: str,
        name: str,
        *,
        user_token: str,
    ) -> dict[str, Any]:
        variables = {"input": {"solutionId": solution_id, "name": name}}
        data = await self._graphql(
            CREATE_SOLUTION_INSTANCE_MUTATION,
            variables,
            token=user_token,
        )
        result = _mutation_result(data, "createSolutionInstance", "solutionInstance")
        return _with_source(result if isinstance(result, dict) else {})

    async def update_solution_instance(
        self,
        instance_id: str,
        *,
        enabled: bool | None = None,
        name: str | None = None,
        user_token: str,
    ) -> dict[str, Any]:
        instance_input: dict[str, Any] = {"solutionInstanceId": instance_id}
        if enabled is not None:
            instance_input["enabled"] = enabled
        if name is not None:
            instance_input["name"] = name

        data = await self._graphql(
            UPDATE_SOLUTION_INSTANCE_MUTATION,
            {"input": instance_input},
            token=user_token,
        )
        result = _mutation_result(data, "updateSolutionInstance", "solutionInstance")
        return _with_source(result if isinstance(result, dict) else {})

    async def delete_solution_instance(
        self,
        instance_id: str,
        *,
        user_token: str,
    ) -> dict[str, Any]:
        data = await self._graphql(
            DELETE_SOLUTION_INSTANCE_MUTATION,
            {"input": {"solutionInstanceId": instance_id}},
            token=user_token,
        )
        result = _mutation_result(data, "deleteSolutionInstance")
        if isinstance(result, dict):
            return _with_source(result)
        return {"deleted": bool(result), "source": "official"}
