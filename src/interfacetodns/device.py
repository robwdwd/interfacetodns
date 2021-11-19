# Copyright (c) 2021, Rob Woodward. All rights reserved.
#
# This file is part of IP Web Tools and is released under the
# "BSD 2-Clause License". Please see the LICENSE file that should
# have been included as part of this distribution.
#
"""Device object for fetching from device."""

import re
import sys
from ipaddress import ip_address, ip_network
from typing import Union
from easysnmp import Session, EasySNMPError


class DeviceParser:
    """Device Parser."""

    def __init__(self, verbose: int, snmp: dict, port_map: dict, match_ip: list) -> None:
        """Device Parser, get SNMP interfaces and parse the output into interface list.

        Args:
            verbose (int): Verbosity Level
            snmp (dict): SNMP Configuration
            port_map (dict): SNMP Portname regex to DNS port name
            match_ip (list): List of IP address ranges to match against when generating DNS for interfaces
        """
        self.verbose = verbose
        self.snmp = snmp
        self.compile_port_map(port_map)
        self.match_ip_to_ip_set(match_ip)

    def match_ip_to_ip_set(self, match_ip: list) -> None:
        """Convert IP match ranges into IPSet object.

        Args:
            match_ip (list): IP Match Ranges

        """
        result = []

        for prefix in match_ip:
            result.append(ip_network(prefix))

        self.match_ip = result

    def compile_port_map(self, port_map: dict) -> None:
        """Compile portmap into regular expressions.

        Args:
            port_map (dict): Port map to DNS name mapping

        """
        result = []

        # Compile all regex for name replacement
        #
        for match_re in port_map:
            new_re = re.compile(match_re)
            result.append({"re": new_re, "repl": port_map[match_re]})

        self.port_map = result

    def fetch_interfaces(self, hostname: str, snmp_version: int = 2) -> Union[dict, None]:
        """Get SNMP interfaces from the network device.

        Args:
            hostname (str): Device hostname.
            snmp_version (int): SNMP version to use.

        Returns:
            dict|None: Parsed interface list.
        """
        try:
            if self.verbose:
                print(f"Debug: Fetching interfaces from {hostname} using SNMP v{snmp_version}.")

            session = Session(
                hostname=hostname,
                community=self.snmp["community"],
                security_username=self.snmp["auth_user"],
                auth_password=self.snmp["auth_password"],
                privacy_password=self.snmp["privacy_key"],
                auth_protocol=self.snmp["auth_protocol"],
                privacy_protocol=self.snmp["privacy_protocol"],
                security_level="auth_with_privacy",
                version=snmp_version,
            )

            # Get interface names.
            if self.verbose > 1:
                print(f"Debug: Fetching interface names from {hostname}.")

            interface_names = session.bulkwalk("1.3.6.1.2.1.2.2.1.2")

            # Get interface IP addresses.
            if self.verbose > 1:
                print(f"Debug: Fetching interface ip addresses from {hostname}.")

            interface_ips = session.bulkwalk(".1.3.6.1.2.1.4.20.1.2")

            if self.verbose:
                print(f"Debug: Finished fetching interfaces from {hostname}.")

            # Parse SNMP results.
            return self.parse_snmp(hostname, interface_names, interface_ips)

        except EasySNMPError as error:
            print(f"Error: [{hostname}] {str(error)}", file=sys.stderr)
            return

    def parse_snmp(self, hostname: str, interfaces_names: list, interface_ips: list) -> dict:
        """Parse the interface results from network device.

        Args:
            hostname (str): Device hostname.
            interfaces_names (list): List of SNMP interface names.
            interface_ips (list): List of SNMP interface IP addresses.

        Returns:
            dict: Parsed interface dictionary.
        """
        interfaces = {}
        replace_illegal_chars = re.compile(r"[\/\.\:]")

        if self.verbose:
            print(f"Debug: Parsing interfaces on {hostname}.")

        for item in interface_ips:
            ip_octets = item.oid.split(".")[-4:]
            ipaddr = ip_address(".".join(ip_octets))

            if self.verbose > 3:
                print(f"Debug: Working on IP address {str(ipaddr)} on {hostname}.")

            if any(ipaddr in network for network in self.match_ip):
                index = item.value
                ptr_record = ".".join(ip_octets[::-1]) + ".in-addr.arpa"
                zone = ptr_record.split(".", 1)[1]

                if self.verbose > 2:
                    print(
                        f"Debug: IP address {str(ipaddr)} on {hostname} is in the match list, adding to interface table."
                    )

                interfaces[index] = {
                    "hostname": hostname,
                    "ip": str(ipaddr),
                    "ipint": int(ipaddr),
                    "ptr": ptr_record,
                    "zone": zone,
                }

        for item in interfaces_names:
            index = item.oid.split(".")[-1]
            value = item.value

            dns_name = value

            if index in interfaces:
                interfaces[index]["name"] = value

                if self.verbose > 2:
                    print(f"Debug: Working on interface {value} on {hostname}.")

                # Check for a mapping to convert the interfaces
                for port_map_name in self.port_map:
                    new_value = port_map_name["re"].sub(port_map_name["repl"], dns_name)
                    if new_value != dns_name:
                        if self.verbose > 2:
                            print(
                                f"Debug: Chanaged interface name for dns from {dns_name} to {new_value} on {hostname}."
                            )

                        dns_name = new_value
                        break

                interfaces[index]["dns_name"] = replace_illegal_chars.sub("-", dns_name.lower()) + "-" + hostname
                if self.verbose > 2:
                    print(f"Debug: Finished working on interface {value} on {hostname}.")

        if self.verbose:
            print(f"Debug: Finished parsing interfaces on {hostname}.")
        return interfaces
