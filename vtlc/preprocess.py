import requests
import csv
from os.path import join, dirname

DATA_DIR = join(dirname(__file__), '..', 'data')


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
        'name_en',
        'affiliation',
        'group',
        'sub_count',
        'video_count',
    ])

    for channel in get_channels():
        print(channel['name'])
        writer.writerow([
            channel['id'],
            channel['name'],
            channel['english_name'],
            channel['org'],
            channel['group'],
            channel['subscriber_count'],
            channel['video_count'],
        ])

    fp.close()


if __name__ == '__main__':
    create_channel_index()