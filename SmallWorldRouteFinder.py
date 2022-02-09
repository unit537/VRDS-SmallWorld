import json
import sys
import requests
import pathlib
from typing import List
from os.path import exists


class CardImage:
    id: int
    image_url: str
    image_url_small: str

class CardPrice:
    cardmarket_price: str
    tcgplayer_price: str
    ebay_price: str
    amazon_price: str
    coolstuffinc_price: str

class CardSet:
    set_name: str
    set_code: str
    set_rarity: str
    set_rarity_code: str
    set_price: str

class Card:
    id: int # Card UUID
    name: str
    type: str # Card Super Type. Monster, Spell, Trap.
    desc: str # Card Text, including Pendulum Text
    atk: int
    card_def: int # We can't use def as a variable name, so card_def
    level: int
    race: str # Monster Type, or Spell/Trap Type (Normal, Continuous, Quick-Play, Counter, etc.)
    attribute: str
    archetype: str # Sometimes this information is wrong or missing
    scale: int # Pendulum Scale
    linkval: int # Link rating, such as LINK-2, LINK-4, etc.
    linkmarkers: List[str] # Link Arrow Directions
    card_sets: List[CardSet] # Set(s) that the card was printed in
    card_images: List[CardImage] # Card Image URLs
    card_prices: List[CardPrice] # Current average prices as of the datetime the file was saved

    def __init__(self, json):
        vars(self).update(json)

# Global Vars
cardDB = None
deck: List[Card] = []
starter: Card = None
starters: List[str] = []
targets: List[str] = []
longestNameLength: int = 0
routes: List[tuple[Card, Card, Card]] = []

# Grab the entirety of YGOProDeck's Card Database in JSON and save to cardinfo.php.json in current directory
def downloadYGOProDeckCardsJSON():
    pathlib.Path('cardinfo.php.json').write_bytes(requests.get('https://db.ygoprodeck.com/api/v7/cardinfo.php').content)

# Initialize Local cardDB JSON
def initializeLocalCardDB():
    global cardDB
    selection = None

    if not exists('cardinfo.php.json'):
        while selection != "Y":
            print("cardinfo.php.json missing from current directory/nDo you want to download from YGOProDeck? (Y/N): ", end ="")
            selection = input().upper()
            if selection == "Y":
                downloadYGOProDeckCardsJSON()
            elif selection == "N":
                print("cardinfo.php.json is required to continue, exiting...")
                sys.exit(0)

    # Open cardDB
    try:
        cardDB = open('cardinfo.php.json')
        cardDB = json.load(cardDB)
    except Exception as e:
        sys.exit(e)

# Init deck
def initializeDeck():
    try:
        deckFile = open('deck.ydk')
    except Exception as e:
        sys.exit(e)
    
    deckFile = deckFile.readlines()
    for line in deckFile:
        if '#EXTRA' in line.upper():
            break
        elif line.startswith('#'):
            continue
        else:
            card = findCard(int(line), cardDB)
            if card is not None and not checkCardIsInDeck(card):
                deck.append(card)

# Request card JSON from YGOProDeck
def findCardOnline(id: int):
    r = requests.get("https://db.ygoprodeck.com/api/v7/cardinfo.php?id=" + id).json()
    return Card(r['data'][0])

# Get card JSON from local DB
def findCard(id, cardDB):
    for i in range(len(cardDB['data'])):
        if cardDB['data'][i]['id'] == id:
            if "SPELL" in cardDB['data'][i]['type'].upper() or "TRAP" in cardDB['data'][i]['type'].upper():
                return None
            else:
                cardDB['data'][i]['card_def'] = cardDB['data'][i]['def']
                return Card(cardDB['data'][i])

# Verify the card is not already in the 'deck'
# The 'deck' in our use case is just the card pool available,
# so we don't want duplicates because that would result in the
# same card being used as a starter/bridge/target multiple times
def checkCardIsInDeck(target: Card):
    for card in deck:
        if target.id == card.id:
            return True
    return False

# Verify two cards are legel for Small World requirement
# "exactly 1 of the same Type, Attribute, Level, ATK or DEF"
def smallWorldLegal(cardA, cardB):
    similarities: int = 0

    if cardA.race == cardB.race: # Race is the Monster Type
        similarities += 1
    if cardA.attribute == cardB.attribute:
        similarities += 1
    if cardA.level == cardB.level:
        similarities += 1
    if cardA.atk == cardB.atk:
        similarities += 1
    if cardA.card_def == cardB.card_def:
        similarities += 1
    
    if similarities == 1:
        return True
    else:
        return False

# Find all cards legal to bridge to, from a given card
def findBridges(cardA, deck):
    bridges = []

    for cardB in deck:
        if cardB.id != cardA.id:
            if smallWorldLegal(cardA, cardB):
                bridges.append(cardB)
        
    return bridges

# Find longest card name in deck for output formatting purposes:
def findLongestCardNameInDeck():
    global longestNameLength
    for card in deck:
        if len(card.name) > longestNameLength:
            longestNameLength = len(card.name)

# Pad every card name to fixed length
def formatCardNamesInDeck():
    for card in deck:
        card.name = "{:^{}}".format(card.name, longestNameLength)

def findRoutes():
    global starter
    global routes
    for card in deck:
        if card.id == starter.id:
            continue
        else:
            starter = card
            starters.append(starter.name)
            bridges = findBridges(starter, deck)
            for bridge in bridges:
                targets = findBridges(bridge, deck)
                for target in targets:
                    if target.id != starter.id:
                        routes.append((starter.name, bridge.name, target.name))

def findTargets():
    for route in routes:
        if route[2] not in targets:
            targets.append(route[2])

initializeLocalCardDB()
initializeDeck()
findLongestCardNameInDeck()
formatCardNamesInDeck()
starter = deck[0]
findRoutes()
findTargets()

# Begin user prompts
selection = None

while selection != "S" or selection != "T":
    print("Find routes by Starters or Targets? (S/T): ", end ="")
    selection = input().upper()

    if selection == "S":
        print("--- Possible starters ---")
        for i in range(len(starters)):
            print(str(i) + " - " + starters[i])

        selection = -1
        while selection > i or selection < 0:
            print("Select starter: ", end ="")
            selection = int(input())

        print("Your selection: " + targets[selection])
        
        for route in routes:
            if starters[selection] == route[0]:
                print(route[0] + "\t>\t" + route[1] + "\t>\t" + route[2])
        
        sys.exit(0)

    elif selection == "T":
        print("--- Possible targets ---")
        for i in range(len(targets)):
            print(str(i) + " - " + targets[i])

        selection = int(-1)
        while selection > i or selection < 0:
            print("Select target: ", end ="")
            try:
                selection = int(input())
            except Exception as e:
                sys.exit(e)

        print("Your selection: " + targets[selection])

        for route in routes:
            if targets[selection] == route[2]:
                print(route[0] + "\t>\t" + route[1] + "\t>\t" + route[2])

        sys.exit(0)
