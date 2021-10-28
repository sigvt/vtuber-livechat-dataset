import gc
import argparse
import csv
import hashlib
import json
import os
import shutil
from datetime import datetime, timezone
from os.path import join

import pandas as pd
import pymongo
from dateutil.relativedelta import relativedelta
from tqdm import tqdm

from vtlc.constants import DATASET_DIR, DATASET_DIR_FULL
from vtlc.util.currency import normalizeCurrency
from vtlc.util.message import convertRawMessageToString
from vtlc.util.superchat import \
    convertHeaderBackgroundColorToColorAndSignificance

ANONYMIZATION_SALT = os.environ['ANONYMIZATION_SALT']
MONGODB_URI = os.environ['MONGODB_URI']

CHAT_COLUMNS = [
    'timestamp',
    'authorName',
    'body',
    'membership',
    'isModerator',
    'isVerified',
    'id',
    'authorChannelId',
    'videoId',
    'channelId',
]

SC_COLUMNS = [
    'timestamp',
    'authorName',
    'body',
    'amount',
    'currency',
    'color',
    'significance',
    'id',
    'authorChannelId',
    'videoId',
    'channelId',
]

# epoch time
genesisEpoch = datetime.fromtimestamp(1610687733293 / 1000, timezone.utc)

# handle missing columns cases before 2021-03-13T21:23:14.000Z
missingMembershipAndSuperchatColumnEpoch = datetime.fromtimestamp(
    1615670594000 / 1000, timezone.utc)


def accumulateChat(collection, recent=-1, ignoreHalfway=False):
    print('# of chats', collection.estimated_document_count())

    if recent >= 0:
        print(f'Processing chats past {recent} month(s)')
    if ignoreHalfway:
        print('While ignoring this month')

    def handleCursor(cursor, total, filename):
        CHAT_PATH = join(DATASET_DIR_FULL, filename)
        chatFp = open(CHAT_PATH, 'w', encoding='UTF8')
        chatWriter = csv.writer(chatFp)
        chatWriter.writerow(CHAT_COLUMNS)

        pbar = tqdm(total=total, mininterval=1, desc=filename)

        for doc in cursor:
            pbar.update(1)

            # https://pandas.pydata.org/pandas-docs/stable/user_guide/timeseries.html
            timestamp = doc['timestamp'].replace(tzinfo=timezone.utc)

            # anonymize id and author channel id with grain of salt
            chatId = hashlib.sha1(
                (doc['id'] + ANONYMIZATION_SALT).encode()).hexdigest()
            authorChannelId = hashlib.sha1(
                (doc['authorChannelId'] +
                 ANONYMIZATION_SALT).encode()).hexdigest()
            authorName = doc['authorName'] if 'authorName' in doc else None

            text = convertRawMessageToString(doc['message'] if 'message' in
                                             doc else doc['rawMessage'])

            videoId = doc['originVideoId']
            channelId = doc['originChannelId']

            if 'membership' in doc:
                if 'since' in doc['membership']:
                    membership = doc['membership']['since']
                else:
                    membership = 'less than 1 month'
            else:
                membership = 'non-member'

            isMembershipAndSuperchatInfoMissing = timestamp < missingMembershipAndSuperchatColumnEpoch
            if isMembershipAndSuperchatInfoMissing:
                membership = 'unknown'

            # skip chat with empty body
            if not text:
                continue

            isModerator = 1 if doc['isModerator'] else 0
            isVerified = 1 if doc['isVerified'] else 0

            chatWriter.writerow([
                timestamp.isoformat(),
                authorName,
                text,
                membership,
                isModerator,
                isVerified,
                chatId,
                authorChannelId,
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
        superchatFp = open(join(DATASET_DIR_FULL, filename),
                           'w',
                           encoding='UTF8')
        superchatWriter = csv.writer(superchatFp)
        superchatWriter.writerow(SC_COLUMNS)

        pbar = tqdm(total=total, mininterval=1, desc=filename)

        for doc in cursor:
            pbar.update(1)

            # https://pandas.pydata.org/pandas-docs/stable/user_guide/timeseries.html
            timestamp = doc['timestamp'].replace(tzinfo=timezone.utc)

            # anonymize id and author channel id with grain of salt
            chatId = hashlib.sha1(
                (doc['id'] + ANONYMIZATION_SALT).encode()).hexdigest()
            authorChannelId = hashlib.sha1(
                (doc['authorChannelId'] +
                 ANONYMIZATION_SALT).encode()).hexdigest()
            authorName = doc['authorName'] if 'authorName' in doc else None

            text = convertRawMessageToString(doc['message'])

            videoId = doc['originVideoId']
            channelId = doc['originChannelId']
            amount = doc['purchaseAmount']
            currency = normalizeCurrency(doc['currency'])
            color = doc['color']
            significance = doc['significance']

            superchatWriter.writerow([
                timestamp.isoformat(),
                authorName,
                text,
                amount,
                currency,
                color,
                significance,
                chatId,
                authorChannelId,
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
    f = open(join(DATASET_DIR_FULL, 'ban_events.csv'), 'w', encoding='UTF8')
    writer = csv.writer(f)

    columns = [
        'timestamp',
        'authorChannelId',
        'videoId',
        'channelId',
    ]
    writer.writerow(columns)

    for doc in cursor:
        # anonymize author channel id with grain of salt
        authorChannelId = hashlib.sha1(
            (doc['channelId'] + ANONYMIZATION_SALT).encode()).hexdigest()
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
    f = open(join(DATASET_DIR_FULL, 'deletion_events.csv'),
             'w',
             encoding='UTF8')
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
        # anonymize author channel id with grain of salt
        chatId = hashlib.sha1(
            (doc['targetId'] + ANONYMIZATION_SALT).encode()).hexdigest()
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

    print('dataset: ' + DATASET_DIR_FULL)

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
