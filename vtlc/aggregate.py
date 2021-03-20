import csv
import hashlib
import os
from datetime import datetime
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

    channels = pd.read_csv(join(DATA_DIR, 'channels.csv'))

    if skipLegacy:
        pipeline = [{'$skip': 60000000}]
        cursor = col.aggregate(pipeline, allowDiskUse=True)
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
        timestamp = round(int(doc['timestampUsec']) / 1000)

        # handle incorrect superchat amount case before 2021-03-15T23:19:32.123Z
        isIncorrectSuperchat = timestamp < 1615850372123

        if skipLegacy and isMembershipAndSuperchatMissing:
            continue

        # handle missing columns cases before 2021-03-13T21:23:14.000Z
        isMembershipAndSuperchatMissing = timestamp < 1615670594000

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
            originChannel = origin['name_en']
            originAffiliation = origin['affiliation']

            superchatWriter.writerow([
                timestamp,
                amount,
                currency,
                significance,
                bgcolor,
                text,
                originVideoId,
                originChannel,
                originAffiliation,
                id,
                channelId,
            ])

        if isMembershipAndSuperchatMissing:
            isMembership = None
            isSuperchat = 1 if text == '' else None

        if not isMembershipAndSuperchatMissing:
            chatWriter.writerow([
                timestamp,
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
                timestamp,
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
    cursor = col.find({'timestampUsec': {'$exists': True}})
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
        timestamp = round(int(doc['timestampUsec']) /
                          1000) if 'timestampUsec' in doc else None

        if not timestamp:
            continue

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
        timestamp = round(int(doc['timestampUsec']) /
                          1000) if 'timestampUsec' in doc else None

        if not timestamp:
            continue

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

    handleChat(db.chats)
    handleBan(db.banactions)
    handleDeletion(db.deleteactions)
