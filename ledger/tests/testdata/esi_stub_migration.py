# Standard Library
from types import SimpleNamespace
from typing import Any

# Django
from django.utils import timezone

# Alliance Auth (External Libs)
from app_utils.esi_testing import (
    BravadoOperationStub,
    EsiClientStub,
    EsiEndpoint,
    _EsiMethod,
    parse_datetime,
)


class EsiEndpoint(EsiEndpoint):
    def __init__(self, *args, return_response=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.return_response = return_response


class _EsiMethodOpenApi(_EsiMethod):
    """An ESI method that can be called from the ESI client using OpenAPI client."""

    @staticmethod
    def _convert_values(data) -> Any:
        def convert_dict(item):
            if isinstance(item, dict):
                for key, value in item.items():
                    if isinstance(value, str):
                        try:
                            if parsed_datetime := parse_datetime(value):
                                item[key] = parsed_datetime.replace(tzinfo=timezone.utc)
                        except ValueError:
                            pass

        def dict_to_obj(obj):
            if isinstance(obj, dict):
                return SimpleNamespace(**{k: dict_to_obj(v) for k, v in obj.items()})
            elif isinstance(obj, list):
                return [dict_to_obj(i) for i in obj]
            else:
                return obj

        if isinstance(data, list):
            for row in data:
                convert_dict(row)
        else:
            convert_dict(data)

        return dict_to_obj(data)

    def call(self, **kwargs):
        result_obj = super().call(**kwargs)
        if self._endpoint.return_response:
            return BravadoOperationStub(result_obj.result(), also_return_response=True)
        return result_obj


class EsiClientStubOpenApi(EsiClientStub):
    """ESI Client Stub that uses OpenAPI generated client."""

    def _add_endpoint(self, endpoint: EsiEndpoint):
        if not hasattr(self, endpoint.category):
            setattr(self, endpoint.category, type(endpoint.category, (object,), {}))
        endpoint_category = getattr(self, endpoint.category)
        if not hasattr(endpoint_category, endpoint.method):
            setattr(
                endpoint_category,
                endpoint.method,
                _EsiMethodOpenApi(
                    endpoint=endpoint,
                    testdata=self._testdata,
                    http_error=self._http_error,
                ).call,
            )
        else:
            raise ValueError(f"Endpoint for {endpoint} already defined!")
