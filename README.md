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

When only countries are specified, the Mullvad app automatically chooses a server from the country to which the location has been changed (as far as I know, chosen randomly)

To avoid this behaviour you can user the `--countries-as-servers` argument, which makes it so that selecting a country produces the equivalent result of selecting all the servers from said country. In practice, this means that you can, for instance, only have a country in your constraints but still sequentially switch from one server to the next, selecting the servers only from the ones in said country. Of course, the option is not limited in use to the case where you only have one country in the constraints. For example:

    $ python3 mullvadRelayChange.py --countries it fi --verbose
    Changing location to fi
    Relay constraints updated

    Available countries given the current constraints:
    fi it
    Available servers given the current constraints:
    All servers in the available countries. No sequential switch

... in this case, the script will sequentially switch the location from Italy to Finland and viceversa (if invoked with the same arguments, of course), but the server chosen within the country will be selected by the Mullvad app (again, probably randomly, and certainly not sequentially). If you wanted to sequentially switch from one server to the next from a pool of servers composed of the ones only located in these two countries, then you can use the `--countries-as-servers` option:

    $ python3 mullvadRelayChange.py --countries it fi --countries-as-servers --verbose
    Changing server to fi2-wireguard
    Setting location constraint to fi2-wireguard in hel, fi
    Relay constraints updated

    Available countries given the current constraints:
    fi it
    Available servers given the current constraints:
    fi-hel-001 fi-hel-002 fi-hel-003 fi-hel-004 fi-hel-005 fi-hel-006 fi-hel-007 fi1-wireguard fi2-wireguard fi3-wireguard it-mil-101 it-mil-102 it-mil-103 it-mil-104 it-mil-wg-001 it-mil-wg-002 it-mil-wg-003 it4-wireguard it5-wireguard it6-wireguard it7-wireguard

... as you can see, the servers in the pool are still all of the ones in the selected countries, but the command given to Mullvad was to connect to a specific one, not to only change the relay location, thereby enabling sequential switching


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
