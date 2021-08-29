import csv
from os.path import join
import shutil

import requests

from vtlc.constants import DATASET_DIR, DATASET_DIR_FULL


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
    fp = open(join(DATASET_DIR_FULL, 'channels.csv'), 'w', encoding='UTF8')
    writer = csv.writer(fp)

    writer.writerow([
        'channelId', 'name', 'name.en', 'affiliation', 'group',
        'subscriptionCount', 'videoCount', 'photo'
    ])

    for channel in get_channels():
        writer.writerow([
            channel['id'], channel['name'], channel['english_name'] or
            channel['name'], channel['org'] or 'Independents', channel['group'],
            channel['subscriber_count'] or 0, channel['video_count'] or 0,
            channel['photo']
        ])

    fp.close()


if __name__ == '__main__':
    print('dataset: ' + DATASET_DIR_FULL)

    create_channel_index()

    shutil.copy(join(DATASET_DIR_FULL, 'channels.csv'), DATASET_DIR)
