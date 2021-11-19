# Copyright (c) 2021, Rob Woodward. All rights reserved.
#
# This file is part of IP Web Tools and is released under the
# "BSD 2-Clause License". Please see the LICENSE file that should
# have been included as part of this distribution.
#
"""Database handling classes."""

import os
import sys
from typing import Union
from sqlite3.dbapi2 import connect, Cursor, Row, DatabaseError


class Db:
    """Database handler."""

    def __init__(self, verbose: int, database_file: str) -> None:
        """Database handling object.

        Args:
            verbose (int): Verbosity level
            database_file (str): Full path to database file
        """
        self.verbose = verbose
        self.create_db(database_file)

    def close(self):
        """Close the database connection."""
        self.connection.close()

    def create_db(self, database_file: str) -> None:
        """Create new SQLite3 DB, removing any that was left over before.

        Args:
            database_file (str): Full path of SQLite DB file

        """
        if self.verbose:
            print("Debug: Creating SQLite database.")

        if os.path.isfile(database_file):
            try:
                os.remove(database_file)

                if self.verbose > 1:
                    print(f"Debug: Removing old database file, {database_file}")
            except OSError as error:
                print(f"Error: {database_file} : {str(error)}", file=sys.stderr)
                sys.exit()

        try:
            self.connection = connect(database_file)

            if self.verbose:
                print(f"Debug: Created new database at {database_file}")

            self.connection.execute(
                "CREATE TABLE records (hostname TEXT, ip TEXT, ipint INTEGER, dns_name TEXT, ptr TEXT, name TEXT, zone TEXT)"
            )
            self.connection.commit()

            if self.verbose > 1:
                print("Debug: Created records table in the database.")

            # Set returned rows to be a Row/Dict instead of list.
            self.connection.row_factory = Row

        except DatabaseError as dberror:
            print(f"Error: Database error, {database_file} ,{str(dberror)}", file=sys.stderr)
            sys.exit()

        if self.verbose:
            print("Debug: Finished creating SQLite database.")

    def interface_to_db(self, interfaces: dict) -> None:
        """Insert the interfaces into SQLite3 Database.

        Args:
            interfaces (dict): list of interfaces

        """
        try:
            self.connection.executemany(
                "insert into records values (:hostname, :ip, :ipint, :dns_name, :ptr, :name, :zone)",
                interfaces.values(),
            )
            self.connection.commit()

            if self.verbose > 1:
                print("Debug: Added DNS interface records to the database.")

        except DatabaseError as dberror:
            print(f"Error: Database error inserting interfaces into database, {str(dberror)}", file=sys.stderr)

    def get_zones(self) -> Union[list, None]:
        """Get list of DNS zones from database.

        Returns:
            Union[list, None]: list of zones or None on error
        """
        try:
            cursor = self.connection.cursor()
            return cursor.execute("SELECT DISTINCT(zone) as zone FROM records").fetchall()
        except DatabaseError as dberror:
            print(f"Error: Database error getting zone list from database, {str(dberror)}", file=sys.stderr)

    def get_zone_rows(self, zone: str) -> Union[Cursor, None]:
        """Get DNS row entries for zone.

        Args:
            zone (str): Zone to search for

        Returns:
            Union[Cursor, None]: DNS records or None if error.
        """
        try:
            return self.connection.execute("SELECT * FROM records WHERE zone LIKE ? ORDER BY ipint ASC", [zone])
        except DatabaseError as dberror:
            print(
                f"Error: Database error getting zone interface records from database, {str(dberror)}", file=sys.stderr
            )

    def get_all_rows(self) -> Union[Cursor, None]:
        """Get all dns record rows.

        Returns:
            Union[Cursor, None]: DNS record rows all None on error.
        """
        try:
            return self.connection.execute("SELECT * FROM records ORDER BY ipint ASC")
        except DatabaseError as dberror:
            print(f"Error: Database error getting interface records from database, {str(dberror)}", file=sys.stderr)
