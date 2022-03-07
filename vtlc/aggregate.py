import argparse
import csv
import gc
import hashlib
import os
from datetime import datetime, timezone
from os.path import join

import pandas as pd
import pymongo
from dateutil.relativedelta import relativedelta
from tqdm import tqdm

from vtlc.constants import RAW_DATA_DIR
from vtlc.util.currency import normalizeCurrency
from vtlc.util.message import replaceEmojiWithReplacement
# from vtlc.util.message import convertRawMessageToString

MONGODB_URI = os.environ['MONGODB_URI']

CHAT_COLUMNS = [
    'timestamp',
    'id',
    'authorName',
    'authorChannelId',
    'body',
    'membership',
    'isModerator',
    'isVerified',
    'videoId',
    'channelId',
]

SC_COLUMNS = [
    'timestamp',
    'id',
    'authorName',
    'authorChannelId',
    'body',
    'amount',
    'currency',
    'color',
    'significance',
    'videoId',
    'channelId',
]

# epoch time
genesisEpoch = datetime.fromtimestamp(1610687733293 / 1000, timezone.utc)

# handle missing columns incident before 2021-03-13T21:23:14.000Z
missingMembershipAndSuperchatColumnEpoch = datetime.fromtimestamp(
    1615670594000 / 1000, timezone.utc)

# handle missing membership column in chats and banneractions incident
# between {"$date":"2022-01-20T23:47:21.029Z"} and {"$date":"2022-01-22T06:07:07.305Z"}
missingMembershipColumn2022Start = datetime.fromtimestamp(
    1642722441029 / 1000, timezone.utc)
missingMembershipColumn2022End = datetime.fromtimestamp(
    1642831627305 / 1000, timezone.utc)


def accumulateChat(collection, recent=-1, ignoreHalfway=False):
    print('# of chats', collection.estimated_document_count())

    if recent >= 0:
        print(f'Processing chats past {recent} month(s)')
    if ignoreHalfway:
        print('While ignoring this month')

    def handleCursor(cursor, total, filename):
        CHAT_PATH = join(RAW_DATA_DIR, filename)
        chatFp = open(CHAT_PATH, 'w', encoding='UTF8')
        chatWriter = csv.writer(chatFp)
        chatWriter.writerow(CHAT_COLUMNS)

        pbar = tqdm(total=total, mininterval=1, desc=filename)

        for doc in cursor:
            pbar.update(1)

            # https://pandas.pydata.org/pandas-docs/stable/user_guide/timeseries.html
            timestamp = doc['timestamp'].replace(tzinfo=timezone.utc)

            chatId = doc['id']
            authorChannelId = doc['authorChannelId']
            authorName = doc['authorName'] if 'authorName' in doc else None

            try:
                text = replaceEmojiWithReplacement(doc['message'])
            except Exception as e:
                # ignore doc missing a message
                print(doc['_id'], 'lacks message (ignored)')
                continue

            videoId = doc['originVideoId']
            channelId = doc['originChannelId']

            membership = doc[
                'membership'] if 'membership' in doc else 'non-member'

            isMembershipAndSuperchatInfoMissing = (
                timestamp < missingMembershipAndSuperchatColumnEpoch) or (
                    (timestamp > missingMembershipColumn2022Start) and
                    (timestamp < missingMembershipColumn2022End))
            if isMembershipAndSuperchatInfoMissing:
                membership = 'unknown'

            isModerator = 1 if doc['isModerator'] else 0
            isVerified = 1 if doc['isVerified'] else 0

            chatWriter.writerow([
                timestamp.isoformat(),
                chatId,
                authorName,
                authorChannelId,
                text,
                membership,
                isModerator,
                isVerified,
                videoId,
                channelId,
            ])

        # bulk write
        # chat_df = pd.DataFrame(chat_list, columns=CHAT_COLUMNS)
        # chat_df.to_parquet(CHAT_PATH)
        # sc_df = pd.DataFrame(sc_list, columns=SC_COLUMNS)
        # sc_df.to_parquet(SC_PATH)
        chatFp.close()
        pbar.close()

    now = datetime.utcnow().replace(tzinfo=timezone.utc)

    if recent >= 0:
        recent = now + relativedelta(months=-recent)
        cm = datetime(recent.year, recent.month, 1, tzinfo=timezone.utc)
    else:
        cm = genesisEpoch

    untilDate = now + relativedelta(months=-1 if ignoreHalfway else 0)

    while cm < untilDate:
        nm = cm + relativedelta(months=+1)
        nm = datetime(nm.year, nm.month, 1, tzinfo=timezone.utc)
        filename = f'chats_{cm.strftime("%Y-%m")}.csv'
        print('data range:', cm, '<= X <', nm)
        print('target:', filename)

        query = {'timestamp': {'$gte': cm, '$lt': nm}}
        cursor = collection.find(query)
        cursorTotal = collection.count_documents(query)
        handleCursor(cursor, cursorTotal, filename)

        gc.collect()

        # update start epoch
        cm = nm


def accumulateSuperChat(collection, recent=-1, ignoreHalfway=False):
    print('# of superchats', collection.estimated_document_count())

    if recent >= 0:
        print(f'Processing chats past {recent} month(s)')
    if ignoreHalfway:
        print('While ignoring this month')

    def handleCursor(cursor, total, filename):
        superchatFp = open(join(RAW_DATA_DIR, filename), 'w', encoding='UTF8')
        superchatWriter = csv.writer(superchatFp)
        superchatWriter.writerow(SC_COLUMNS)

        pbar = tqdm(total=total, mininterval=1, desc=filename)

        for doc in cursor:
            pbar.update(1)

            # https://pandas.pydata.org/pandas-docs/stable/user_guide/timeseries.html
            timestamp = doc['timestamp'].replace(tzinfo=timezone.utc)

            chatId = doc['id']
            authorChannelId = doc['authorChannelId']
            authorName = doc['authorName'] if 'authorName' in doc else None

            text = replaceEmojiWithReplacement(
                doc['message']) if doc['message'] else None

            videoId = doc['originVideoId']
            channelId = doc['originChannelId']
            amount = doc['purchaseAmount']
            currency = doc['currency']
            color = doc['color']
            significance = doc['significance']

            superchatWriter.writerow([
                timestamp.isoformat(),
                chatId,
                authorName,
                authorChannelId,
                text,
                amount,
                currency,
                color,
                significance,
                videoId,
                channelId,
            ])

        superchatFp.close()
        pbar.close()

    now = datetime.utcnow().replace(tzinfo=timezone.utc)

    if recent >= 0:
        recent = now + relativedelta(months=-recent)
        cm = datetime(recent.year, recent.month, 1, tzinfo=timezone.utc)
    else:
        cm = genesisEpoch

    untilDate = now + relativedelta(months=-1 if ignoreHalfway else 0)

    while cm < untilDate:
        nm = cm + relativedelta(months=+1)
        nm = datetime(nm.year, nm.month, 1, tzinfo=timezone.utc)
        filename = f'superchats_{cm.strftime("%Y-%m")}.csv'
        print('data range:', cm, '<= X <', nm)
        print('target:', filename)

        query = {'timestamp': {'$gte': cm, '$lt': nm}}
        cursor = collection.find(query)
        cursorTotal = collection.count_documents(query)
        handleCursor(cursor, cursorTotal, filename)

        # update start epoch
        cm = nm


def accumulateBan(col):
    print('# of ban', col.estimated_document_count())
    cursor = col.find()
    f = open(join(RAW_DATA_DIR, 'ban_events.csv'), 'w', encoding='UTF8')
    writer = csv.writer(f)

    columns = [
        'timestamp',
        'authorChannelId',
        'videoId',
        'channelId',
    ]
    writer.writerow(columns)

    for doc in cursor:
        authorChannelId = doc['channelId']
        videoId = doc['originVideoId']
        channelId = doc['originChannelId']
        timestamp = doc['timestamp'].replace(
            tzinfo=timezone.utc).isoformat() if 'timestamp' in doc else None

        writer.writerow([
            timestamp,
            authorChannelId,
            videoId,
            channelId,
        ])

    f.close()


def accumulateDeletion(col):
    print('# of deletion', col.estimated_document_count())
    cursor = col.find()
    f = open(join(RAW_DATA_DIR, 'deletion_events.csv'), 'w', encoding='UTF8')
    writer = csv.writer(f)

    columns = [
        'timestamp',
        'id',
        'retracted',
        'videoId',
        'channelId',
    ]
    writer.writerow(columns)

    for doc in cursor:
        chatId = doc['targetId']
        videoId = doc['originVideoId']
        channelId = doc['originChannelId']
        retracted = 1 if doc['retracted'] else 0
        timestamp = doc['timestamp'].replace(
            tzinfo=timezone.utc).isoformat() if 'timestamp' in doc else None

        writer.writerow([
            timestamp,
            chatId,
            retracted,
            videoId,
            channelId,
        ])

    f.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='dataset generator')
    parser.add_argument('-R', '--recent', type=int, default=0)
    parser.add_argument('-I', '--ignore-halfway', action='store_true')
    args = parser.parse_args()

    print('dataset: ' + RAW_DATA_DIR)

    client = pymongo.MongoClient(MONGODB_URI)
    db = client.vespa

    accumulateChat(db.chats,
                   recent=args.recent,
                   ignoreHalfway=args.ignore_halfway)
    accumulateSuperChat(db.superchats,
                        recent=args.recent,
                        ignoreHalfway=args.ignore_halfway)
    accumulateDeletion(db.deleteactions)
    accumulateBan(db.banactions)
