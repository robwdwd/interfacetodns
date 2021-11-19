# Interface to DNS

Command line tool to build reverse DNS entries for interface IP on network devices.

## Command line options

```console
Usage: interfacetodns [OPTIONS]

  Parse interfaces on network devices using SNMP and build DNS zone files with
  records for IP addresses found on the interfaces.

Options:
  --config CONFIG_FILE  Configuaration file to load.
  --seed SEED_FILE      Seedfile to load.  [required]
  --rpz                 Output a response policy zone instead of seperate zone
                        files.
  -v, --verbose         Output some debug information, use multiple times for
                        increased verbosity.
  --help                Show this message and exit.
```

## Seedfile

Seedfile is one device per line in the format `device;os;mgnt_protocol;snmp_version`. At the moment this is using a format used by some other scripts, the OS (IOS-XR etc) and the management protocol are not used (SSH, TELNET).

```console
router1.example.net;IOS-XR;SSH;2
router2.example.net;IOS-XR;SSH;3
router3.example.net;JunOS;SSH;2
```

## Configuration

Configuration by default is in `.config/interfacetodns/config.json` and takes the following format. The configration can be specified on the command line or by using `INTERFACETODNS_CONFIG_FILE` environment variable.

```json
{
  "basedir": "/var/dns",
  "snmp": {
    "timeout": 1,
    "community": "public",
    "auth_user": "user",
    "auth_protocol": "SHA",
    "auth_password": "password",
    "privacy_protocol": "AES",
    "privacy_key": "private"
  },
  "ip_range_match": ["10.1.1.0/24", "192.168.1.0/24", "10.6.0.0/20"],
  "zones": {
    "rpz": "/home/user/.config/interfacetodns/rpz.template",
    "standard": "/home/user/.config/interfacetodns/standard.template"
  },
  "masks": {
    "port_name": ["^system", "_PE_"]
  },
  "mapping": {
    "port_name": {
      "^xe-": "xe",
      "^ge-": "ge",
      "^FastEthernet": "fa",
      "^GigabitEthernet": "gi",
      "^TenGigabitEthernet": "te",
      "^TenGigE": "te",
      "^FortyGigE": "fge",
      "^HundredGigE": "hge",
      "^FourHundredGigE": "fhge",
      "^Bundle-Ether": "be",
      "^Vlan": "vl",
      "^Loopback": "lo",
      "^lo": "lo"
    }
  }
}
```

## Zone templates

Two zone templates need to be created, one for response policy zone and one for normal zone files. These are configured in the zones key in the configuration file.

```json
"rpz": "/home/user/.config/interfacetodns/rpz.template",
"standard": "/home/user/.config/interfacetodns/standard.template"
```

They can look something like this

```zone
; BIND Zone
;
;
$TTL    86400
@   IN  SOA localhost. root.localhost. (
                  1     ; Serial
             604800     ; Refresh
              86400     ; Retry
            2419200     ; Expire
              86400 )   ; Negative Cache TTL
;
@   IN  NS  localhost.
```
