import argparse
import calendar
import csv
import hashlib
import os
from datetime import datetime, timezone
from os.path import dirname, join

import pandas as pd
import pymongo
from dateutil.relativedelta import relativedelta

ANONYMIZATION_SALT = os.environ.get('ANONYMIZATION_SALT')
MONGODB_URI = os.environ.get('MONGODB_URI')
DATA_DIR = join(dirname(__file__), '..', 'datasets/vtuber-livechat')

superchatColors = {
    '4279592384': 'blue',
    '4278237396': 'lightblue',
    '4278239141': 'green',
    '4294947584': 'yellow',
    '4293284096': 'orange',
    '4290910299': 'magenta',
    '4291821568': 'red',
}

superchatSignificance = {
    'blue': 1,
    'lightblue': 2,
    'green': 3,
    'yellow': 4,
    'orange': 5,
    'magenta': 6,
    'red': 7,
}

# epoch time
genesisEpoch = datetime.fromtimestamp(1610687733293 / 1000, timezone.utc)

# handle incorrect superchat amount case before 2021-03-15T23:19:32.123Z
incorrectSuperchatEpoch = datetime.fromtimestamp(1615850372123 / 1000,
                                                 timezone.utc)

# handle missing columns cases before 2021-03-13T21:23:14.000Z
missingMembershipAndSuperchatColumnEpoch = datetime.fromtimestamp(
    1615670594000 / 1000, timezone.utc)
# missingMembershipAndSuperchatColumnEpoch < incorrectSuperchatEpoch


def convertRawMessageToString(rawMessage):

    def handler(run):
        msgType = list(run.keys())[0]
        if msgType == 'text':
            return run[msgType]
        elif msgType == 'emoji':
            # label = run[msgType]['image']['accessibility']['accessibilityData'][
            #     'label']
            """
            Replacement character U+FFFD
            https://en.wikipedia.org/wiki/Specials_(Unicode_block)#Replacement_character
            """
            return "\uFFFD"
        else:
            raise 'Invalid type: ' + msgType

    return "".join([handler(run) for run in rawMessage])


def accumulateChat(col, recent=-1, ignoreHalfway=False):
    print('# of chats', col.estimated_document_count())

    if recent >= 0:
        print(f'Processing chats past {recent} month(s)')
    if ignoreHalfway:
        print('While ignoring this month')

    def handleCursor(cursor, filename, sc_filename):
        chatFp = open(join(DATA_DIR, filename), 'w', encoding='UTF8')
        chatWriter = csv.writer(chatFp)
        chatWriter.writerow([
            'timestamp',
            'body',
            'membership',
            'isModerator',
            'isVerified',
            'id',
            'channelId',
            'originVideoId',
            'originChannelId',
        ])

        superchatFp = open(join(DATA_DIR, sc_filename), 'w', encoding='UTF8')
        superchatWriter = csv.writer(superchatFp)
        superchatWriter.writerow([
            'timestamp',
            'amount',
            'currency',
            'significance',
            'color',
            'body',
            'id',
            'channelId',
            'originVideoId',
            'originChannelId',
        ])

        for doc in cursor:
            # https://pandas.pydata.org/pandas-docs/stable/user_guide/timeseries.html
            timestamp = doc['timestamp'].replace(tzinfo=timezone.utc)

            # anonymize id and author channel id with grain of salt
            id = hashlib.sha1(
                (doc['id'] + ANONYMIZATION_SALT).encode()).hexdigest()
            channelId = hashlib.sha1((doc['authorChannelId'] +
                                      ANONYMIZATION_SALT).encode()).hexdigest()

            text = convertRawMessageToString(doc['rawMessage'])

            originVideoId = doc['originVideoId']
            originChannelId = doc['originChannelId']

            isSuperchat = 1 if 'purchase' in doc else 0

            # handle superchat
            if isSuperchat:
                isIncorrectSuperchat = timestamp < incorrectSuperchatEpoch

                if not isIncorrectSuperchat:
                    amount = doc['purchase']['amount']
                    currency = doc['purchase']['currency']
                    bgcolor = superchatColors[doc['purchase']
                                              ['headerBackgroundColor']]

                    significance = superchatSignificance[bgcolor]

                    superchatWriter.writerow([
                        timestamp.isoformat(),
                        amount,
                        currency,
                        significance,
                        bgcolor,
                        text,
                        id,
                        channelId,
                        originVideoId,
                        originChannelId,
                    ])

                continue

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
                text,
                membership,
                isModerator,
                isVerified,
                id,
                channelId,
                originVideoId,
                originChannelId,
            ])

        chatFp.close()
        superchatFp.close()

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
        sc_filename = f'superchats_{cm.strftime("%Y-%m")}.csv'
        print('data range:', cm, '<= X <', nm)
        print('target:', filename, 'and', sc_filename)

        cursor = col.find({'timestamp': {'$gte': cm, '$lt': nm}})
        handleCursor(cursor, filename, sc_filename)

        # update start epoch
        cm = nm


def accumulateBan(col):
    print('# of ban', col.estimated_document_count())
    cursor = col.find()
    f = open(join(DATA_DIR, 'ban_events.csv'), 'w', encoding='UTF8')
    writer = csv.writer(f)

    columns = [
        'timestamp',
        'channelId',
        'originVideoId',
        'originChannelId',
    ]
    writer.writerow(columns)

    for doc in cursor:
        # anonymize author channel id with grain of salt
        channelId = hashlib.sha1(
            (doc['channelId'] + ANONYMIZATION_SALT).encode()).hexdigest()
        originVideoId = doc['originVideoId']
        originChannelId = doc['originChannelId']
        timestamp = doc['timestamp'].replace(
            tzinfo=timezone.utc).isoformat() if 'timestamp' in doc else None

        writer.writerow([
            timestamp,
            channelId,
            originVideoId,
            originChannelId,
        ])

    f.close()


def accumulateDeletion(col):
    print('# of deletion', col.estimated_document_count())
    cursor = col.find()
    f = open(join(DATA_DIR, 'deletion_events.csv'), 'w', encoding='UTF8')
    writer = csv.writer(f)

    columns = [
        'timestamp',
        'id',
        'retracted',
        'originVideoId',
        'originChannelId',
    ]
    writer.writerow(columns)

    for doc in cursor:
        # anonymize author channel id with grain of salt
        id = hashlib.sha1(
            (doc['targetId'] + ANONYMIZATION_SALT).encode()).hexdigest()
        originVideoId = doc['originVideoId']
        originChannelId = doc['originChannelId']
        retracted = 1 if doc['retracted'] else 0
        timestamp = doc['timestamp'].replace(
            tzinfo=timezone.utc).isoformat() if 'timestamp' in doc else None

        writer.writerow([
            timestamp,
            id,
            retracted,
            originVideoId,
            originChannelId,
        ])

    f.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='dataset generator')
    parser.add_argument('-R', '--recent', type=int, default=1)
    parser.add_argument('-I', '--ignore-halfway', action='store_true')
    args = parser.parse_args()
    print('set base dir to', DATA_DIR)

    client = pymongo.MongoClient(MONGODB_URI)
    db = client.vespa

    accumulateChat(db.chats,
                   recent=args.recent,
                   ignoreHalfway=args.ignore_halfway)
    accumulateBan(db.banactions)
    accumulateDeletion(db.deleteactions)
