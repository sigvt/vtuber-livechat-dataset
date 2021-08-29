import argparse
import csv
import hashlib
import os
from datetime import datetime, timezone
from os.path import join

import pymongo
from dateutil.relativedelta import relativedelta

from vtlc.constants import DATASET_DIR_FULL
from vtlc.util.message import convertRawMessageToString
from vtlc.util.superchat import \
    convertHeaderBackgroundColorToColorAndSignificance

ANONYMIZATION_SALT = os.environ['ANONYMIZATION_SALT']
MONGODB_URI = os.environ['MONGODB_URI']

# epoch time
genesisEpoch = datetime.fromtimestamp(1610687733293 / 1000, timezone.utc)

# handle incorrect superchat amount case before 2021-03-15T23:19:32.123Z
incorrectSuperchatEpoch = datetime.fromtimestamp(1615850372123 / 1000,
                                                 timezone.utc)

# handle missing columns cases before 2021-03-13T21:23:14.000Z
missingMembershipAndSuperchatColumnEpoch = datetime.fromtimestamp(
    1615670594000 / 1000, timezone.utc)
# missingMembershipAndSuperchatColumnEpoch < incorrectSuperchatEpoch


def accumulateChat(col, recent=-1, ignoreHalfway=False):
    print('# of chats', col.estimated_document_count())

    if recent >= 0:
        print(f'Processing chats past {recent} month(s)')
    if ignoreHalfway:
        print('While ignoring this month')

    def handleCursor(cursor, filename, sc_filename):
        chatFp = open(join(DATASET_DIR_FULL, filename), 'w', encoding='UTF8')
        chatWriter = csv.writer(chatFp)
        chatWriter.writerow([
            'timestamp',
            'body',
            'membership',
            'isModerator',
            'isVerified',
            'id',
            'authorChannelId',
            'videoId',
            'channelId',
        ])

        superchatFp = open(join(DATASET_DIR_FULL, sc_filename),
                           'w',
                           encoding='UTF8')
        superchatWriter = csv.writer(superchatFp)
        superchatWriter.writerow([
            'timestamp',
            'amount',
            'currency',
            'color',
            'significance',
            'body',
            'id',
            'authorChannelId',
            'videoId',
            'channelId',
        ])

        for doc in cursor:
            # https://pandas.pydata.org/pandas-docs/stable/user_guide/timeseries.html
            timestamp = doc['timestamp'].replace(tzinfo=timezone.utc)

            # anonymize id and author channel id with grain of salt
            chatId = hashlib.sha1(
                (doc['id'] + ANONYMIZATION_SALT).encode()).hexdigest()
            authorChannelId = hashlib.sha1(
                (doc['authorChannelId'] +
                 ANONYMIZATION_SALT).encode()).hexdigest()

            text = convertRawMessageToString(doc['message'] if 'message' in
                                             doc else doc['rawMessage'])

            videoId = doc['originVideoId']
            channelId = doc['originChannelId']

            isSuperchat = 1 if 'purchase' in doc else 0

            # handle legacy superchat
            if isSuperchat:
                isIncorrectSuperchat = timestamp < incorrectSuperchatEpoch

                if not isIncorrectSuperchat:
                    amount = doc['purchase']['amount']
                    currency = doc['purchase']['currency']
                    [color, significance
                    ] = convertHeaderBackgroundColorToColorAndSignificance(
                        doc['purchase']['headerBackgroundColor'])

                    superchatWriter.writerow([
                        timestamp.isoformat(),
                        amount,
                        currency,
                        color,
                        significance,
                        text,
                        chatId,
                        authorChannelId,
                        videoId,
                        channelId,
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
                chatId,
                authorChannelId,
                videoId,
                channelId,
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


def accumulateSuperChat(col, recent=-1, ignoreHalfway=False):
    print('# of superchats', col.estimated_document_count())

    if recent >= 0:
        print(f'Processing chats past {recent} month(s)')
    if ignoreHalfway:
        print('While ignoring this month')

    def handleCursor(cursor, filename):
        # superchatFp = open(join(DATASET_DIR_FULL, filename), 'w', encoding='UTF8')
        superchatFp = open(join(DATASET_DIR_FULL, filename),
                           'a',
                           encoding='UTF8')
        superchatWriter = csv.writer(superchatFp)
        # superchatWriter.writerow([
        #     'timestamp',
        #     'amount',
        #     'currency',
        #     'color',
        #     'significance',
        #     'body',
        #     'id',
        #     'authorChannelId',
        #     'videoId',
        #     'channelId',
        # ])

        for doc in cursor:
            # https://pandas.pydata.org/pandas-docs/stable/user_guide/timeseries.html
            timestamp = doc['timestamp'].replace(tzinfo=timezone.utc)

            # anonymize id and author channel id with grain of salt
            chatId = hashlib.sha1(
                (doc['id'] + ANONYMIZATION_SALT).encode()).hexdigest()
            authorChannelId = hashlib.sha1(
                (doc['authorChannelId'] +
                 ANONYMIZATION_SALT).encode()).hexdigest()

            text = convertRawMessageToString(doc['message'])

            videoId = doc['originVideoId']
            channelId = doc['originChannelId']
            amount = doc['purchaseAmount']
            currency = doc['currency']
            color = doc['color']
            significance = doc['significance']

            superchatWriter.writerow([
                timestamp.isoformat(),
                amount,
                currency,
                color,
                significance,
                text,
                chatId,
                authorChannelId,
                videoId,
                channelId,
            ])

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
        filename = f'superchats_{cm.strftime("%Y-%m")}.csv'
        print('data range:', cm, '<= X <', nm)
        print('target:', filename)

        cursor = col.find({'timestamp': {'$gte': cm, '$lt': nm}})
        handleCursor(cursor, filename)

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
    accumulateBan(db.banactions)
    accumulateDeletion(db.deleteactions)
