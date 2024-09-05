#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# ================================================================================================ #
# Project    : AppVoCAI-Acquire                                                                    #
# Version    : 0.2.0                                                                               #
# Python     : 3.10.14                                                                             #
# Filename   : /appvocai/container.py                                                              #
# ------------------------------------------------------------------------------------------------ #
# Author     : John James                                                                          #
# Email      : john@variancexplained.com                                                           #
# URL        : https://github.com/variancexplained/appvocai-acquire                                #
# ------------------------------------------------------------------------------------------------ #
# Created    : Thursday July 25th 2024 04:17:11 am                                                 #
# Modified   : Thursday September 5th 2024 04:57:03 am                                             #
# ------------------------------------------------------------------------------------------------ #
# License    : MIT License                                                                         #
# Copyright  : (c) 2024 John James                                                                 #
# ================================================================================================ #
"""Framework Dependency Container"""
# import logging
# import logging.config  # pragma: no cover

# import aiohttp
# from dependency_injector import containers, providers

# from appvocai.core.enum import DataType
# from appvocai.infra.base.config import Config
# from appvocai.infra.database.mysql import MySQLDatabase
# from appvocai.infra.observer.extract import ObserverASessionMetrics
# from appvocai.infra.observer.load import ObserverLoadMetrics
# from appvocai.infra.observer.transform import ObserverTransformMetrics
# from appvocai.infra.web.adapter import (
#     AdapterBaselineStage,
#     AdapterConcurrencyExploreStage,
#     AdapterExploitStage,
#     AdapterRateExploreStage,
# )

# # from appvocai.infra.web.asession import ASession
# from appvocai.infra.web.profile import SessionHistory


# # ------------------------------------------------------------------------------------------------ #
# #                                        LOGGING                                                   #
# # ------------------------------------------------------------------------------------------------ #
# class LoggingContainer(containers.DeclarativeContainer):
#     config = providers.Configuration()

#     logging = providers.Resource(
#         logging.config.dictConfig,
#         config=config.logging,
#     )


# # ------------------------------------------------------------------------------------------------ #
# #                                      PERSISTENCE                                                 #
# # ------------------------------------------------------------------------------------------------ #
# class PersistenceContainer(containers.DeclarativeContainer):

#     mysql = providers.Singleton(MySQLDatabase)


# # ------------------------------------------------------------------------------------------------ #
# #                                 EXTRACTOR CONTAINER                                              #
# # ------------------------------------------------------------------------------------------------ #
# class ASessionContainer(containers.DeclarativeContainer):

#     config = providers.Configuration()

#     # Dummy cookie jar which does not store cookies but ignores them.
#     # An aiohttp.ClientSession dependency.
#     cookie_jar = providers.Singleton(aiohttp.DummyCookieJar)

#     # Connector for working with HTTP and HTTPS via TCP sockets.
#     connector = providers.Singleton(
#         aiohttp.TCPConnector,
#         use_dns_cache=config.asession.connector.use_dns_cache,
#         ttl_dns_cache=config.asession.connector.ttl_dns_cache,
#         limit=config.asession.connector.limit,
#         limit_per_host=config.asession.connector.limit_per_host,
#         enable_cleanup_closed=config.asession.connector.enable_cleanup_closed,
#         keepalive_timeout=config.asession.connector.keepalive_timeout,
#         force_close=config.asession.connector.force_close,
#         happy_eyeballs_delay=config.asession.connector.happy_eyeballs_delay,
#     )

#     # Controls the adapter metrics and statistics history
#     history = providers.Singleton(SessionHistory, max_history=config.adapter.history)

#     # The four rate and concurrency adapter stages are defined here.
#     # 1. Baseline adapter stage: Gathers baseline statistics
#     adapter_baseline_stage = providers.Singleton(
#         AdapterBaselineStage, config=config.adapter.baseline
#     )

#     # 2. Rate Explore Stage: Optimizes request rate given baseline statistics
#     adapter_explore_rate_stage = providers.Singleton(
#         AdapterRateExploreStage, config=config.adapter.explore_rate
#     )

#     # 3. Explore Concurrency: Tunes concurrency to current performance
#     adapter_explore_concurrency_stage = providers.Singleton(
#         AdapterConcurrencyExploreStage, config=config.adapter.explore_concurrency
#     )

#     # 4. Exploit Stage: Adjusts request rate based on conditions
#     adaptor_exploit_stage = providers.Singleton(
#         AdapterExploitStage, config=config.adapter.exploit
#     )


# # ------------------------------------------------------------------------------------------------ #
# #                                   METRICS OBSERVERS                                              #
# # ------------------------------------------------------------------------------------------------ #
# class ObserverContainer(containers.DeclarativeContainer):

#     asession_observer = providers.Singleton(
#         ObserverASessionMetrics, data_type=DataType.APPDATA
#     )
#     transform_observer = providers.Singleton(
#         ObserverTransformMetrics, data_type=DataType.APPDATA
#     )
#     load_observer = providers.Singleton(ObserverLoadMetrics, data_type=DataType.APPDATA)


# # ------------------------------------------------------------------------------------------------ #
# #                                       FRAMEWORK                                                  #
# # ------------------------------------------------------------------------------------------------ #
# class AppVoCAIContainer(containers.DeclarativeContainer):

#     config_filepath = Config().filepath

#     config = providers.Configuration(yaml_files=[config_filepath])

#     logs = providers.Container(LoggingContainer, config=config)

#     db = providers.Container(PersistenceContainer)

#     asession = providers.Container(ASessionContainer)
