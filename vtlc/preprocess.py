import requests
import csv
from os.path import join, dirname

DATA_DIR = join(dirname(__file__), '..', 'datasets', 'vtuber-livechat')

# https://vlueprint.org/

# prefix vlueprint: <https://vlueprint.org/schema/>
# prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#>

# select ?CHANNEL ?NAME ?ORGLABEL {
#   ?uri rdf:type vlueprint:VirtualBeing.
#   ?uri rdfs:label ?NAME.
#   ?uri vlueprint:youtubeChannelId ?CHANNEL.
#   OPTIONAL {
#     ?uri vlueprint:belongTo ?orgUri.
#     ?orgUri rdfs:label ?ORGLABEL.
#   }.
# }


def get_channels(offset=0, limit=100):
    payload = {
        'limit': 100,
        'offset': offset,
        'org': "All Vtubers",
        'type': "vtuber",
        'sort': 'suborg',
        'order': 'asc'
    }
    res = requests.get('https://holodex.net/api/v2/channels', params=payload)
    data = res.json()

    if len(data) == 0:
        return data

    return data + get_channels(offset + limit)


def create_channel_index():
    fp = open(join(DATA_DIR, 'channels.csv'), 'w', encoding='UTF8')
    writer = csv.writer(fp)

    writer.writerow([
        'channelId',
        'name',
        'name.en',
        'affiliation',
        'group',
        'subscriptionCount',
        'videoCount',
    ])

    for channel in get_channels():
        writer.writerow([
            channel['id'],
            channel['name'],
            channel['english_name'] or channel['name'],
            channel['org'] or 'Independents',
            channel['group'],
            channel['subscriber_count'],
            channel['video_count'],
        ])

    fp.close()


if __name__ == '__main__':
    create_channel_index()
