#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# ================================================================================================ #
# Project    : AppVoCAI-Acquire                                                                    #
# Version    : 0.2.0                                                                               #
# Python     : 3.10.14                                                                             #
# Filename   : /appvocai/infra/database/mysql.py                                                   #
# ------------------------------------------------------------------------------------------------ #
# Author     : John James                                                                          #
# Email      : john@variancexplained.com                                                           #
# URL        : https://github.com/variancexplained/appvocai-acquire                                #
# ------------------------------------------------------------------------------------------------ #
# Created    : Friday July 19th 2024 07:14:52 am                                                   #
# Modified   : Thursday August 29th 2024 07:47:43 pm                                               #
# ------------------------------------------------------------------------------------------------ #
# License    : MIT License                                                                         #
# Copyright  : (c) 2024 John James                                                                 #
# ================================================================================================ #
"""MySQL Database Module"""
from __future__ import annotations

import getpass
import logging
import os
import subprocess
from time import sleep
from typing import Type

import sqlalchemy
from dotenv import load_dotenv
from sqlalchemy.exc import SQLAlchemyError

from appvocai.core.data import NestedNamespace
from appvocai.infra.base.config import Config
from appvocai.infra.database.base import DBA, Database

# ------------------------------------------------------------------------------------------------ #
load_dotenv()


# ------------------------------------------------------------------------------------------------ #
#                            MYSQL DATABASE BUILDER                                                #
# ------------------------------------------------------------------------------------------------ #
class MySQLDatabase(Database):
    """MySQL Database Class
    Args:
        config_cls (Type[Config]): System configuration class.
    """

    __dbname = "appvocai"

    def __init__(self, config_cls: Type[Config] = Config) -> None:
        self._config = config_cls()

        self._dbname = f"{self.__dbname}_{self._config.get_environment()}"
        self._mysql_credentials = self._config.mysql
        self._connection_string = self._get_connection_string()
        self._engine = None
        self._connection = None
        self._is_connected = False
        super().__init__(connection_string=self._connection_string)

    def begin(self) -> None:
        """Begin a new MySQL database transaction."""
        # MySQL-specific transaction management could go here
        super().begin()  # Call the base method if needed

    def connect(self, autocommit: bool = False) -> MySQLDatabase:
        attempts = 0
        retries = self._config.database.retries if isinstance(self._config.database, NestedNamespace) else self._config.database['retries']

        while attempts < retries:
            attempts += 1
            try:
                if self._engine is None:
                    self._engine = sqlalchemy.create_engine(self._connection_string)
                if self._connection is None:
                    self._connection = self._engine.connect()

                if autocommit:
                    self._connection.execution_options(isolation_level="AUTOCOMMIT")
                else:
                    self._connection.execution_options(isolation_level="READ COMMITTED")

                self._is_connected = True
                return self

            except SQLAlchemyError as e:
                self._is_connected = False
                if attempts < retries:
                    print("Database connection failed. Attempting to start database..")
                    self._start_db()
                    sleep(3)
                else:
                    msg = f"Database connection failed after {attempts} attempts.\nException type: {type(e)}\n{e}"
                    self._logger.exception(msg)
                    raise
        msg = f"Database connection failed after multiple attempts."
        self._logger.exception(msg)
        raise

    def _get_connection_string(self) -> str:
        """Returns the connection string for the named database."""
        username = self._mysql_credentials.username if isinstance(self._mysql_credentials, NestedNamespace) else self._mysql_credentials["username"]
        password = self._mysql_credentials.password if isinstance(self._mysql_credentials, NestedNamespace) else self._mysql_credentials["password"]
        return f"mysql+pymysql://{username}:{password}@localhost/{self._dbname}"

    def _start_db(self) -> None:
        """Starts the MySQL database."""

        start = self._config.database.start if isinstance(self._config.database, NestedNamespace) else self._config.database["start"]
        subprocess.run([start], shell=True)

    def close(self) -> None:
        """Closes the database connection."""
        if self._connection is not None:
            self._connection.close()
            self._connection = None
        if self._engine is not None:
            self._engine.dispose()
            self._engine = None



# ------------------------------------------------------------------------------------------------ #
#                          MYSQL DATABASE ADMIN                                                    #
# ------------------------------------------------------------------------------------------------ #


class MySQLDBA(DBA):
    """
    A class to handle various database operations for a MySQL database.

    This class can execute DDL files, check for the existence of databases and tables,
    and manage user passwords using the MySQL command line tool.

    Attributes:
        config_cls (Type[Config]): The configuration class used to get database connection info.
        safe_mode (bool): If True, prevents dropping databases in 'prod' environment.

    Methods:
        create_database(dbname: str) -> None: Creates a MySQL database.
        drop_database(dbname: str) -> None: Drops a MySQL database with user confirmation, unless in safe mode.
        database_exists(dbname: str) -> bool: Checks if the specified database exists.
        table_exists(dbname: str, table_name: str) -> bool: Checks if a specific table exists in the specified database.
        create_table(dbname: str, ddl_filepath: str) -> None: Creates a table from a DDL file.
        create_tables(dbname: str, ddl_directory: str) -> None: Creates tables from all DDL files in a directory.
        _run_bash_script(script_filepath: str) -> None: Runs a bash script with sudo privileges.
    """

    def __init__(
        self, config_cls: Type[Config] = Config, safe_mode: bool = True
    ) -> None:
        self._config = config_cls()
        self._mysql_credentials = self._config.mysql
        self._env = self._config.get_environment()
        self._safe_mode = safe_mode
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def create_database(self, dbname: str) -> None:
        """
        Creates a MySQL database.

        Args:
            dbname (str): The name of the database to create.
        """
        dbname = self._format_dbname(dbname)
        query = f"CREATE DATABASE IF NOT EXISTS `{dbname}`;"
        command = self._build_mysql_command(query)
        self._execute_command(command, f"Creating database {dbname}")

    def drop_database(self, dbname: str) -> None:
        """
        Drops a MySQL database with user confirmation, unless in safe mode.

        Args:
            dbname (str): The name of the database to drop.
        """
        if self._safe_mode and self._env == "prod":
            print(
                "Dropping databases is not permitted in safe mode in the 'prod' environment."
            )
            return

        dbname = self._format_dbname(dbname)
        full_dbname = input(
            f"Please enter the full name of the database to drop (e.g., '{dbname}'): "
        ).strip()
        if full_dbname == dbname:
            confirm = (
                input(
                    f"Are you sure you want to drop the database '{dbname}'? Type 'YES' to confirm: "
                )
                .strip()
                .upper()
            )
            if confirm == "YES":
                query = f"DROP DATABASE IF EXISTS `{dbname}`;"
                command = self._build_mysql_command(query)
                self._execute_command(command, f"Dropping database {dbname}")
            else:
                print("Operation cancelled by user.")
        else:
            print(f"Database name '{full_dbname}' does not match expected '{dbname}'.")

    def database_exists(self, dbname: str) -> bool:
        """
        Checks if the specified database exists.

        Args:
            dbname (str): The database name to check for existence.

        Returns:
            bool: True if the database exists, False otherwise.
        """
        dbname = self._format_dbname(dbname)
        query = f"SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = '{dbname}';"
        command = self._build_mysql_command(query)

        try:
            result = subprocess.run(command, check=True, text=True, capture_output=True)
            return dbname in result.stdout
        except subprocess.CalledProcessError as e:
            self._logger.exception(
                f"Command to check database existence failed with error: {e}"
            )
            return False

    def create_table(self, dbname: str, ddl_filepath: str) -> None:
        """
        Creates a table from a DDL file.

        Args:
            dbname (str): The name of the database.
            ddl_filepath (str): The path to the DDL file.
        """
        dbname = self._format_dbname(dbname)
        self._execute_ddl(dbname, ddl_filepath)

    def create_tables(self, dbname: str, ddl_directory: str) -> None:
        """
        Creates tables from all DDL files in a directory.

        Args:
            dbname (str): The name of the database.
            ddl_directory (str): The directory containing DDL files.
        """
        try:
            for file_name in sorted(os.listdir(ddl_directory)):
                if file_name.endswith(".sql"):
                    file_path = os.path.join(ddl_directory, file_name)
                    print(f"Executing {file_path}..")
                    self.create_table(dbname, file_path)
        except FileNotFoundError as e:
            self._logger.exception(f"Directory {ddl_directory} not found.\n{e}")
            raise
        except Exception as e:
            self._logger.exception(f"An unknown error occurred.\n{e}")
            raise

    def table_exists(self, dbname: str, table_name: str) -> bool:
        """
        Checks if a specific table exists in the specified database.

        Args:
            dbname (str): The name of the database to check.
            table_name (str): The name of the table to check for existence.

        Returns:
            bool: True if the table exists, False otherwise.
        """
        dbname = self._format_dbname(dbname)
        query = f"SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = '{dbname}' AND TABLE_NAME = '{table_name}';"
        command = self._build_mysql_command(query)

        try:
            result = subprocess.run(command, check=True, text=True, capture_output=True)
            return table_name in result.stdout
        except subprocess.CalledProcessError as e:
            self._logger.exception(
                f"Command to check table existence failed with error: {e}"
            )
            return False

    def _build_mysql_command(self, query: str) -> list[str]:
        """
        Builds the MySQL command with optional password.

        Args:
            query (str): The SQL query to execute.

        Returns:
            list[str]: The command and arguments to execute.
        """
        host = self._mysql_credentials.host if isinstance(self._mysql_credentials, NestedNamespace) else self._mysql_credentials["host"]
        username = self._mysql_credentials.username if isinstance(self._mysql_credentials, NestedNamespace) else self._mysql_credentials["username"]
        command = [
            "mysql",
            "-h",
            host,
            "-u",
            username,
            "-e",
            query,
        ]
        password = self._mysql_credentials.password if isinstance(self._mysql_credentials, NestedNamespace) else self._mysql_credentials["password"]
        command.insert(3, f"-p{password}")

        return command

    def _execute_command(self, command: list[str], action: str) -> None:
        """
        Executes a MySQL command using subprocess.

        Args:
            command (list[str]): The command to execute.
            action (str): The action being performed (for logging).
        """
        try:
            result = subprocess.run(command, text=True, capture_output=True)
            if result.returncode != 0:
                self._logger.exception(f"Error {action}: {result.stderr}")
            else:
                print(f"Successfully completed {action}")
        except subprocess.CalledProcessError as e:
            self._logger.exception(f"Command {action} failed with error: {e}")

    def _execute_ddl(self, dbname: str, ddl_filepath: str) -> None:
        """
        Executes DDL SQL commands from a file within the specified database.

        Args:
            dbname (str): The name of the database.
            ddl_filepath (str): The path to the DDL file.
        """
        try:
            with open(ddl_filepath, "r") as ddl_file:
                sql_commands = ddl_file.read()

            use_command = f"USE {dbname};"
            full_query = f"{use_command}\n{sql_commands}"
            command = self._build_mysql_command(full_query)
            result = subprocess.run(command, text=True, capture_output=True)

            if result.returncode != 0:
                self._logger.exception(
                    f"Error executing {ddl_filepath}: {result.stderr}"
                )
            else:
                print(f"Successfully executed {ddl_filepath}")

        except FileNotFoundError as e:
            self._logger.exception(f"SQL file {ddl_filepath} not found.\n{e}")
        except Exception as e:
            self._logger.exception(
                f"An unknown error occurred while executing {ddl_filepath}.\n{e}"
            )

    def _run_bash_script(self, script_filepath: str) -> None:
        """
        Runs a bash script located at the specified path with sudo privileges.

        Args:
            script_filepath (str): The path to the bash script.
        """
        try:
            sudo_password = getpass.getpass(prompt="Enter your sudo password: ")
            command = f"echo {sudo_password} | sudo -S bash {script_filepath}"
            subprocess.run(command, shell=True, check=True)
            print(f"Successfully executed {script_filepath}")
        except subprocess.CalledProcessError as e:
            self._logger.exception(f"Script execution failed with error: {e}")

    def _format_dbname(self, dbname: str) -> str:
        return f"{dbname}_{self._env}"
