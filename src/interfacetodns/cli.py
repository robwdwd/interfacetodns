#!/usr/bin/env python3
# Copyright (c) 2021, Rob Woodward. All rights reserved.
#
# This file is part of IP Web Tools and is released under the
# "BSD 2-Clause License". Please see the LICENSE file that should
# have been included as part of this distribution.
#
"""Command to generate reverse DNS zones from interfaces on network devices."""

import os
import json
import sys
import re
import click
from interfacetodns.device import DeviceParser
from interfacetodns.db import Db
from interfacetodns.zones import Zone


@click.command()
@click.option(
    "--config",
    metavar="CONFIG_FILE",
    help="Configuaration file to load.",
    default=os.environ["HOME"] + "/.config/interfacetodns/config.json",
    envvar="INTERFACETODNS_CONFIG_FILE",
    type=click.File(mode="r"),
)
@click.option("--seed", required=True, metavar="SEED_FILE", help="Seedfile to load.", type=click.File(mode="r"))
@click.option("--rpz", is_flag=True, help="Output a response policy zone instead of seperate zone files.")
@click.option(
    "--verbose", "-v", count=True, help="Output some debug information, use multiple times for increased verbosity."
)
def cli(**cli_args):
    """Parse interfaces on network devices using SNMP and build DNS zone files with records for IP addresses found on the interfaces."""
    # Allow acces to cfg and other vars
    #
    cfg = json.load(cli_args["config"])

    device_parser = DeviceParser(cli_args["verbose"], cfg["snmp"], cfg["mapping"]["port_name"], cfg["ip_range_match"])

    # Create DB object
    #
    database = Db(cli_args["verbose"], f"{cfg['basedir']}/interfacetodns.db")

    # Build the database from interfaces retrived from network devices.
    #
    seedline_re = re.compile("^(.+);.+;.+;(.+)$")

    for seed_line in cli_args["seed"]:
        seedline = str(seed_line).strip()
        seed_matches = seedline_re.match(seedline)
        if seed_matches:
            hostname = seed_matches.group(1)
            host_snmp_version = int(seed_matches.group(2))
            interfaces = device_parser.fetch_interfaces(hostname, host_snmp_version)
            if interfaces:
                database.interface_to_db(interfaces)
            else:
                print(f"Warning: [{hostname}] No interfaces discoverd on device.", file=sys.stderr)

    # Process the database and turn into zonefiles

    zone = Zone(cli_args["verbose"])

    if cli_args["rpz"]:
        records = database.get_all_rows()
        if records:
            zone.db_to_zonefile(f"{cfg['basedir']}/db.rpz.local", cfg["zones"]["rpz"], records)
        else:
            print("Warning: No records found in database.", file=sys.stderr)
    else:
        zone_rows = database.get_zones()
        if zone_rows:
            for zone_row in zone_rows:
                records = database.get_zone_rows(zone_row["zone"])
                if records:
                    zone.db_to_zonefile(f"{cfg['basedir']}/db.{zone_row['zone']}", cfg["zones"]["standard"], records)
                else:
                    print(f"Warning: No records found in database for zone, {zone_row['zone']}.", file=sys.stderr)
        else:
            print("Warning: No zones discoverd in database.", file=sys.stderr)

    database.close()
