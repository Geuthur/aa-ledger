"""
Etag Helpers
"""

import time

from bravado.exception import HTTPNotModified

from django.core.cache import cache

from ledger.hooks import get_extension_logger

logger = get_extension_logger(__name__)

MAX_ETAG_LIFE = 60 * 60 * 24 * 7  # 7 Days


class NotModifiedError(Exception):
    pass


def get_etag_key(operation):
    return "etag-" + operation._cache_key()


def get_etag_header(operation):
    return cache.get(get_etag_key(operation), False)


def del_etag_header(operation):
    return cache.delete(get_etag_key(operation), False)


def inject_etag_header(operation):
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
    logger.debug(
        "ETag: rem_etag %s - %s",
        operation.operation.operation_id,
        stringify_params(operation),
    )
    if "If-None-Match" in operation.future.request.headers:
        del operation.future.request.headers["If-None-Match"]


def set_etag_header(operation, headers):
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


def stringify_params(operation):
    out = []
    for p, v in operation.future.request.params.items():
        out.append(f"{p}: {v}")
    return ", ".join(out)


# pylint: disable=too-many-statements, too-many-branches
def etag_results(operation, token, force_refresh=False):
    _start_tm = time.perf_counter()
    results = []
    # override to always get the raw response for expiry header
    operation.request_config.also_return_response = True
    if token:
        operation.future.request.headers["Authorization"] = (
            "Bearer " + token.valid_access_token()
        )
    if "page" in operation.operation.params:
        logger.debug(
            "ETag: Pages Start %s - %s",
            operation.operation.operation_id,
            stringify_params(operation),
        )
        current_page = 1
        total_pages = 1
        etags_incomplete = False

        # loop all pages and add data to output array
        while current_page <= total_pages:
            _pg_tm = time.perf_counter()
            operation.future.request.params["page"] = current_page
            # will use cache if applicable
            try:
                if not etags_incomplete and not force_refresh:
                    logger.debug(
                        "ETag: Injecting Header %s - %s",
                        operation.operation.operation_id,
                        stringify_params(operation),
                    )
                    inject_etag_header(operation)
                else:
                    logger.debug(
                        "ETag: Removing Header %s F: %s Ei: %s - %s",
                        operation.operation.operation_id,
                        force_refresh,
                        etags_incomplete,
                        stringify_params(operation),
                    )
                    rem_etag_header(operation)

                result, headers = operation.result()
                total_pages = int(headers.headers["X-Pages"])

                if (
                    get_etag_header(operation) == headers.headers.get("ETag")
                    and not force_refresh
                    and not etags_incomplete
                ):
                    # if django esi is returning our cache check it manualy.
                    raise NotModifiedError()

                if force_refresh:
                    logger.debug(
                        "ETag: Removing Etag %s F:%s - %s",
                        operation.operation.operation_id,
                        force_refresh,
                        stringify_params(operation),
                    )
                    del_etag_header(operation)
                else:
                    logger.debug(
                        "ETag: Saving Etag %s F:%s - %s",
                        operation.operation.operation_id,
                        force_refresh,
                        stringify_params(operation),
                    )
                    set_etag_header(operation, headers)

                # append to results list to be seamless to the client
                results += result
                current_page += 1

                if not etags_incomplete and not force_refresh:
                    logger.debug(
                        "ETag: No Etag %s - %s",
                        operation.operation.operation_id,
                        stringify_params(operation),
                    )
                    current_page = 1  # reset to page 1 and fetch everything
                    results = []
                    etags_incomplete = True

            except HTTPNotModified as e:  # etag is match from ESI
                logger.debug(
                    "ETag: HTTPNotModified Hit ETag %s Ei:%s - %s - P:%s",
                    operation.operation.operation_id,
                    etags_incomplete,
                    stringify_params(operation),
                    e.response.headers["X-Pages"],
                )
                total_pages = int(e.response.headers["X-Pages"])

                if not etags_incomplete:
                    current_page += 1
                else:
                    current_page = 1  # reset to page 1 and fetch everything, we should not get here
                    results = []

            except NotModifiedError:  # etag is match in cache
                logger.debug(
                    "ESI_TIME: PAGE %s %s %s",
                    time.perf_counter() - _pg_tm,
                    operation.operation.operation_id,
                    stringify_params(operation),
                )
                total_pages = int(headers.headers["X-Pages"])

                if not etags_incomplete:
                    current_page += 1
                else:
                    current_page = 1  # reset to page 1 and fetch everything, we should not get here
                    results = []
            logger.debug(
                "ETag: No Etag %s - %s",
                operation.operation.operation_id,
                stringify_params(operation),
            )
        if not etags_incomplete and not force_refresh:
            raise NotModifiedError()

    else:  # it doesn't so just return as usual
        if not force_refresh:
            inject_etag_header(operation)
        try:
            results, headers = operation.result()
        except HTTPNotModified as e:
            logger.debug(
                "ETag: HTTPNotModified Hit ETag %s - %s",
                operation.operation.operation_id,
                stringify_params(operation),
            )
            set_etag_header(operation, e.response)
            raise NotModifiedError() from e

        if (
            get_etag_header(operation) == headers.headers.get("ETag")
            and not force_refresh
        ):
            # etag is match in cache
            logger.debug(
                "ETag: result Cache Hit ETag %s - %s",
                operation.operation.operation_id,
                stringify_params(operation),
            )
            set_etag_header(operation, headers)
            raise NotModifiedError()

        if force_refresh:
            logger.debug(
                "ETag: Removing Etag %s F:%s - %s",
                operation.operation.operation_id,
                force_refresh,
                stringify_params(operation),
            )
            del_etag_header(operation)
        else:
            logger.debug(
                "ETag: Saving Etag %s F:%s - %s",
                operation.operation.operation_id,
                force_refresh,
                stringify_params(operation),
            )
            set_etag_header(operation, headers)
    logger.debug(
        "ESI_TIME: OVERALL %s %s %s",
        time.perf_counter() - _start_tm,
        operation.operation.operation_id,
        stringify_params(operation),
    )
    return results
