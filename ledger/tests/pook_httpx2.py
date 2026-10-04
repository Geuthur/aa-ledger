"""Pook interceptor for httpx2 support.

httpx2 is a modern fork/successor of httpx used by newer aiopenapi3 / allianceauth versions.
Since pook currently only has built-in interceptors for httpx, urllib3, aiohttp, and http.client,
this module registers an interceptor for httpx2 if both pook and httpx2 are installed.
"""

# Standard Library
import asyncio
import typing as t
from http.client import responses as http_reasons
from unittest import mock

try:
    # Third Party
    import httpx2
    import pook
    from pook.interceptors.base import BaseInterceptor
    from pook.request import Request
    from pook.response import Response

    PATCHES = (
        "httpx2.Client._transport_for_url",
        "httpx2.AsyncClient._transport_for_url",
    )

    Httpx2Client = t.Union[httpx2.Client, httpx2.AsyncClient]

    class MockedTransport2(httpx2.BaseTransport):
        """Mock transport for httpx2 requests."""

        def __init__(
            self,
            interceptor: "Httpx2Interceptor",
            client: Httpx2Client,
            original_transport_for_url: t.Callable,
        ):
            self._interceptor = interceptor
            self._client = client
            self._original_transport_for_url = original_transport_for_url

        def _get_pook_request(self, httpx_request: httpx2.Request) -> Request:
            req = Request(httpx_request.method)
            req.url = str(httpx_request.url)
            req.headers = dict(httpx_request.headers)
            return req

        def _get_httpx_response(
            self, httpx_request: httpx2.Request, mock_response: Response
        ) -> httpx2.Response:
            res = httpx2.Response(
                status_code=mock_response._status,
                headers=mock_response._headers,
                content=mock_response._body,
                extensions={
                    "http_version": b"HTTP/1.1",
                    "reason_phrase": http_reasons.get(mock_response._status, "").encode(
                        "ascii"
                    ),
                    "network_stream": None,
                },
                request=httpx_request,
            )
            res.is_stream_consumed = False
            res.is_closed = False
            if hasattr(res, "_content"):
                del res._content
            return res

    class SyncTransport2(MockedTransport2):
        """Synchronous mock transport for httpx2."""

        def _get_pook_request(self, httpx_request: httpx2.Request) -> Request:
            req = super()._get_pook_request(httpx_request)
            req.body = httpx_request.read()
            return req

        def handle_request(self, request: httpx2.Request) -> httpx2.Response:
            pook_request = self._get_pook_request(request)
            mock_match = self._interceptor.engine.match(pook_request)
            if not mock_match:
                transport = self._original_transport_for_url(self._client, request.url)
                return transport.handle_request(request)
            return self._get_httpx_response(request, mock_match._response)

    class AsyncTransport2(MockedTransport2):
        """Asynchronous mock transport for httpx2."""

        async def _get_pook_request(self, httpx_request: httpx2.Request) -> Request:
            req = super()._get_pook_request(httpx_request)
            req.body = await httpx_request.aread()
            return req

        async def handle_async_request(
            self, request: httpx2.Request
        ) -> httpx2.Response:
            pook_request = await self._get_pook_request(request)
            mock_match = self._interceptor.engine.match(pook_request)
            if not mock_match:
                transport = self._original_transport_for_url(self._client, request.url)
                return await transport.handle_async_request(request)
            if mock_match._delay:
                await asyncio.sleep(mock_match._delay / 1000)
            return self._get_httpx_response(request, mock_match._response)

    class Httpx2Interceptor(BaseInterceptor):
        """pook interceptor for httpx2."""

        def _patch(self, path: str) -> None:
            if "AsyncClient" in path:
                transport_cls = AsyncTransport2
            else:
                transport_cls = SyncTransport2

            def handler(client, *_):
                return transport_cls(self, client, original_transport_for_url)

            try:
                patcher = mock.patch(path, handler)
                original_transport_for_url = patcher.get_original()[0]
                patcher.start()
            except Exception:  # pylint: disable=broad-exception-caught
                pass
            else:
                self.patchers.append(patcher)

        def activate(self) -> None:
            for path in PATCHES:
                self._patch(path)

        def disable(self) -> None:
            for patcher in self.patchers:
                patcher.stop()

    if Httpx2Interceptor not in pook.interceptors.interceptors:
        pook.interceptors.add(Httpx2Interceptor)

    engine_interceptors = pook.engine().mock_engine.interceptors
    if not any(isinstance(i, Httpx2Interceptor) for i in engine_interceptors):
        engine_interceptors.append(Httpx2Interceptor(pook.engine().mock_engine.engine))

except ImportError:
    pass
