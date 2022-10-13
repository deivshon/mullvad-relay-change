#!/bin/python3

import subprocess as sp
from random import randint
import sys
import json
import os

def getCurrentRelayInfo():
    status = sp.run(["mullvad", "relay", "get"], capture_output = True)
    status = status.stdout.decode().lower().split(" ")

    country = ""
    city = ""
    server = ""
    if "city" not in status and "country" not in status: return "", "", ""
    elif "country" in status:
        countryIndex = status.index("country") + 1
        if(len(status) > countryIndex):
            country = status[countryIndex].strip(",")
    elif "city" in status:
        cityIndex = status.index("city") + 1
        countryIndex = status.index("city") + 2
        if(len(status) > countryIndex):
            country = status[countryIndex].strip(",")
            city = (country, status[cityIndex].strip(","))

    if "hostname" in status:
        serverIndex = status.index("hostname") + 1
        if(len(status) > serverIndex):
            server = status[serverIndex].strip(",")

    return country, city, server

def printList(list, label, endChar = "\n"):
    if label != None:
        print(f"Available {label}:", end = "\n")
    if(len(list) == 1):
        print(list[0])
        return

    for i in range(0, len(list) - 1):
        print(list[i], end = endChar)
    print(list[i + 1])

def printTupleList(list, label, endChar = "\n"):
    if label != None:
        print(f"Available {label}:", end = "\n")
    if(len(list) == 1):
        printList(list[0], label = None, endChar = endChar)
        return

    for i in range(0, len(list)):
        printList(list[i], label = None, endChar = endChar)

def perror(errorMsg):
    print(errorMsg, file = sys.stderr)

def handleConstraints(args, argsIndex, constraints, mainArgs):
    i = argsIndex
    while(i < len(args) and args[i] not in mainArgs):
        constraints.append(args[i])
        i += 1

    return i - 1

def getRelayInfo():
    try:
        # Imported here as the import takes significantly more time than
        # that of the other modules, and it only needs to be used occasionally
        from requests import get as reqget

        relayInfo = reqget("https://api.mullvad.net/www/relays/all/", timeout = 10).json()
        return relayInfo
    except:
        perror("Could not get relay information from Mullvad API")
        return -1

def saveRelayInfo(relayInfo, dirPath, fileName = "mullvadRelayInfo.json"):
    if(not os.path.isdir(dirPath)):
        perror(f"{dirPath} is not a valid directory")
        return -1
    
    if(dirPath[len(dirPath) - 1] != "/"): dirPath += "/"
    try:
        with open(dirPath + fileName, "w") as f:
            json.dump(relayInfo, f)
        return 1
    except:
        perror(f"An error occurred while writing relay info to {dirPath + fileName}")
        return -1

def loadRelayInfo(dirPath, fileName = "mullvadRelayInfo.json"):
    if(dirPath[len(dirPath) - 1] != "/"): dirPath += "/"
    if not os.path.isfile(dirPath + fileName):
        relayInfo = getRelayInfo()
        if relayInfo != -1: saveRelayInfo(relayInfo, dirPath, fileName)
        return relayInfo

    with open(dirPath + fileName) as f:
        relayInfo = json.loads(f.read())

    return relayInfo

def getRelayFieldList(relayInfo, field, excludeBridges = True, excludeOffline = True):
    resultList = []
    for relay in relayInfo:
        if excludeBridges and relay["type"] == "bridge": continue
        if excludeOffline and relay["active"] == False: continue
        if field not in relay.keys(): continue

        if relay[field] not in resultList:
            resultList.append(relay[field])

    return resultList

def getCities(relayInfo, excludeBridges = True, excludeOffline = True):
    resultList = []
    for relay in relayInfo:
        if excludeBridges and relay["type"] == "bridge": continue
        if excludeOffline and relay["active"] == False: continue
        if "city_code" not in relay.keys(): continue
        if "country_code" not in relay.keys(): continue

        country = relay["country_code"]
        city = relay["city_code"]

        if (country, city) not in resultList:
            resultList.append((country, city))

    return resultList

def serverFits(relay, serverNames, countryConstraints, cityConstraints, serverConstraints):
    if "country_code" not in relay.keys(): return False
    if "city_code" not in relay.keys(): return False
    if "hostname" not in relay.keys(): return False

    country = relay["country_code"]
    city = relay["city_code"]
    hostname = relay["hostname"]

    if hostname not in serverNames:
        return False
    if countryConstraints != [] and country not in countryConstraints:
        return False
    if cityConstraints != [] and (country, city) not in cityConstraints:
        return False
    if serverConstraints != [] and hostname not in serverConstraints:
        return False
    
    return True

def cityFits(city, relayInfo, countryConstraints, cityConstraints):
    cityCountry = city[0]
    cityProper = city[1]
    for relay in relayInfo:
        if "city_code" not in relay.keys(): continue
        if "country_code" not in relay.keys(): continue

        relayCity = relay["city_code"]
        relayCountry = relay["country_code"]
        if relayCity != cityProper or relayCountry != cityCountry: continue

        if countryConstraints != [] and relayCountry not in countryConstraints:
            return False
        if cityConstraints != [] and (relayCountry, relayCity) not in cityConstraints:
            return False

        return True
    
    return False

def argCheck(argv, index, acceptedOptions = None):
    if len(argv) <= index + 1:
        perror(f"No option after {sys.argv[index]}")
        if acceptedOptions != None:
            perror(f"Accepted options: {', '.join(acceptedOptions)}")
        sys.exit(1)
    
    if acceptedOptions != None and argv[index + 1] not in acceptedOptions:
        perror(f"Unrecognized option after {sys.argv[index]}\nAccepted options: {', '.join(acceptedOptions)}")
        sys.exit(1)

def filterRelayEntityList(unfilteredEntityList, relayInfo, necessaryFields, entityGet, *args):
    newEntityList = []
    for relay in relayInfo:
        invalid = False

        for f in necessaryFields:
            if f not in relay.keys():
                invalid = True
                break
        if invalid: continue

        relayEntity = entityGet(relay)

        if relayEntity not in unfilteredEntityList: continue
        if relayEntity in newEntityList: continue
        for validityFunction in args:
            if not validityFunction(relay):
                invalid = True
                break

        if invalid: continue

        newEntityList.append(relayEntity)

    return newEntityList

relayInfo = loadRelayInfo("/tmp")
if relayInfo == -1: sys.exit(1)

countries = getRelayFieldList(relayInfo, "country_code")
cities = getCities(relayInfo)
servers = getRelayFieldList(relayInfo, "hostname")

mainArgs = (
    "--print",
    "--countries",
    "--cities",
    "--servers",
    "--verbose",
    "--countries-as-servers",
    "--cities-as-servers",
    "--tunnel-protocol",
    "--ownership",
    "--stboot",
    "--isp",
    "--isp-not",
    "--min-bandwidth",
    "--random",
    "--pick-country",
    "--pick-city"
)

countryConstraints = []
cityConstraints = []
serverConstraints = []

ispConstraints = []
ispNegativeConstraints = []
ispCheck = lambda r: "provider" in r.keys() and (True if ispConstraints == [] else r["provider"] in ispConstraints)
ispNegativeCheck = lambda r: "provider" in r.keys() and (True if ispNegativeCheck == [] else r["provider"] not in ispNegativeConstraints)

tunnelProtocol = "any"
tunnelProtocolCheck = lambda r: "type" in r.keys() and (True if tunnelProtocol == "any" else r["type"] == tunnelProtocol)

ownership = "any"
ownershipCheck = lambda r: "owned" in r.keys() and (True if ownership == "any" else (r["owned"] == True if ownership == "owned" else r["owned"] == False))

stboot = "any"
stbootCheck = lambda r: "stboot" in r.keys() and (True if stboot == "any" else (r["stboot"] == True if stboot == "true" else r["stboot"] == False))

minBandwidth = 0
minBandwidthCheck = lambda r: "network_port_speed" in r.keys() and r["network_port_speed"] >= minBandwidth

verbose = False
countriesAsServers = False
citiesAsServers = False
randomChoice = False

pickCountry = False
pickCity = False

i = 1
while i < len(sys.argv):
    arg = sys.argv[i]
    if arg == "--print":
        argCheck(sys.argv, i, ("countries", "cities", "servers"))

        nextArg = sys.argv[i + 1]
        if nextArg == "countries":
            printList(countries, "countries")
            quit()
        elif nextArg == "cities":
            printTupleList(cities, "cities", ", ")
            quit()
        elif nextArg == "servers":
            printList(servers, "servers")
            quit()

    elif arg == "--countries" or arg == "--cities" or arg == "--servers":
        if len(sys.argv) <= i + 1:
            perror(f"No option(s) after {arg}")
            sys.exit(1)
        if arg == "--countries":
            constraints = countryConstraints
        elif arg == "--cities":
            constraints = cityConstraints
        else:
            constraints = serverConstraints

        i = handleConstraints(sys.argv, i + 1, constraints, mainArgs)

        if arg == "--cities":
            # City codes are not unique, therefore city arguments
            # must be expressed in the form of "country_code city_code"
            cityConstraints = [(constraints[i], constraints[i + 1])
                                for i in range(0, len(constraints), 2)
                                if i + 1 < len(constraints)]
    elif arg == "--tunnel-protocol":
        argCheck(sys.argv, i, ("any", "wireguard", "openvpn"))

        tunnelProtocol = sys.argv[i + 1]
        i += 1
    elif arg == "--ownership":
        argCheck(sys.argv, i, ("any", "owned", "rented"))

        ownership = sys.argv[i + 1]
        i += 1
    elif arg == "--stboot":
        argCheck(sys.argv, i, ("any", "true", "false"))

        stboot = sys.argv[i + 1]
        i += 1
    elif arg == "--isp":
        i = handleConstraints(sys.argv, i + 1, ispConstraints, mainArgs)
    elif arg == "--isp-not":
        i = handleConstraints(sys.argv, i + 1, ispNegativeConstraints, mainArgs)
    elif arg == "--min-bandwidth":
        argCheck(sys.argv, i)

        try:
            minBandwidth = int(sys.argv[i + 1])
        except:
            perror("Invalid minimum bandwidth value provided")
            sys.exit(1)
        
        i += 1
    elif arg == "--verbose":
        verbose = True
    elif arg == "--countries-as-servers":
        countriesAsServers = True
    elif arg == "--cities-as-servers":
        citiesAsServers = True
    elif arg == "--random":
        randomChoice = True
    elif arg == "--pick-country":
        pickCountry = True
    elif arg == "--pick-city":
        pickCity = True
    else:
        perror(f"Unrecognized argument: {arg}")
        sys.exit(1)

    i += 1

currentCountry, currentCity, currentServer = getCurrentRelayInfo()
newCountryIndex = -1

if countryConstraints != []:
    availableCountries = list(filter(lambda c: c in countryConstraints, countries))
    if availableCountries == []:
        perror("No available countries amongst the ones specified")
        sys.exit(1)
else: availableCountries = countries

if cityConstraints != []:
    availableCities = list(filter(lambda c: cityFits(c, relayInfo, countryConstraints, cityConstraints), cities))
    if availableCities == []:
        perror("No available cities amongst the ones specified")
        sys.exit(1)
else: availableCities = []

if serverConstraints != []:
    availableServers = filter(lambda s: serverFits(s, servers, countryConstraints, cityConstraints, serverConstraints), relayInfo)

    if availableServers == []:
        perror("No compatible and available servers amongst the ones specified")
        sys.exit(1)
else: availableServers = []

if countriesAsServers:
    countryServers = filter(lambda s: serverFits(s, servers, countryConstraints, [], []), relayInfo)

    availableServers += [s for s in countryServers if s not in availableServers]

if citiesAsServers and cityConstraints != []:
    cityServers = filter(lambda s: serverFits(s, servers, countryConstraints, cityConstraints, []), relayInfo)

    availableServers += [s for s in cityServers if s not in availableServers]

implicitServerPick = False

if availableServers == [] and availableCities == []:
    availableCountries = filterRelayEntityList(availableCountries, relayInfo, ["country_code"], lambda r: r["country_code"], ispCheck, ispNegativeCheck, tunnelProtocolCheck, ownershipCheck, stbootCheck, minBandwidthCheck)

    if currentCountry not in availableCountries or randomChoice:
        newCountryIndex = randint(0, len(availableCountries) - 1)
    else:
        newCountryIndex = (availableCountries.index(currentCountry) + 1) % len(availableCountries)

    if availableCountries[newCountryIndex] == currentCountry:
        newCountryIndex += 1
        newCountryIndex %= len(availableCountries)

    print(f"Changing location to {availableCountries[newCountryIndex]}")
    if pickCountry:
        sp.run(["mullvad", "disconnect", "--wait"])
        sp.run(["mullvad", "relay", "set", "location", availableCountries[newCountryIndex]])
        sp.run(["mullvad", "connect", "--wait"])
    else:
        availableServers = filter(lambda s: serverFits(s, servers, [availableCountries[newCountryIndex]], [], []), relayInfo)
        sp.run(["mullvad", "disconnect", "--wait"])
        sp.run(["mullvad", "relay", "set", "location", availableCountries[newCountryIndex]])
        implicitServerPick = True

elif availableServers == [] and availableCities != []:
    availableCities = filterRelayEntityList(availableCities, relayInfo, ["country_code", "city_code"], lambda r: (r["country_code"], r["city_code"]), ispCheck, ispNegativeCheck, tunnelProtocolCheck, ownershipCheck, stbootCheck, minBandwidthCheck)

    if currentCity not in availableCities or randomChoice:
        newCityIndex = randint(0, len(availableCities) - 1)
    else:
        newCityIndex = (availableCities.index(currentCity) + 1) % len(availableCities)
    
    if availableCities[newCityIndex] == currentCity:
        newCityIndex += 1
        newCityIndex %= len(availableCities)

    cityCountry = availableCities[newCityIndex][0]
    if cityCountry == False:
        perror("Could not detect which country the city selected is located in")
        sys.exit(1)

    newCountry = availableCities[newCityIndex][0]
    newCity = availableCities[newCityIndex][1]
    print(f"Changing location to {newCountry}, {newCity}")
    if pickCity:
        sp.run(["mullvad", "disconnect", "--wait"])
        sp.run(["mullvad", "relay", "set", "location", newCountry, newCity])
        sp.run(["mullvad", "connect", "--wait"])
    else:
        availableServers = filter(lambda s: serverFits(s, servers, [], [availableCities[newCityIndex]], []), relayInfo)
        sp.run(["mullvad", "disconnect", "--wait"])
        sp.run(["mullvad", "relay", "set", "location", newCountry, newCity])
        implicitServerPick = True

if availableServers != []:
    availableServerNames = list(map(lambda r: r["hostname"], (availableServers)))
    availableServers = filterRelayEntityList(availableServerNames, relayInfo, ["hostname"], lambda r: r["hostname"], ispCheck, ispNegativeCheck, tunnelProtocolCheck, ownershipCheck, stbootCheck, minBandwidthCheck)

    if currentServer not in availableServers or randomChoice:
        newServerIndex = randint(0, len(availableServers) - 1)
    else:
        newServerIndex = (availableServers.index(currentServer) + 1) % len(availableServers)

    if availableServers[newServerIndex] == currentServer:
        newServerIndex += 1
        newServerIndex %= len(availableServers)    

    print(f"Changing server to {availableServers[newServerIndex]}")
    sp.run(["mullvad", "relay", "set", "hostname", availableServers[newServerIndex]])
    sp.run(["mullvad", "connect", "--wait"])

if verbose:
    print(end = "\n")
    printList(availableCountries, "countries given the current constraints", " ")

    if availableCities == []:
        print("Available cities given the current constraints:\nAll cities in the available countries. No sequential switch")
    else:
        printTupleList(availableCities, "cities given the current constraints", ", ")

    if availableServers == []:
        print("Available servers given the current constraints:\nAll servers in the available countries. No sequential switch")
    elif implicitServerPick:
        print("Available servers given the current constraints:\nAll servers in the available countries, within specified constraints. No sequential switch")
    else:
        printList(availableServers, "servers given the current constraints", " ")
