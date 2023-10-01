from graphqlclient import GraphQLClient
import json
import math

authToken = 'e811f56a095137f23e2b991e6a902935'
apiVersion = 'alpha'
client = GraphQLClient('https://api.start.gg/gql/' + apiVersion)
client.inject_token('Bearer ' + authToken)

def getTopXOfRaves(x):
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
        topx.append({"placement": entrant['placement'], "tag": entrant['entrant']['name']})
    return topx
        
def makeRankings(pointsFormula=lambda x: 1/x, top=8):
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
                    data[player['tag']]['score'] += round(pointsFormula(player['placement']), 3)
                    data[player['tag']]['placements'].append(player['placement'])
    
    rankings = sorted(data.items(), key=lambda x: x[1]['score'], reverse=True)
    return rankings

def parseRankings(rankings):
    msg = "\n"
    rank = 1
    while(rank-1 < rankings.__len__()):
        player = rankings[rank-1]
        msg += f"{rank}: {player[0]} - score: {round(player[1]['score'], 2)} - placements: {sorted(player[1]['placements'], reverse=False)}\n"
        rank += 1
    return msg


rankings = makeRankings(top=32)
print(parseRankings(rankings))

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