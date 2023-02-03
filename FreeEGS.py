import json
import time
import discord
import requests
from asyncio import sleep
from os.path import isfile

def get_API(endpoint):
    r = requests.get(endpoint, headers = {'User-Agent': ARGS['useragent']})
    if r.status_code != 200:
        raise Exception('Error! non-200 response.')
    data = json.loads(r.text)
    return data

def updateDB(DB):
    with open(dbfile, 'wb') as f:
        f.seek(0)
        f.write(json.dumps(DB).encode('utf-8'))
    return

if __name__ == '__main__':
    intents = discord.Intents.default()
    intents.message_content = True
    client = discord.Client(intents=intents)
    
    argfile = './config.cfg'
    with open(argfile, 'r+') as f:
        ARGS = json.loads(f.read())
    
    dbfile = './DB.json'
    if not isfile(dbfile):
        DB = {}
        updateDB(DB)
    else:
        with open(dbfile, 'r+') as f:
            DB = json.loads(f.read())
else:
    print('FreeEGS bot is not running as main!')
    exit()

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')
    channel = client.get_channel(ARGS['announce_channel'])
    
    while True:
        try:
            r = get_API('https://store-site-backend-static-ipv4.ak.epicgames.com/freeGamesPromotions?locale=en-US&country=US&allowCountries=US')
            free_games = r['data']['Catalog']['searchStore']['elements']
        except: # if we except then try again later
            print(f'sleeping for {ARGS["check_interval"]} seconds')
            await sleep(ARGS['check_interval']) # sleep before retrying
            continue
        
        for game in free_games:
            NOW = int(time.time())
            TITLE = game['title']
            ID = game['id']
            
            # get product slug
            SLUG = None
            for i in game['catalogNs']['mappings']:
                SLUG = i['pageSlug']
            for i in game['offerMappings']:
                SLUG = i['pageSlug']
            for i in game['customAttributes']:
                if i['key'] == 'com.epicgames.app.productSlug':
                    SLUG = i['value']
            
            # make url from slug
            URL = '(no url found)'
            if SLUG != None:
                URL = f'https://store.epicgames.com/en-US/p/{SLUG}'
            
            # check if is *currently* free
            currentlyFree = False
            if game['price']['totalPrice']['discountPrice'] == 0:
                currentlyFree = True
            
            isNewlyFree = False
            if ID in DB:
                elapsed = NOW - DB[ID]['last_time_free']
                # free_interval = 605460 # 1 week + 11 mins
                free_interval = 7776000 # 90 days
                if elapsed >= free_interval:
                    isNewlyFree = True
                else:
                    print(f'{TITLE} is still free')
            else:
                isNewlyFree = True
            
            if isNewlyFree and currentlyFree:
                # update db
                DB[ID] = {'last_time_free': NOW}
                updateDB(DB)
                print(f'{TITLE} is now free!')
                message = f'<@&{ARGS["ping_role"]}> {TITLE} is free on Epic Games!\n{URL}'
                await channel.send(message)
        
        # exit()
        print(f'sleeping for {ARGS["check_interval"]} seconds')
        await sleep(ARGS['check_interval'])
    
client.run(ARGS['TOKEN'])
