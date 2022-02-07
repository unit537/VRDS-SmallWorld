import json
import requests
from typing import List


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
    id: int
    name: str
    type: str
    desc: str
    atk: int
    card_def: int
    level: int
    race: str
    attribute: str
    archetype: str
    scale: int
    linkval: int
    linkmarkers: List[str]
    card_sets: List[CardSet]
    card_images: List[CardImage]
    card_prices: List[CardPrice]

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

def checkCardIsInDeck(target: Card):
    for card in deck:
        if target.id == card.id:
            return True
    return False

# Init deck
def initializeDeck():
    deckFile = open('deck.ydk')
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

# Verify two cards are legel for Small World requirement
def smallWorldLegal(cardA, cardB):
    similarities: int = 0

    if cardA.race == cardB.race:
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
                        # print(starter.name + "\t>\t" + bridge.name + "\t>\t" + target.name)

def findTargets():
    for route in routes:
        if route[2] not in targets:
            targets.append(route[2])

# Open cardDB
cardDB = open('cardinfo.php.json')
cardDB = json.load(cardDB)
initializeDeck()
findLongestCardNameInDeck()
formatCardNamesInDeck()
starter = deck[0]
findRoutes()
findTargets()

# Begin user prompts
print("Find routes by:\nS - Starters\nT - Targets")
print("How do you want to find routes? (S/T): ", end ="")
selection = input().upper()

if selection == "S":
    print("--- Possible starters ---")
    for i in range(len(starters)):
        print(str(i) + " - " + starters[i])

    print("Select starter: ", end ="")
    selection = int(input())

    for route in routes:
        if starters[selection] == route[0]:
            print(route[0] + "\t>\t" + route[1] + "\t>\t" + route[2])

elif selection == "T":
    print("--- Possible targets ---")
    for i in range(len(targets)):
        print(str(i) + " - " + targets[i])

    print("Select target: ", end ="")
    selection = int(input())

    print("Your selection: " + targets[selection])

    for route in routes:
        if targets[selection] == route[2]:
            print(route[0] + "\t>\t" + route[1] + "\t>\t" + route[2])
