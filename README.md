# mullvad-relay-change

Wrapper utility script to sequentially select Mullvad servers/countries from a custom pool

## Country and server constraints

Country and server constraints can be chosen with command line arguments

From the available servers and countries, only the ones that fit the constraints are selected to be in the final pool from which the next relay location/server will be extracted and eventually set using the `mullvad` commands

To select countries, use the argument `--countries` followed by a list of countries you want in your constraints. For example:

    $ python3 mullvadRelayChange.py --countries us pt it
    Changing location to us
    Relay constraints updated

Invalid country codes will be ignored

To select servers, use the argument `--servers` followed by a list of servers you want in your constraints.

    $ python3 mullvadRelayChange.py --servers us258-wireguard pt1-wireguard fi3-wireguard us-sea-wg-001
    Changing server to fi3-wireguard
    Setting location constraint to fi3-wireguard in hel, fi
    Relay constraints updated

Invalid server names will be ignored

The two arguments can be combined, so that in the final pool will only be the servers that also fit the country constraints. For example:

    $ python3 mullvadRelayChange.py --servers us258-wireguard pt1-wireguard fi3-wireguard us-sea-wg-001 --countries us pt it
    Changing server to us258-wireguard
    Setting location constraint to us258-wireguard in den, us
    Relay constraints updated

In this case, the final pool will only be composed of the following servers:

    pt1-wireguard us258-wireguard us-sea-wg-001

... as these are the only ones that also fit the country constraints

Without any argument the default behaviour is selecting a pool full of all the available countries

When only countries are specified, the Mullvad app automatically chooses a server from the country to which the location has been changed (as far as I know, this is random, but I could be wrong)

## Other utilities

To facilitate the creation of custom pools, the script also features a listing function, which can print all the currently available countries, cities or servers

    $ python3 mullvadRelayChange.py --print servers
    Available servers:
    al-tia-001
    au-adl-001
    [...]
    us238-wireguard
    us241-wireguard
    $ python3 mullvadRelayChange.py --print cities
    Available cities:
    tia
    adl
    [...]
    sea
    uyk
    $ python3 mullvadRelayChange.py --print countries
    Available countries:
    al
    au
    [...]
    ae
    us

Note that right now cities can not be included in the custom relay constraints

Finally, to make sure the right countries and/or servers are being selected, you can use the `--verbose` argument to make the script show the available countries and servers after the filtering done using the selected constraints

    $ python3 mullvadRelayChange.py --servers us258-wireguard pt1-wireguard fi3-wireguard us-sea-wg-001 --countries us pt it --verbose
    Changing server to us-sea-wg-001
    Setting location constraint to us-sea-wg-001 in sea, us
    Relay constraints updated
    
    Available countries given the current constraints:
    it pt us
    Available servers given the current constraints:
    pt1-wireguard us258-wireguard us-sea-wg-001

Note that currently offline servers are automatically filtered out because they are not shown in the output of the `mullvad relay list` command, which is used by the script to fetch the necessary data
