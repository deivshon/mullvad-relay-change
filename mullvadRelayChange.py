#!/bin/python3

import subprocess as sp
from random import randint
import sys

def parseCountry(countryLine):
    if "(" not in countryLine: return ""

    countryLine = countryLine[countryLine.index("(") + 1:len(countryLine) - 1]
    return countryLine

def parseCity(cityLine):
    if not ("(" in cityLine and ")" in cityLine): return ""

    cityLine = cityLine[cityLine.index("(") + 1:cityLine.index(")")]
    return cityLine

def parseServer(serverLine):
    if("\t\t" not in serverLine): return ""
    serverLine = serverLine[serverLine.index("\t\t") + 2: len(serverLine)]
    return serverLine.split(" ")[0]

def countryFromServer(server):
    firstToken = list(server.split("-")[0])
    return "".join(c for c in firstToken if c not in "0123456789")

def fetchServerData():
    relays = sp.run(["mullvad", "relay", "list"], capture_output = True)
    relays = relays.stdout.decode().splitlines()
    countries = []
    cities = []
    servers = []
    for i in range(0, len(relays)):
        if(len(relays[i]) < 1): continue

        fc = relays[i][0]
        if(len(relays[i]) > 1): sc = relays[i][1]

        if(fc != "\t"):
            countries.append(parseCountry(relays[i]))
        elif(len(relays[i]) < 2): continue
        elif(fc == "\t" and sc != "\t"):
            cities.append(parseCity(relays[i]))
        elif(fc == "\t" and sc == "\t"):
            servers.append(parseServer(relays[i]))
    
    countries = list(filter(lambda s: s != "", countries))
    cities = list(filter(lambda s: s != "", cities))
    servers = list(filter(lambda s: s != "", servers))
    return countries, cities, servers

def getCurrentCountry():
    status = sp.run(["mullvad", "relay", "get"], capture_output = True)
    status = status.stdout.decode().lower().split(" ")
    if "country" not in status: return "/"
    if status.index("country") + 1 >= len(status): return "/"

    return status[status.index("country") + 1]

def getCurrentServer():
    status = sp.run(["mullvad", "status"], capture_output = True)
    status = status.stdout.decode().lower().split(" ")

    if "connected" not in status: return "/"
    if status.index("to") + 1 >= len(status): return "/"

    return status[status.index("to") + 1]

def printList(list, label, endChar = "\n"):
    print(f"Available {label}:", end = "\n")
    if(len(list) == 1):
        print(list[0])
        return

    for i in range(0, len(list) - 1):
        print(list[i], end = endChar)
    print(list[i + 1])

def perror(errorMsg):
    print(errorMsg, file = sys.stderr)

def handleConstraints(args, argsIndex, constraints, mainArgs):
    i = argsIndex
    while(i < len(args) and args[i] not in mainArgs):
        constraints.append(args[i])
        i += 1

    return i - 1

mainArgs = (
    "--print",
    "--countries",
    "--servers",
    "--verbose",
    "--countries-as-servers"
)

countries, cities, servers = fetchServerData()

countryConstraints = []
serverConstraints = []

verbose = False
countriesAsServers = False

i = 1
while i < len(sys.argv):
    arg = sys.argv[i]
    if arg == "--print":
        if len(sys.argv) <= i + 1:
            perror("No option after --print\nAvailable options: countries, cities, servers")
            sys.exit(1)

        nextArg = sys.argv[i + 1]
        if nextArg == "countries":
            printList(countries, "countries")
            quit()
        elif nextArg == "cities":
            printList(cities, "cities")
            quit()
        elif nextArg == "servers":
            printList(servers, "servers")
            quit()
        else:
            perror("Unrecognized option after --print\nAvailable options: countries, cities, servers")
            sys.exit(1)
    elif arg == "--countries":
        if len(sys.argv) <= i + 1:
            perror("No option(s) after --countries")
            sys.exit(1)

        i = handleConstraints(sys.argv, i + 1, countryConstraints, mainArgs)
    elif arg == "--servers":
        if len(sys.argv) <= i + 1:
            perror("No option(s) after --servers")
            sys.exit(1)

        i = handleConstraints(sys.argv, i + 1, serverConstraints, mainArgs)
    elif arg == "--verbose":
        verbose = True
    elif arg == "--countries-as-servers":
        countriesAsServers = True
    else:
        perror(f"Unrecognized argument: {arg}")
        sys.exit(1)

    i += 1

currentCountry = getCurrentCountry()
currentServer = getCurrentServer()
newCountryIndex = -1

if countryConstraints != []:
    availableCountries = list(filter(lambda c: c in countryConstraints, countries))
    if availableCountries == []:
        perror("No available countries amongst the ones specified")
        sys.exit(1)
else: availableCountries = countries

if serverConstraints != []:
    availableServers = list(filter(lambda s: s in serverConstraints and countryFromServer(s) in availableCountries, servers))
    if availableServers == []:
        perror("No compatible and available servers amongst the ones specified")
        sys.exit(1)
else: availableServers = []

if countriesAsServers:
    countryServers = list(filter(lambda s: countryFromServer(s) in availableCountries, servers))
    availableServers += countryServers

del countries
del servers

if availableServers == []:
    if currentCountry not in availableCountries:
        newCountryIndex = randint(0, len(availableCountries) - 1)
    else:
        newCountryIndex = (availableCountries.index(currentCountry) + 1) % len(availableCountries)

    print(f"Changing location to {availableCountries[newCountryIndex]}")
    sp.run(["mullvad", "relay", "set", "location", availableCountries[newCountryIndex]])
else:
    if currentServer not in availableServers:
        newServerIndex = randint(0, len(availableServers) - 1)
    else:
        newServerIndex = (availableServers.index(currentServer) + 1) % len(availableServers)
    print(f"Changing server to {availableServers[newServerIndex]}")
    sp.run(["mullvad", "relay", "set", "hostname", availableServers[newServerIndex]])

if verbose:
    print(end = "\n")
    printList(availableCountries, "countries given the current constraints", " ")
    if(availableServers == []):
        print("Available servers given the current constraints:\nAll servers in the available countries. No sequential switch")
    else: printList(availableServers, "servers given the current constraints", " ")
