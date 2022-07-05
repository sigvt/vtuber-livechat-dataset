import argparse
import gc
import itertools
import os
from datetime import datetime, timezone
from os.path import join

import pyarrow as pa
import pyarrow.parquet as pq
import pymongo
from bson.codec_options import CodecOptions
from dateutil.relativedelta import relativedelta
from tqdm import tqdm

from vtlc.constants import RAW_DATA_DIR
from vtlc.util.message import replaceEmojiWithReplacement


# by reclosedev
# https://stackoverflow.com/a/8998040/2276646
def grouper_it(n, iterable):
    it = iter(iterable)
    while True:
        chunk_it = itertools.islice(it, n)
        try:
            first_el = next(chunk_it)
        except StopIteration:
            return
        yield itertools.chain((first_el, ), chunk_it)


MONGODB_URI = os.environ['MONGODB_URI']

CHUNK_SIZE = 1_000

CHAT_SCHEMA = pa.schema([
    pa.field('timestamp', pa.timestamp('ms', tz='UTC')),
    pa.field('id', pa.string()),
    pa.field('authorName', pa.string()),
    pa.field('authorChannelId', pa.string()),
    pa.field('body', pa.string()),
    pa.field('membership', pa.string()),
    pa.field('isModerator', pa.bool_()),
    pa.field('isVerified', pa.bool_()),
    pa.field('isOwner', pa.bool_()),
    pa.field('videoId', pa.string()),
    pa.field('channelId', pa.string()),
])

SC_SCHEMA = pa.schema([
    pa.field('timestamp', pa.timestamp('ms', tz='UTC')),
    pa.field('id', pa.string()),
    pa.field('authorName', pa.string()),
    pa.field('authorChannelId', pa.string()),
    pa.field('body', pa.string()),
    pa.field('amount', pa.float32()),
    pa.field('currency', pa.string()),
    pa.field('color', pa.string()),
    pa.field('significance', pa.int8()),
    pa.field('videoId', pa.string()),
    pa.field('channelId', pa.string()),
])

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
missingMembershipAndSuperchatColumnEnd = datetime.fromtimestamp(
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

    def convert(doc):
        timestamp = doc['timestamp']

        chatId = doc['id']
        authorChannelId = doc['authorChannelId']
        authorName = doc['authorName'] if 'authorName' in doc else None

        try:
            text = replaceEmojiWithReplacement(doc['message'])
        except Exception as e:
            # ignore doc missing a message
            print(doc['_id'], 'lacks message (ignored)')
            return None

        videoId = doc['originVideoId']
        channelId = doc['originChannelId']

        membership = doc['membership'] if 'membership' in doc else 'non-member'

        isMembershipAndSuperchatInfoMissing = (
            timestamp < missingMembershipAndSuperchatColumnEnd) or (
                (timestamp >= missingMembershipColumn2022Start) and
                (timestamp < missingMembershipColumn2022End))
        if isMembershipAndSuperchatInfoMissing:
            membership = 'unknown'

        isModerator = doc['isModerator']
        isVerified = doc['isVerified']
        isOwner = doc['isOwner']

        return {
            'timestamp': timestamp,
            'id': chatId,
            'authorName': authorName,
            'authorChannelId': authorChannelId,
            'body': text,
            'membership': membership,
            'isModerator': isModerator,
            'isVerified': isVerified,
            'isOwner': isOwner,
            'videoId': videoId,
            'channelId': channelId,
        }

    def to_file(cursor, total, filename):
        outpath = join(RAW_DATA_DIR, filename)

        pq_writer = pq.ParquetWriter(outpath, CHAT_SCHEMA)
        tp = tqdm(total=total, mininterval=1, desc=filename)

        for docs in grouper_it(CHUNK_SIZE, cursor):
            tp.update(CHUNK_SIZE)
            table = pa.Table.from_pylist(list(filter(None, map(convert,
                                                               docs))),
                                         schema=CHAT_SCHEMA)
            pq_writer.write_table(table)

        pq_writer.close()
        tp.close()

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
        filename = f'chats_{cm.strftime("%Y-%m")}.parquet'
        print('data range:', cm, '<= X <', nm)
        print('target:', filename)

        query = {'timestamp': {'$gte': cm, '$lt': nm}}
        cursor = collection.find(query)
        cursorTotal = collection.count_documents(query)
        to_file(cursor, cursorTotal, filename)

        gc.collect()

        # update start epoch
        cm = nm


def accumulateSuperChat(collection, recent=-1, ignoreHalfway=False):
    print('# of superchats', collection.estimated_document_count())

    if recent >= 0:
        print(f'Processing chats past {recent} month(s)')
    if ignoreHalfway:
        print('While ignoring this month')

    def convert(doc):
        timestamp = doc['timestamp']

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

        return {
            'timestamp': timestamp,
            'id': chatId,
            'authorName': authorName,
            'authorChannelId': authorChannelId,
            'body': text,
            'amount': amount,
            'currency': currency,
            'color': color,
            'significance': significance,
            'videoId': videoId,
            'channelId': channelId,
        }

    def to_file(cursor, total, filename):
        outpath = join(RAW_DATA_DIR, filename)

        pq_writer = pq.ParquetWriter(outpath, SC_SCHEMA)
        tp = tqdm(total=total, mininterval=1, desc=filename)

        for docs in grouper_it(CHUNK_SIZE, cursor):
            tp.update(CHUNK_SIZE)
            table = pa.Table.from_pylist(list(map(convert, docs)),
                                         schema=SC_SCHEMA)
            pq_writer.write_table(table)

        pq_writer.close()
        tp.close()

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
        filename = f'superchats_{cm.strftime("%Y-%m")}.parquet'
        print('data range:', cm, '<= X <', nm)
        print('target:', join(RAW_DATA_DIR, filename))

        query = {'timestamp': {'$gte': cm, '$lt': nm}}
        cursor = collection.find(query)
        cursorTotal = collection.count_documents(query)
        to_file(cursor, cursorTotal, filename)

        # update start epoch
        cm = nm


def accumulateBan(col):
    print('# of ban', col.estimated_document_count())
    cursor = col.find()

    def convert(doc):
        authorChannelId = doc['channelId']
        videoId = doc['originVideoId']
        channelId = doc['originChannelId']
        timestamp = doc['timestamp'] if 'timestamp' in doc else None

        return {
            'timestamp': timestamp,
            'authorChannelId': authorChannelId,
            'videoId': videoId,
            'channelId': channelId,
        }

    records = list(map(convert, cursor))
    table = pa.Table.from_pylist(records)
    pq.write_table(table, join(RAW_DATA_DIR, 'ban_events.parquet'))


def accumulateDeletion(col):
    print('# of deletion', col.estimated_document_count())
    cursor = col.find()

    def convert(doc):
        chatId = doc['targetId']
        videoId = doc['originVideoId']
        channelId = doc['originChannelId']
        retracted = doc['retracted']
        timestamp = doc['timestamp'] if 'timestamp' in doc else None

        return {
            'timestamp': timestamp,
            'id': chatId,
            'retracted': retracted,
            'videoId': videoId,
            'channelId': channelId,
        }

    records = list(map(convert, cursor))
    table = pa.Table.from_pylist(records)
    pq.write_table(table, join(RAW_DATA_DIR, 'deletion_events.parquet'))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='dataset generator')
    parser.add_argument('-R', '--recent', type=int, default=0)
    parser.add_argument('-I', '--ignore-halfway', action='store_true')
    args = parser.parse_args()

    print('dataset: ' + RAW_DATA_DIR)

    client = pymongo.MongoClient(MONGODB_URI)
    db = client.vespa

    options = CodecOptions(tz_aware=True)

    chats = db.get_collection('chats', codec_options=options)
    sc = db.get_collection('superchats', codec_options=options)
    delete_actions = db.get_collection('deleteactions', codec_options=options)
    ban_actions = db.get_collection('banactions', codec_options=options)

    accumulateChat(chats,
                   recent=args.recent,
                   ignoreHalfway=args.ignore_halfway)
    accumulateSuperChat(sc,
                        recent=args.recent,
                        ignoreHalfway=args.ignore_halfway)
    accumulateDeletion(delete_actions)
    accumulateBan(ban_actions)
