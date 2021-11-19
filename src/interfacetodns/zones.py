# Copyright (c) 2021, Rob Woodward. All rights reserved.
#
# This file is part of IP Web Tools and is released under the
# "BSD 2-Clause License". Please see the LICENSE file that should
# have been included as part of this distribution.
#
"""Build Zonefiles."""
import sys
from shutil import copy
from sqlite3.dbapi2 import Cursor


class Zone:
    """Zonefile writer Object."""

    def __init__(self, verbose: int) -> None:
        """Zonefile writer.

        Args:
            verbose (int): Verbosity Level
        """
        self.verbose = verbose

    def db_to_zonefile(self, zone_file: str, template_file: str, records: Cursor) -> None:
        """Convert the database into zone files.

        Args:
            zone_file (str): Zone file path to write to
            template_file (str): Zone file template path to write to
            records (Cursor): PTR records

        """
        if self.verbose:
            print(f"Debug: Building zone file, {zone_file}.")

        try:
            copy(template_file, zone_file)

            if self.verbose > 1:
                print(f"Debug: Copying zone template from {template_file} to {zone_file}.")

            outfile = open(zone_file, "a", encoding="ascii")

            if self.verbose > 1:
                print(f"Debug: Opened new zone file, {zone_file}, for writing.")

        except EnvironmentError as error:
            print(f"Error: {str(error)} : {zone_file}", file=sys.stderr)
            return

        for record in records:
            outfile.write(f"{record['ptr']:<28}{'PTR':^11}{record['dns_name']}.\n")
            if self.verbose > 2:
                print(f"Debug: Writing {record['ptr']} -> {record['dns_name']} to zone file.")

        if self.verbose:
            print("Debug: Finished writing zone records to zone file.")

        # close DB cursor.
        records.close()

        # Close output zone file.
        try:
            outfile.close()
        except EnvironmentError as error:
            print(f"Error: Closing files {str(error)} : {zone_file}", file=sys.stderr)
