#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# ================================================================================================ #
# Project    : AppStoreStream: Apple App Data and Reviews, Delivered!                              #
# Version    : 0.1.0                                                                               #
# Python     : 3.10.14                                                                             #
# Filename   : /appstorestream/core/enum.py                                                        #
# ------------------------------------------------------------------------------------------------ #
# Author     : John James                                                                          #
# Email      : john@variancexplained.com                                                           #
# URL        : https://github.com/variancexplained/appstore-stream.git                             #
# ------------------------------------------------------------------------------------------------ #
# Created    : Monday July 22nd 2024 10:19:32 pm                                                   #
# Modified   : Sunday July 28th 2024 07:49:55 pm                                                   #
# ------------------------------------------------------------------------------------------------ #
# License    : MIT License                                                                         #
# Copyright  : (c) 2024 John James                                                                 #
# ================================================================================================ #
from enum import Enum


# ------------------------------------------------------------------------------------------------ #
class JobStatus(Enum):
    CREATED = "CREATED"
    SCHEDULED = "SCHEDULED"
    IN_PROGRESS = "IN PROGRESS"
    COMPLETE = "COMPLETE"
    TERMINATED = "TERMINATED"
    CANCELLED = "CANCELLED"

class ProjectStatus(Enum):
    NOT_STARTED = "NOT_STARTED"
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    PAUSED = "PAUSED"
    CANCELLED = "CANCELLED"

class ProjectPriority(Enum):
    HIGH: 1
    MEDIUM_HIGH: 2
    MEDIUM: 3
    MEDIUM_LOW: 4
    LOW: 5

class Dataset(Enum):
    APPDATA="APPDATA"
    REVIEW="REVIEW"

class ErrorType(Enum):
    CLIENT="CLIENT"
    SERVER="SERVER"
    DATA="DATA"

class CircuitBreakerStates:
    CLOSED="CLOSED"
    OPEN="OPEN"
    HALF_OPEN="HALF_OPEN"
    TERMINATED="TERMINATED"
    COMPLETE="COMPLETE"