"""
ESI OpenAPI Client Stub for Testing

This module provides a stub implementation for ESI OpenAPI clients that can be used
in tests to return predefined test data without making actual API calls.
"""

# Standard Library
import json
from datetime import datetime
from pathlib import Path
from typing import Any

# Third Party
from pydantic import BaseModel, create_model


def _to_pydantic_model_instance(name: str, data: Any) -> Any:
    """
    Recursively convert dicts/lists to Pydantic model instances.
    """
    # Lists -> convert each item
    if isinstance(data, list):
        return [_to_pydantic_model_instance(name + "Item", v) for v in data]

    # Helper: try to parse ISO datetime strings into datetime objects
    def _try_parse_datetime(value: Any) -> Any:
        if not isinstance(value, str):
            return value
        try:
            v = value
            # Accept trailing Z as UTC
            if v.endswith("Z"):
                v = v[:-1] + "+00:00"
            return datetime.fromisoformat(v)
        except Exception:
            return value

    # Dicts -> create a transient pydantic model class and instantiate it
    if isinstance(data, dict):
        fields: dict[str, tuple[type, Any]] = {}
        values: dict[str, Any] = {}
        for k, v in data.items():
            # Use Any for field type; instantiate nested models recursively
            fields[k] = (Any, ...)
            # Recursively convert nested structures
            val = _to_pydantic_model_instance(name + k.capitalize(), v)
            # Try to convert ISO datetime-like strings to datetime objects
            if isinstance(val, str):
                val = _try_parse_datetime(val)
            values[k] = val

        Model = create_model(name, **fields, __base__=BaseModel)
        return Model(**values)

    # Primitives -> return as-is
    return data


def _select_method_data(method_data: Any, kwargs: dict, endpoint=None):
    """Select appropriate test data entry from a mapping using endpoint param names.

    - If method_data is a dict and endpoint.param_names are provided, try to match
      kwargs values (as str or int) to the dict keys. If found, return that value.
    - If only a single entry exists in the dict, return its value as a sensible default.
    - Otherwise return method_data unchanged.
    """
    if not endpoint or not isinstance(method_data, dict):
        return method_data

    # Drill down through param names in order, attempting to match kwargs
    current = method_data
    matched_any = False
    for param_name in endpoint.param_names:
        if not isinstance(current, dict):
            break
        if param_name in kwargs and kwargs[param_name] is not None:
            key = str(kwargs[param_name])
            # direct string key
            if key in current:
                current = current[key]
                matched_any = True
                continue
            # try integer key match
            try:
                int_key = int(kwargs[param_name])
            except Exception:
                int_key = None
            if int_key is not None and int_key in current:
                current = current[int_key]
                matched_any = True
                continue
        # if we couldn't match this param, stop drilling
        break

    if matched_any:
        return current

    # Fallback for POST-style methods where the body contains ids (common key 'body')
    if (
        "body" in kwargs
        and kwargs["body"] is not None
        and isinstance(kwargs["body"], (list, tuple))
    ):
        key = str(kwargs["body"])
        if key in method_data:
            return method_data[key]

    # Fallback: if single-entry dict, return its value
    if isinstance(method_data, dict) and len(method_data) == 1:
        return list(method_data.values())[0]

    return method_data


class MockResponse:
    """
    Mock HTTP response object for testing.

    Mimics the response object returned by ESI when return_response=True.
    """

    def __init__(self, status_code: int = 200, headers: dict | None = None):
        """
        Initialize mock response.

        Attributes:
            status_code (int): HTTP status code
            headers (dict | None): Response headers
        """
        self.status_code = status_code
        self.headers = headers or {"X-Pages": 1}
        self.text = ""
        self.content = b""


class EsiEndpoint:
    """
    Definition of an ESI endpoint for stub configuration.

    Defines which endpoints should be stubbed and with what side effects.
    """

    def __init__(
        self,
        category: str,
        method: str,
        param_names: str | tuple[str, ...],
        side_effect: Exception | None = None,
    ):
        """
        Initialize an ESI endpoint definition.

        Attributes:
            category (str): ESI category name (e.g., "Character", "Skills")
            method (str): ESI method name (e.g., "GetCharactersCharacterIdSkills")
            param_names (str | tuple[str, ...]): Parameter name(s) used to look up test data
            side_effect (Exception | None): Optional exception to raise when this endpoint is called
        """
        self.category = category
        self.method = method
        # Allow tests to pass multiple param names as two positional strings
        if isinstance(param_names, tuple):
            params = list(param_names)
        else:
            params = [param_names]

        # If side_effect is a string, tests likely passed a second param name
        if isinstance(side_effect, str):
            params.append(side_effect)
            self.side_effect = None
        else:
            self.side_effect = side_effect

        self.param_names = tuple(params)

    def __repr__(self):
        return f"EsiEndpoint({self.category}.{self.method})"


class EsiOperationStub:
    """
    Stub for ESI operation that mimics the behavior of openapi_clients operations.

    This class simulates the result() and results() methods that are called on
    ESI operations in the actual implementation.

    If a side_effect is configured, calling result() or results() will raise that exception
    instead of returning test data.
    """

    def __init__(self, test_data: Any, side_effect: Exception | None = None):
        """
        Initialize the operation stub with test data or side effect.

        Attributes:
            test_data (Any): The data to return when result() or results() is called
            side_effect (Exception | None): Exception to raise when result() or results() is called
        """
        self._test_data = test_data
        self._side_effect = side_effect

    def result(
        self,
        use_etag: bool = True,  # not implemented yet
        return_response: bool = False,
        force_refresh: bool = False,  # not implemented yet
        use_cache: bool = True,  # not implemented yet
        **kwargs,
    ) -> Any:
        """
        Simulate the result() method of an ESI operation.

        Returns a single result (not a list) as an object with attributes.
        When return_response=True, returns tuple of (data, response).

        If a side_effect was configured, raises that exception instead.

        Args:
            use_etag (bool) Whether to use ETag (ignored in stub)
            return_response (bool): Whether to return response object
            force_refresh (bool): Whether to force refresh (ignored in stub)
            use_cache (bool): Whether to use cache (ignored in stub)
        Returns:
            Any: Test data as object, or tuple of (data, response) if return_response=True
        Raises:
            Exception: if side_effect was configured
        """
        # If side_effect is configured, raise it
        if self._side_effect is not None:
            # Support both exception instances and lists of exceptions/values
            if isinstance(self._side_effect, list):
                # Pop from list for sequential side effects
                if self._side_effect:
                    effect = self._side_effect.pop(0)
                    if isinstance(effect, Exception):
                        raise effect
                    # If not an exception, return it as data
                    return (
                        _to_pydantic_model_instance("SideEffect", effect)
                        if not return_response
                        else (
                            _to_pydantic_model_instance("SideEffect", effect),
                            MockResponse(),
                        )
                    )
            elif isinstance(self._side_effect, Exception):
                raise self._side_effect

        # Convert dict to Pydantic model instance to mimic OpenAPI 3 behavior
        data = _to_pydantic_model_instance("Result", self._test_data)

        if return_response:
            # Return tuple of (data, response)
            response = MockResponse()
            return (data, response)

        return data

    def results(
        self,
        use_etag: bool = True,  # not implemented yet
        return_response: bool = False,
        force_refresh: bool = False,  # not implemented yet
        use_cache: bool = True,  # not implemented yet
        **kwargs,
    ) -> list[Any]:
        """
        Simulate the results() method of an ESI operation.

        Returns a list of results (paginated data) as objects with attributes.
        When return_response=True, returns tuple of (data, response).

        If a side_effect was configured, raises that exception instead.

        Args:
            use_etag (bool): Whether to use ETag (ignored in stub)
            return_response (bool): Whether to return response object
            force_refresh (bool): Whether to force refresh (ignored in stub)
            use_cache (bool): Whether to use cache (ignored in stub)
        Returns:
            list[Any]: Test data as list of objects, or tuple of (data, response) if return_response=True
        Raises:
            Exception: if side_effect was configured
        """
        # If side_effect is configured, raise it
        if self._side_effect is not None:
            # Support both exception instances and lists of exceptions/values
            if isinstance(self._side_effect, list):
                # Pop from list for sequential side effects
                if self._side_effect:
                    effect = self._side_effect.pop(0)
                    if isinstance(effect, Exception):
                        raise effect
                    # If not an exception, return it as data
                    data = _to_pydantic_model_instance("SideEffect", effect)
                    result_data = data if isinstance(data, list) else [data]
                    return (
                        (result_data, MockResponse())
                        if return_response
                        else result_data
                    )
            elif isinstance(self._side_effect, Exception):
                raise self._side_effect

        # Convert to Pydantic model instances first
        data = _to_pydantic_model_instance("Results", self._test_data)

        # If test data is already a list, use it as is
        if isinstance(data, list):
            result_data = data
        else:
            # If single item, wrap in list
            result_data = [data]

        if return_response:
            # Return tuple of (data, response)
            response = MockResponse()
            return (result_data, response)

        return result_data


class EsiCategoryStub:
    """
    Stub for an ESI category (e.g., Skills, Character, Wallet).

    This class holds methods for a specific ESI category and returns
    EsiOperationStub instances when methods are called.
    """

    def __init__(
        self,
        category_name: str,
        test_data: dict[str, Any],
        endpoints: dict[str, EsiEndpoint],
    ):
        """
        Initialize the category stub.

        Attributes:
            category_name (str): Name of the ESI category
            test_data (dict[str, Any]): Test data for methods in this category
            endpoints (dict[str, EsiEndpoint]): Endpoint definitions for this category
        """
        self._category_name = category_name
        self._test_data = test_data
        self._endpoints = endpoints

    def __getattr__(self, method_name: str) -> callable:
        """
        Return a callable that creates an EsiOperationStub when invoked.

        Args:
            method_name (str): Name of the ESI method
        Returns:
            callable: Callable that returns EsiOperationStub
        Raises:
            AttributeError: If method is not registered in endpoints
        """

        def operation_caller(**kwargs) -> EsiOperationStub:
            """
            Create and return an operation stub with test data and optional side effect.

            :return: Operation stub with test data
            :rtype: EsiOperationStub
            :raises AttributeError: If endpoints were provided and this method is not registered
            """
            # Check if endpoint is registered
            endpoint = self._endpoints.get(method_name)

            # Only registered methods are allowed
            if endpoint is None:
                raise AttributeError(
                    f"Method '{self._category_name}.{method_name}' is not registered. "
                    f"Available methods: {list(self._endpoints.keys())}"
                )

            # Look up test data for this method
            method_data = self._test_data.get(method_name, {})

            # print(f"DEBUG: EsiCategoryStub: method_data for {self._category_name}.{method_name}: {method_data}")
            data = _select_method_data(method_data, kwargs, endpoint)
            # print(f"DEBUG: EsiCategoryStub: selected data for {self._category_name}.{method_name}: {data}")

            # Get side effect from endpoint if defined
            side_effect = endpoint.side_effect if endpoint else None

            return EsiOperationStub(test_data=data, side_effect=side_effect)

        return operation_caller


class EsiClientStub:
    """
    Stub for ESI OpenAPI client that mimics ESIClientProvider.client.

    This class provides access to ESI categories and their methods,
    returning test data instead of making real API calls.
    """

    def __init__(
        self,
        test_data_config: dict[str, dict[str, Any]],
        endpoints: list[EsiEndpoint],
    ):
        """
        Initialize the ESI client stub.

        Args:
            test_data_config (dict[str, dict[str, Any]]): Test data configuration
                Format: {"CategoryName": {"MethodName": test_data}}
            endpoints (list[EsiEndpoint]): List of endpoint definitions (REQUIRED)
        Raises:
            ValueError: If endpoints is None or empty
        """
        if not endpoints:
            raise ValueError(
                "endpoints parameter is required and cannot be empty. "
                "You must provide a list of EsiEndpoint definitions."
            )

        self._test_data_config = test_data_config
        self._categories = {}
        self._endpoints_by_category = {}

        # Build endpoint lookup by category and method
        for endpoint in endpoints:
            if endpoint.category not in self._endpoints_by_category:
                self._endpoints_by_category[endpoint.category] = {}
            self._endpoints_by_category[endpoint.category][endpoint.method] = endpoint

        # Create category stubs only for categories that have registered endpoints
        for category_name in self._endpoints_by_category.keys():
            methods_data = test_data_config.get(category_name, {})
            category_endpoints = self._endpoints_by_category[category_name]
            self._categories[category_name] = EsiCategoryStub(
                category_name=category_name,
                test_data=methods_data,
                endpoints=category_endpoints,
            )

    def __getattr__(self, category_name: str) -> EsiCategoryStub:
        """
        Return the category stub for the requested ESI category.

        Args:
            category_name (str): Name of the ESI category
        Returns:
            EsiCategoryStub: The category stub
        Raises:
            AttributeError: If category is not registered in endpoints
        """
        if category_name in self._categories:
            return self._categories[category_name]

        # Only registered categories are allowed
        raise AttributeError(
            f"Category '{category_name}' is not registered. "
            f"Available categories: {list(self._categories.keys())}"
        )


def load_test_data_from_json(file_name: str = "esi_test_data.json") -> dict:
    """
    Load test data from a JSON file in the testdata directory.

    Args:
        file_name (str): Name of the JSON file (default: "esi_test_data.json")

    Returns:
        dict: Loaded test data
    """
    file_path = Path(__file__).parent / file_name

    if not file_path.exists():
        return {}

    with file_path.open("r", encoding="utf-8") as fp:
        return json.load(fp)


def create_esi_client_stub(
    test_data_config: dict[str, dict[str, Any]] | None = None,
    endpoints: list[EsiEndpoint] | None = None,
) -> EsiClientStub:
    """
    Create an ESI client stub with the provided test data configuration.
    This function can be used in tests to provide a stub ESI client.

    Args:
        test_data_config (dict[str, dict[str, Any]] | None): Test data configuration, if None loads from JSON file
        endpoints (list[EsiEndpoint] | None): List of endpoint definitions (REQUIRED)

    Returns:
        EsiClientStub: ESI client stub

    Raises:
        ValueError: If endpoints is None or empty
    """
    if test_data_config is None:
        test_data_config = load_test_data_from_json()

    if not endpoints:
        raise ValueError(
            "endpoints parameter is required. "
            "You must provide a list of EsiEndpoint definitions."
        )

    return EsiClientStub(test_data_config=test_data_config, endpoints=endpoints)
