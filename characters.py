from graphqlclient import GraphQLClient
import json
import math
from time import sleep
import matplotlib.pyplot as plt

authToken = 'e811f56a095137f23e2b991e6a902935'
apiVersion = 'alpha'
client = GraphQLClient('https://api.start.gg/gql/' + apiVersion)
client.inject_token('Bearer ' + authToken)
"""
{
  "Authorization": "Bearer e811f56a095137f23e2b991e6a902935"
}
"""

def addToDictionary(dictionary, key, val):
  if key not in dictionary:
    dictionary[key] = val
  else: 
    dictionary[key] += val

def mergeDicts(baseDict, valueDict):
   for key in valueDict:
      addToDictionary(baseDict, key, valueDict[key])
   

def getRaveIDs():
    raves = client.execute("""
        query Raves($perPage: Int, $coordinates: String!, $radius: String!){
        tournaments(query: {
        perPage: $perPage,
        filter: {
            location: {
                distanceFrom: $coordinates
                distance: $radius
            }
            afterDate: 1693540800
        }
        }){
        nodes{
            id
            name
        }
    }
    }""", 
    {
        "perPage": 50,
        "coordinates": "39.97917121010257, -75.15532016137276",
        "radius": "1mi"
    }
    )

    return json.loads(raves)['data']['tournaments']['nodes']

def getCharactersFromTournament(id_, page=1):
    characters = client.execute(
    """
    query getCharacterFromTournament($id: ID){
    tournaments(query: {
      filter: {
        id: $id
      }
    }){
    nodes{
      id
      name
      events(limit: 0, filter: {
            videogameId: [1386]
      }){
        name
        sets(page: %s, perPage: 50){
          pageInfo{
            totalPages
          }
          nodes{
            games{
              selections{
                character{
                  name
                }
              }
            }
          }
        }
      }
    }
  }
}
    """ % page,
    {
        "id": id_
    }
        )
    
    return json.loads(characters)

def parseSetsFromTourneyId(tourneyId):
  page = 1

  data = getCharactersFromTournament(tourneyId)['data']['tournaments']['nodes'][0]
  if data['events'] == []:
     return None
  
  setData = data['events'][0]['sets']
  sets = setData['nodes']
  totalPages = setData['pageInfo']['totalPages']
  while page < totalPages:
      page += 1
      data = getCharactersFromTournament(tourneyId, page)['data']['tournaments']['nodes'][0]
      sets += data['events'][0]['sets']['nodes']

  return sets

def getAllCharactersFromAllSets(sets):
    if not sets:
       return {}
    
    characters = {}
    for set_ in sets:
      if set_:
        selections = set_['games']
        if selections:
          for game in selections:
            charactersInGame = game['selections']
            for character in charactersInGame:
              char = character['character']['name']
              addToDictionary(characters, char, 1)
    return characters


def getAllCharactersFromAllRaves():
  allRaveCharacters = {}
  raves = []
  for rave in getRaveIDs():
    id_ = rave['id']
    raves.append(rave['name'])
    raveChars = getAllCharactersFromAllSets(parseSetsFromTourneyId(id_))
    mergeDicts(allRaveCharacters, raveChars)

  sortedChars = sorted(allRaveCharacters.items(), key=lambda x: x[1], reverse=False)
  return [sortedChars, raves]


def graphCharacters():
   data = getAllCharactersFromAllRaves()
   characters = dict(data[0])
   tournaments = data[1]

   characterNames = list(characters.keys())
   characterValues = list(characters.values())

   fig = plt.figure(figsize=(10, 5))
   plt.rcParams.update({'font.size': 8})
   rects = plt.barh(characterNames, characterValues)

   plt.title("Character usage at Temple Tournaments")

   plt.xlabel("Amount of times used (total number of games played as character)")
   plt.ylabel("Character")

   plt.margins(y=0)

   for rect in rects:
    plt.text(1.25 + rect.get_width(), rect.get_y()+0.5*rect.get_height(), # THANK YOU STACKOVERFLOW 🔥🔥🔥🔥
                  '%d' % int(rect.get_width()),
                  ha='center', va='center')
   print(tournaments)
   plt.show()

graphCharacters()