#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# ================================================================================================ #
# Project    : AppStoreStream: Apple App Data and Reviews, Delivered!                              #
# Version    : 0.1.0                                                                               #
# Python     : 3.10.14                                                                             #
# Filename   : /appstorestream/infra/web/asession.py                                               #
# ------------------------------------------------------------------------------------------------ #
# Author     : John James                                                                          #
# Email      : john@variancexplained.com                                                           #
# URL        : https://github.com/variancexplained/appstore-stream.git                             #
# ------------------------------------------------------------------------------------------------ #
# Created    : Friday July 19th 2024 04:42:55 am                                                   #
# Modified   : Sunday July 28th 2024 05:23:00 pm                                                   #
# ------------------------------------------------------------------------------------------------ #
# License    : MIT License                                                                         #
# Copyright  : (c) 2024 John James                                                                 #
# ================================================================================================ #
import asyncio
import logging
import os
import random
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Optional

import aiohttp

from appstorestream.application.appdata.response import AppDataAsyncResponse
from appstorestream.application.base.response import (AsyncRequest,
                                                      AsyncResponse,
                                                      ResponseError)
from appstorestream.infra.web.throttle import AThrottle


# ------------------------------------------------------------------------------------------------ #
#                                         ASESSION                                                 #
# ------------------------------------------------------------------------------------------------ #
class ASession(ABC):
    """Base class for asynchronous HTTP sessions and requests

    Args:
        throttle (AThrottle): Throttling mechanism to control request rate.
        max_concurrency (int): Maximum number of concurrent requests.
        retries (int): Number of retries if a request fails.
        timeout (int): Timeout for requests in seconds.
    """

    def __init__(
        self,
        throttle: AThrottle,
        max_concurrency: int = 100,
        retries: int = 3,
        timeout: int = 30,
    ) -> None:
        self._throttle = throttle
        self._max_concurrency = max(max_concurrency, throttle.max_rate)
        self._retries = retries
        self._timeout = timeout
        self._timeout_obj = aiohttp.ClientTimeout(total=timeout)

        self._proxy = self._config.config.proxy

        self._logger = logging.getLogger(f"{self.__class__.__name__}")

    @abstractmethod
    async def get(self, request: AsyncRequest) -> AsyncResponse:
        """Formats and executes asynchronous get commands.

        Args:
            request (AsyncRequest): An Asyncronous HTTP Request
        """

    def as_dict(self) -> dict:
        return {"throttle": self._throttle.as_dict(), "max_concurrency": self._max_concurrency, "retries": self._retries, "timeout": self._timeout}

    async def make_request(
        self,
        client: aiohttp.ClientSession,
        url: str,
        concurrency: asyncio.Semaphore,
        params: Optional[Dict] = None,
    ) -> Dict[str, any]:
        """Executes the HTTP request and returns a JSON response.

        Args:
            client (aiohttp.ClientSession): The HTTP client executing the request.
            url (str): The base URL for the HTTP request.
            concurrency (asyncio.Semaphore): Controls the number of concurrent requests.
            params (Optional[Dict]): URL parameters. Optional.

        Returns:
            Dict[str, any]: The JSON response or an error dictionary.
        """

        retries = 0

        async with concurrency:
            while retries < self._retries:
                try:
                    await self._throttle.send()
                    self._metrics_svc.increment_requests_total()

                    async with client.get(
                        url, proxy=self._proxy, ssl=False, params=params
                    ) as response:
                        await self._throttle.recv()
                        await self._throttle.delay()
                        response.raise_for_status()
                        self._metrics_svc.increment_requests_successful_total()
                        return await response.json()

                except aiohttp.ClientResponseError as e:
                    if 400 <= e.status < 500:
                        self._logger.warning(
                            f"ClientResponseError: Response code: {e.status} - {e}. Retry #{retries}."
                        )

                    elif 500 <= e.status < 600:
                        self._logger.warning(
                            f"ServerResponseError: Response code: {e.status} - {e}. Retry #{retries}."
                        )
                    else:
                        self._logger.warning(
                            f"UnexpectedResponseError: Response code: {e.status} - {e}. Retry #{retries}."
                        )

                except aiohttp.ClientError as e:
                    self._logger.warning(
                        f"ClientError: {e}. Retry #{retries}."
                    )

                except Exception as e:
                    self._logger.warning(
                        f"Unknown Error: {e}. Retry #{retries}."
                    )

                retries += 1
                await asyncio.sleep(2**retries)  # Exponential backoff

            self._logger.error("Exhausted retries. Returning to calling environment.")
            error = ResponseError(return_code=e.status)
            return {"error": error}

    def _get_proxy(self) -> dict:
        dns = os.getenv("WEBSHARE_DNS")
        username = os.getenv("WEBSHARE_USER")
        pwd = os.getenv("WEBSHARE_PWD")
        port = os.getenv("WEBSHARE_PORT")
        proxy = f"http://{username}:{pwd}@{dns}:{port}"
        return proxy


# ------------------------------------------------------------------------------------------------ #
#                                      ASESSION APPDATA                                            #
# ------------------------------------------------------------------------------------------------ #
class ASessionAppData(ASession):
    """Asynchronous Session Handling and HTTP Request for App Data

    Args:
        url (str): The base url
        param_list (list): List of parameter dictionaries.
        headers (dict): Header dictionary. Optional
    """

    async def get(self, request: AsyncRequest) -> AsyncResponse:
        """Formats and executes asynchronous get commands.

        Args:
            request (AsyncRequest): An Asyncronous HTTP Request
        """

        conn = aiohttp.TCPConnector()

        concurrency = asyncio.Semaphore(self._max_concurrency)

        response = AppDataAsyncResponse()
        response.send()

        async with aiohttp.ClientSession(
            headers=request.header,
            connector=conn,
            trust_env=True,
            raise_for_status=True,
            timeout=self._timeout_obj,
        ) as client:

            tasks = [
                self._make_request(
                    client=client,
                    url=request.baseurl,
                    params=param_dict,
                    concurrency=concurrency,
                )
                for param_dict in request.param_list
            ]
            results = await asyncio.gather(*tasks)
            response.recv(results=results)
            response.request_count = len(tasks)
            return response

# ------------------------------------------------------------------------------------------------ #
#                                      ASESSION REVIEW                                             #
# ------------------------------------------------------------------------------------------------ #
class ASessionReview(ASession):
    @abstractmethod
    async def get(self, request: AsyncRequest) -> AsyncResponse:
        """Formats and executes asyncronous get commands.

        Args:
            request (AsyncRequest): An Asyncronous HTTP Request
        """

        conn = aiohttp.TCPConnector()

        concurrency = asyncio.Semaphore(self._max_concurrency)

        response = AppDataAsyncResponse()
        response.send()

        async with aiohttp.ClientSession(
            headers=request.header,
            connector=conn,
            trust_env=True,
            raise_for_status=True,
            timeout=self._timeout_obj,
        ) as client:
            tasks = [
                self._make_request(client=client, url=url, concurrency=concurrency)
                for url in request.urls
            ]
            results = await asyncio.gather(*tasks)
            response.recv(results=results)
            response.request_count = len(tasks)
            return response

