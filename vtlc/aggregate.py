import csv
import hashlib
import os
from datetime import datetime, timezone
from os.path import dirname, join

import pandas as pd
import pymongo

ANONYMIZATION_SALT = os.environ.get('ANONYMIZATION_SALT')
MONGODB_URI = os.environ.get('MONGODB_URI')
DATA_DIR = join(dirname(__file__), '..', 'data')


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


def handleChat(col, skipLegacy=True):
    print('# of chats', col.estimated_document_count())

    if skipLegacy:
        print('skipping creating legacy dataset')

    incorrectSuperchatEpoch = datetime.fromtimestamp(1615850372123 / 1000)
    missingMembershipAndSuperchatColumnEpoch = datetime.fromtimestamp(
        1615670594000 / 1000)

    channels = pd.read_csv(join(DATA_DIR, 'channels.csv')).fillna("")

    if skipLegacy:
        # pipeline = [{'$skip': 60000000}]
        # cursor = col.aggregate(pipeline, allowDiskUse=True)
        cursor = col.find(
            {'timestamp': {
                '$gt': missingMembershipAndSuperchatColumnEpoch
            }})
    else:
        cursor = col.find()

        chatLegacyFp = open(join(DATA_DIR, 'chatLegacy.csv'),
                            'w',
                            encoding='UTF8')
        chatLegacyWriter = csv.writer(chatLegacyFp)
        chatLegacyWriter.writerow([
            'timestamp',
            'body',
            'isModerator',
            'isVerified',
            'originVideoId',
            'originChannelId',
            'id',
            'channelId',
        ])

    chatFp = open(join(DATA_DIR, 'chat.csv'), 'w', encoding='UTF8')
    superchatFp = open(join(DATA_DIR, 'superchat.csv'), 'w', encoding='UTF8')
    chatWriter = csv.writer(chatFp)
    superchatWriter = csv.writer(superchatFp)

    chatWriter.writerow([
        'timestamp',
        'body',
        'isModerator',
        'isVerified',
        'isSuperchat',
        'isMembership',
        'originVideoId',
        'originChannelId',
        'id',
        'channelId',
    ])

    superchatWriter.writerow([
        'timestamp',
        'amount',
        'currency',
        'significance',
        'color',
        'body',
        'originVideoId',
        'originChannel',
        'originAffiliation',
        'originGroup',
        'id',
        'channelId',
    ])

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

    for doc in cursor:
        # https://pandas.pydata.org/pandas-docs/stable/user_guide/timeseries.html
        if not 'timestamp' in doc:
            print(doc)
            continue
        timestamp = doc['timestamp']
        # datetime(2002, 10, 27, 14, 0).replace(tzinfo=timezone.utc).timestamp()

        # handle missing columns cases before 2021-03-13T21:23:14.000Z
        isMembershipAndSuperchatMissing = timestamp < missingMembershipAndSuperchatColumnEpoch

        if skipLegacy and isMembershipAndSuperchatMissing:
            continue

        # handle incorrect superchat amount case before 2021-03-15T23:19:32.123Z
        isIncorrectSuperchat = timestamp < incorrectSuperchatEpoch

        # anonymize id and author channel id with grain of salt
        id = hashlib.sha256(
            (doc['id'] + ANONYMIZATION_SALT).encode()).hexdigest()
        channelId = hashlib.sha256(
            (doc['authorChannelId'] + ANONYMIZATION_SALT).encode()).hexdigest()
        text = convertRawMessageToString(doc['rawMessage'])

        originVideoId = doc['originVideoId']
        originChannelId = doc['originChannelId']
        isSuperchat = 1 if 'purchase' in doc else 0
        isMembership = 1 if 'membership' in doc else 0
        isModerator = 1 if doc['isModerator'] else 0
        isVerified = 1 if doc['isVerified'] else 0

        if isSuperchat and not isIncorrectSuperchat:
            amount = doc['purchase']['amount']
            currency = doc['purchase']['currency']
            bgcolor = superchatColors[doc['purchase']['headerBackgroundColor']]
            significance = superchatSignificance[bgcolor]

            origin = channels[channels['channelId'] == originChannelId].iloc[0]
            originChannel = origin['name_en'] or origin['name']
            originAffiliation = origin['affiliation']
            originGroup = origin['group']

            superchatWriter.writerow([
                timestamp.replace(tzinfo=timezone.utc).isoformat(),
                amount,
                currency,
                significance,
                bgcolor,
                text,
                originVideoId,
                originChannel,
                originAffiliation,
                originGroup,
                id,
                channelId,
            ])

        if isMembershipAndSuperchatMissing:
            isMembership = None
            isSuperchat = 1 if text == '' else None

        if not isMembershipAndSuperchatMissing:
            chatWriter.writerow([
                timestamp.replace(tzinfo=timezone.utc).isoformat(),
                text,
                isModerator,
                isVerified,
                isSuperchat,
                isMembership,
                originVideoId,
                originChannelId,
                id,
                channelId,
            ])
        elif not skipLegacy:
            chatLegacyWriter.writerow([
                timestamp.replace(tzinfo=timezone.utc).isoformat(),
                text,
                isModerator,
                isVerified,
                originVideoId,
                originChannelId,
                id,
                channelId,
            ])

    chatFp.close()
    if not skipLegacy:
        chatLegacyFp.close()
    superchatFp.close()


def handleBan(col):
    print('# of ban', col.estimated_document_count())
    cursor = col.find()
    f = open(join(DATA_DIR, 'markedAsBanned.csv'), 'w', encoding='UTF8')
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
        channelId = hashlib.sha256(
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


def handleDeletion(col):
    print('# of deletion', col.estimated_document_count())
    cursor = col.find()
    f = open(join(DATA_DIR, 'markedAsDeleted.csv'), 'w', encoding='UTF8')
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
        id = hashlib.sha256(
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
    client = pymongo.MongoClient(MONGODB_URI)
    db = client.vespa

    handleChat(db.chats, skipLegacy=True)
    handleBan(db.banactions)
    handleDeletion(db.deleteactions)
