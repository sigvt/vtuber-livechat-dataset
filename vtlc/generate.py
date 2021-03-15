import pymongo
import os
import csv
import hashlib
from datetime import datetime
from os.path import join, dirname

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


def handleChat(cursor):
    chatFp = open(join(DATA_DIR, 'chat.csv'), 'w', encoding='UTF8')
    chatWriter = csv.writer(chatFp)

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

    for doc in cursor:
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
        timestamp = round(int(doc['timestampUsec']) / 1000)

        # handle cases before 2021-03-14T06:23:14+09:00
        if timestamp < 1615670594000:
            isMembership = None
            isSuperchat = 1 if text == '' else None

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

    chatFp.close()


def handleBan(cursor):
    # chat
    f = open(join(DATA_DIR, 'markedAsBan.csv'), 'w', encoding='UTF8')
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

        writer.writerow([
            timestamp,
            channelId,
            originVideoId,
            originChannelId,
        ])

    f.close()


def handleDeletion(cursor):
    # chat
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
    chats = db.chats
    ban = db.banactions
    deletion = db.deleteactions

    print('# of chats', chats.estimated_document_count())
    print('# of ban', ban.estimated_document_count())
    print('# of deletion', deletion.estimated_document_count())

    chatCursor = chats.find()
    banCursor = ban.find()
    deletionCursor = deletion.find()

    handleChat(chatCursor)
    handleBan(banCursor)
    handleDeletion(deletionCursor)