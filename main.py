from graphqlclient import GraphQLClient
import json
import math

authToken = 'e811f56a095137f23e2b991e6a902935'
apiVersion = 'alpha'
client = GraphQLClient('https://api.start.gg/gql/' + apiVersion)
client.inject_token('Bearer ' + authToken)

def removeWhiteSpace(str_):
  while " " in str_:
    str_ = str_.replace(" ", "")
  return str_

def removeDuplicates(list_):
  l = []
  for obj in list_:
    if obj not in l:
      l.append(obj)
  return l

def getTopXOfRaves(x=8):
    tournaments = client.execute("""
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
    }) {
    nodes{
        id
        name
        slug
        events{
            name
            rulesetId
            numEntrants
            standings(query: {
                perPage: %s,
                page: 1
                }){
                    nodes {
                        placement
                        entrant {
                            id
                            name
                        }
                    }
                }
            }
        }
        }
    }
    """ % x,
    {
        "perPage": 50,
        "coordinates": "39.97917121010257, -75.15532016137276",
        "radius": "1mi"
    })

    return json.loads(tournaments)['data']['tournaments']['nodes']

def getTopXListFromRave(rave):
    topx = []
    for entrant in rave:
        topx.append({"placement": entrant['placement'], "tag": removeWhiteSpace(entrant['entrant']['name'].split("|")[-1])})
    return topx
        
def makeRankings(pointsFormula=lambda x: 1/x, top=8, stacking=True, rounding=3, requirement=2):
    """
    top: only count the people who have made top 8, top 16, or top 500

    pointsFormula: the formula that you plug your placements into to be added to your score

    stacking: people with the same points get the same rank

    rounding: scores get rounded by this number

    requirement: how many tournaments are required for them to be counted
    
    
    """


    data = {}
    raves = getTopXOfRaves(x=top)
    numRaves = 0
    for rave in raves:
        for event in rave['events']:
            if event['rulesetId'] == 126 and event['standings']:
                numRaves += 1
                topx = getTopXListFromRave(event['standings']['nodes'])
                for player in topx:
                    if player['tag'] not in data: # i love python so much
                        data[player['tag']] = {'score': 0, 'placements': []}
                    data[player['tag']]['score'] += round(pointsFormula(player['placement']), rounding)
                    data[player['tag']]['placements'].append(player['placement'])       

    rankings = {}

    filteredData = dict(filter(lambda player: len(player[1]['placements']) >= requirement, list(data.items())))

    sortedData = sorted(filteredData.items(), key=lambda x: x[1]['score'], reverse=True)

    rank = 1
    i = 0
    previousPlayer = None
    while(i < len(sortedData)):

        player = sortedData[i]

        dictPlayer = {player[0]: player[1]}

        if stacking:
            if previousPlayer and player[1]['score'] == previousPlayer[1]['score']:
                rank -= 1
        if rank not in rankings:
            rankings[rank] = []
        
        rankings[rank].append(dictPlayer)
        
        previousPlayer = player

        rank += 1
        i += 1

    return rankings

def printPRList(rankings):
    print("\n")
    for rank in rankings:
        print(f"{rank}: \n", end='')
        for player in rankings[rank]:
            data = list(player.items())[0]
            print(f"\t{data[0]}: {data[1]}")
    print("\n")

rankings = makeRankings(
        top=32, 
        pointsFormula=lambda x: 1/x, 
        stacking=True,
        rounding=100, 
        requirement=2
    )

printPRList(rankings)

"""
What this algorithm does is look at the top 8 (or top 16 or top whatever you choose) of every rave and counts each player

It then takes every player's result, puts it into a formula (right now i have 1/x but this can change) and adds that point
to their 'score'

Then the algorithm sorts by who has the most points and that's your pr

What this effectively does is reward players for making top 8 consistenly and exponentially increases their score by 
how far they go within top 8

Right now it doesn't track anything else - no head to heads, no bad losses or wins, just pure results. This is flawed,
of course, but I could inplement this if people really want me to.

----------------------------------------------------------------------------

An obvious result of this flaw is TerraBoy's placement. TerraBoy is obviously top 5, probably even top 3 by opinion,
but because of DQs and not giving a shit he's (as I'm writing this) 17th, which is the lowest on the list. There's also
key who is 100% top 2 but because (as he said) the rave doesn't count for anything (before I made this) he also didn't
give a shit and doesn't compete/throws. 

If we introduce this system to the rave and start tracking what happens after I think it could make the list a lot
more accurate. Or if the rave is just to be a chill no pressure environment that's also completely fine and this project
could just be a 'for fun' thing. It's up to the Temple smash community!
"""