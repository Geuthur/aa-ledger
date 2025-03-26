"""
Etag Helpers
"""

import logging

from bravado.exception import HTTPGatewayTimeout, HTTPNotModified

from django.core.cache import cache

from ledger.decorators import log_timing

logger = logging.getLogger(__name__)

MAX_ETAG_LIFE = 60 * 60 * 24 * 7  # 7 Days


class NotModifiedError(Exception):
    pass


class HTTPGatewayTimeoutError(Exception):
    pass


def get_etag_key(operation):
    """Get ETag Key"""
    return "ledger-" + operation._cache_key()


def get_etag_header(operation):
    """Get Cached ETag"""
    return cache.get(get_etag_key(operation), False)


def del_etag_header(operation):
    """Delete Cached ETag"""
    return cache.delete(get_etag_key(operation), False)


def inject_etag_header(operation):
    """Inject ETag header"""
    etag = get_etag_header(operation)
    logger.debug(
        "ETag: get_etag %s - %s - etag:%s",
        operation.operation.operation_id,
        stringify_params(operation),
        etag,
    )
    if etag:
        operation.future.request.headers["If-None-Match"] = etag


def rem_etag_header(operation):
    """Remove ETag header"""
    logger.debug(
        "ETag: rem_etag %s - %s",
        operation.operation.operation_id,
        stringify_params(operation),
    )
    if "If-None-Match" in operation.future.request.headers:
        del operation.future.request.headers["If-None-Match"]
        return True
    return False


def set_etag_header(operation, headers):
    """Set ETag header"""
    etag_key = get_etag_key(operation)
    etag = headers.headers.get("ETag", None)
    if etag is not None:
        result = cache.set(etag_key, etag, MAX_ETAG_LIFE)
        logger.debug(
            "ETag: set_etag %s - %s - etag: %s - stored: %s",
            operation.operation.operation_id,
            stringify_params(operation),
            etag,
            result,
        )
        return True
    return False


def stringify_params(operation):
    """Stringify Operation Params"""
    out = []
    for p, v in operation.future.request.params.items():
        out.append(f"{p}: {v}")
    return ", ".join(out)


def handle_etag_headers(operation, headers, force_refresh, etags_incomplete):
    if (
        get_etag_header(operation) == headers.headers.get("ETag")
        and not force_refresh
        and not etags_incomplete
    ):
        # Etag Match Cache Check
        raise NotModifiedError()

    if force_refresh:
        # Remove Etag if force_refresh
        logger.debug(
            "ETag: Removing Etag %s F:%s - %s",
            operation.operation.operation_id,
            force_refresh,
            stringify_params(operation),
        )
        del_etag_header(operation)
    else:
        # Save Etag
        logger.debug(
            "ETag: Saving Etag %s F:%s - %s",
            operation.operation.operation_id,
            force_refresh,
            stringify_params(operation),
        )
        set_etag_header(operation, headers)


def handle_page_results(
    operation, current_page, total_pages, etags_incomplete, force_refresh
):
    results = []
    while current_page <= total_pages:
        operation.future.request.params["page"] = current_page
        try:
            if not etags_incomplete and not force_refresh:
                inject_etag_header(operation)
            else:
                rem_etag_header(operation)

            result, headers = operation.result()
            total_pages = int(headers.headers["X-Pages"])
            handle_etag_headers(operation, headers, force_refresh, etags_incomplete)

            # Store results
            results += result
            current_page += 1

            if not etags_incomplete and not force_refresh:
                logger.debug(
                    "ETag: No Etag %s - %s",
                    operation.operation.operation_id,
                    stringify_params(operation),
                )
                current_page = 1
                results = []
                etags_incomplete = True

        except (HTTPNotModified, NotModifiedError) as e:
            if isinstance(e, NotModifiedError):
                logger.debug(
                    "ETag: Match Cache - Etag:%s, %s",
                    operation.operation.operation_id,
                    stringify_params(operation),
                )
                total_pages = int(headers.headers["X-Pages"])
            else:
                logger.debug(
                    "ETag: Match ESI - Etag: %s - %s ETag-Incomplete: %s",
                    operation.operation.operation_id,
                    stringify_params(operation),
                    etags_incomplete,
                )
                total_pages = int(e.response.headers["X-Pages"])

            if not etags_incomplete:
                current_page += 1
            else:
                current_page = 1
                results = []
                etags_incomplete = False

    if not etags_incomplete and not force_refresh:
        raise NotModifiedError()

    return results, current_page, total_pages


@log_timing(logger)
def etag_results(operation, token, force_refresh=False):
    """Handle ETag results"""
    operation.request_config.also_return_response = True
    if token:
        operation.future.request.headers["Authorization"] = (
            "Bearer " + token.valid_access_token()
        )
    if "page" in operation.operation.params:
        current_page = 1
        total_pages = 1
        etags_incomplete = False

        results, current_page, total_pages = handle_page_results(
            operation, current_page, total_pages, etags_incomplete, force_refresh
        )
    else:
        if not force_refresh:
            inject_etag_header(operation)
        try:
            results, headers = operation.result()
        except HTTPNotModified as e:
            logger.debug("ETag: Not Modified %s", operation.operation.operation_id)
            set_etag_header(operation, e.response)
            raise NotModifiedError() from e
        except HTTPGatewayTimeout as e:
            logger.debug("ETag: Gateway Timeout %s", operation.operation.operation_id)
            raise HTTPGatewayTimeoutError() from e
        handle_etag_headers(operation, headers, force_refresh, etags_incomplete=False)
    return results
