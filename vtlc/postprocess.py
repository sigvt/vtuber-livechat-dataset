import gc
import hashlib
import os
import shutil
from glob import iglob
import argparse
from os.path import basename, join, splitext

import numpy as np
import pandas as pd

from vtlc.constants import RAW_DATA_DIR, VTLC_DIR, VTLC_ELEMENTS_DIR, VTLC_COMPLETE_DIR
from vtlc.util.currency import applyJPY

ANONYMIZATION_SALT = os.environ['ANONYMIZATION_SALT']

# utils


def binMember(x):
    if x == 'unknown':
        return None
    return 0 if x == 'non-member' else 1


def anonymize(s):
    return hashlib.sha1((s + ANONYMIZATION_SALT).encode()).hexdigest()


# func


def load_channels(**kwargs):
    dtype_dict = {
        'channelId': 'category',
        'name': 'category',
        'englishName': 'category',
        'affiliation': 'category',
        'group': 'category',
        'subscriptionCount': 'int32',
        'videoCount': 'int32',
        'photo': 'category'
    }
    channels = pd.read_csv(join(RAW_DATA_DIR, 'channels.csv'),
                           dtype=dtype_dict,
                           **kwargs)
    return channels


def load_moderation_events():
    delet_path = join(RAW_DATA_DIR, 'deletion_events.csv')

    print('>>> Calculating:', delet_path)
    delet = pd.read_csv(join(RAW_DATA_DIR, 'deletion_events.csv'),
                        index_col='timestamp',
                        parse_dates=True)
    delet['period'] = delet.index.strftime('%Y-%m')
    delet = delet.query('retracted == 0')
    delet = delet.groupby(
        ['channelId', 'period'],
        observed=True)['id'].nunique().rename('deletedChats').reset_index()
    # delet.info()

    ban_path = join(RAW_DATA_DIR, 'ban_events.csv')
    print('>>> Calculating:', ban_path)
    ban = pd.read_csv(ban_path, index_col='timestamp', parse_dates=True)
    ban['period'] = ban.index.strftime('%Y-%m')
    ban = ban.groupby([
        'channelId',
        'period',
    ], observed=True).agg({'authorChannelId': ['nunique']})
    ban.columns = ['_'.join(col) for col in ban.columns.values]
    ban.reset_index(inplace=True)
    ban.rename(columns={'authorChannelId_nunique': 'bannedChatters'},
               inplace=True)
    # ban.info()

    return [ban, delet]


# for generate_superchat_stats
def load_superchat(f):
    print('>>> Calculating:', f)
    # dtype_dict = {
    #     'amount': 'float64',
    #     'currency': 'category',
    #     'authorChannelId': 'category',
    #     'channelId': 'category',
    # }
    sc = pd.read_parquet(
        f,
        columns=[
            'amount',
            'currency',
            'authorChannelId',
            'channelId',
            'color',
            'body',
        ],
        #  dtype=dtype_dict
    )

    sc['amountJPY'] = sc.apply(applyJPY, axis=1)
    sc['bodyLength'] = sc['body'].str.len()

    # credit: https://stackoverflow.com/a/23692920/2276646
    mode = lambda x: x.mode()[0] if len(x) > 0 else None

    stat = sc.groupby('channelId', observed=True, sort=False).agg({
        'authorChannelId': [
            'size',
            'nunique',
        ],
        'amountJPY': [
            'sum',
            'mean',
        ],
        'currency':
        mode,
        'color':
        mode,
        'bodyLength': ['sum', 'mean'],
    })
    stat.columns = ['_'.join(col) for col in stat.columns.values]
    stat.reset_index(inplace=True)

    stat = stat.rename(
        columns={
            'authorChannelId_size': 'superChats',
            'authorChannelId_nunique': 'uniqueSuperChatters',
            'amountJPY_sum': 'totalSC',
            'amountJPY_mean': 'averageSC',
            'bodyLength_sum': 'totalMessageLength',
            'bodyLength_mean': 'averageMessageLength',
            'currency_<lambda>': 'mostFrequentCurrency',
            'color_<lambda>': 'mostFrequentColor',
        })

    return stat


# for generate_chat_stats
def load_chat(f):
    print('>>> Calculating:', f)
    # load chats
    # dtype_dict = {
    #     'authorChannelId': 'category',
    #     'channelId': 'category',
    #     'membership': 'category',
    # }
    chat = pd.read_parquet(
        f,
        columns=[
            'authorChannelId',
            'channelId',
            'membership',
        ],
        #    dtype=dtype_dict
    )

    # calculate total, unique
    stat = chat.groupby('channelId', observed=True).agg(
        {'authorChannelId': ['size', 'nunique']})
    stat.columns = ['_'.join(col) for col in stat.columns.values]
    stat.reset_index(inplace=True)
    stat = stat.rename(
        columns={
            'authorChannelId_size': 'chats',
            'authorChannelId_nunique': 'uniqueChatters'
        })

    # calculate for members chats
    mchats = chat[(chat['membership'] != 'non-member')
                  & (chat['membership'] != 'unknown')]
    mstat = mchats.groupby('channelId', observed=True).agg(
        {'authorChannelId': ['size', 'nunique']})
    mstat.columns = ['_'.join(col) for col in mstat.columns.values]
    mstat.reset_index(inplace=True)
    mstat = mstat.rename(
        columns={
            'authorChannelId_size': 'memberChats',
            'authorChannelId_nunique': 'uniqueMembers'
        })
    stat = pd.merge(stat, mstat, on='channelId', how='left')

    return stat


def generate_chat_stats(matcher: str = '*', append_only: bool = False):
    print('[generate_chat_stats]')
    channel_stats = pd.DataFrame()

    for f in sorted(iglob(join(VTLC_COMPLETE_DIR,
                               f'chats_{matcher}.parquet'))):
        period_string = splitext(basename(f))[0].split('_')[1]
        print('>>> Period:', period_string)

        chat_path = join(VTLC_COMPLETE_DIR,
                         'chats_' + period_string + '.parquet')

        # calc chat
        stat = load_chat(chat_path)

        # add period column
        stat['period'] = period_string

        print('>>> Info:', period_string)
        stat.info(memory_usage='deep')

        # merge into result df
        channel_stats = pd.concat([channel_stats, stat])

        gc.collect()

    # merge moderation columns
    [ban, delet] = load_moderation_events()
    channel_stats = pd.merge(left=channel_stats,
                             right=ban,
                             on=['channelId', 'period'],
                             how='left')
    channel_stats = pd.merge(left=channel_stats,
                             right=delet,
                             on=['channelId', 'period'],
                             how='left')

    # fillna
    numeric_columns = channel_stats.select_dtypes(include=['number']).columns
    channel_stats[numeric_columns] = channel_stats[numeric_columns].fillna(
        0).astype('int')

    # re-order columns
    channel_stats = channel_stats.reindex(columns=[
        'channelId',
        'period',
        'chats',
        'memberChats',
        'uniqueChatters',
        'uniqueMembers',
        'bannedChatters',
        'deletedChats',
    ])

    # save df as csv
    print('>>> Writing chat statistics')
    channel_stats.info()
    channel_stats.to_csv(join(RAW_DATA_DIR, 'chat_stats.csv'),
                         index=False,
                         header=not append_only,
                         mode='a' if append_only else 'w')


def generate_superchat_stats(matcher: str = '*', append_only: bool = False):
    print('[generate_superchat_stats]')
    stats = pd.DataFrame()

    for f in sorted(
            iglob(join(VTLC_COMPLETE_DIR, f'superchats_{matcher}.parquet'))):
        period_string = splitext(basename(f))[0].split('_')[1]
        print('>>> Period:', period_string)

        sc_path = join(VTLC_COMPLETE_DIR,
                       'superchats_' + period_string + '.parquet')

        # calc sc
        stat = load_superchat(sc_path)
        stat.info()

        # add period column
        stat['period'] = period_string

        print('>>> Info:', period_string)
        stat.info(memory_usage='deep')

        # merge into result df
        stats = pd.concat([stats, stat])

        gc.collect()

    # fillna
    numeric_columns = stats.select_dtypes(include=['number']).columns
    stats[numeric_columns] = stats[numeric_columns].fillna(0).astype('int')

    # re-order columns
    stats = stats.reindex(columns=[
        'channelId',
        'period',
        'superChats',
        'uniqueSuperChatters',
        'totalSC',
        'averageSC',
        'totalMessageLength',
        'averageMessageLength',
        'mostFrequentCurrency',
        'mostFrequentColor',
    ])

    # save df as csv
    print('>>> Writing super chat statistics')
    stats.info()
    stats.to_csv(join(RAW_DATA_DIR, 'superchat_stats.csv'),
                 index=False,
                 header=not append_only,
                 mode='a' if append_only else 'w')


def compress_chats(matcher: str = '*'):
    print('[compress_chats]')
    for f in sorted(iglob(join(RAW_DATA_DIR, f'chats_{matcher}.csv'))):
        target = join(VTLC_COMPLETE_DIR, splitext(basename(f))[0] + '.parquet')
        print('>>> Loading:', f)

        df = pd.read_csv(
            f,
            na_values='',
            keep_default_na=False,
        )

        print('>>> Normalizing')
        df['isModerator'] = df['isModerator'].astype(bool)
        df['isVerified'] = df['isVerified'].astype(bool)

        print('>>> Saving:', target)
        df.to_parquet(target, index=False)

        del df
        gc.collect()


def compress_superchats(matcher: str = '*'):
    print('[compress_superchats]')
    for f in sorted(iglob(join(RAW_DATA_DIR, f'superchats_{matcher}.csv'))):
        target = join(VTLC_COMPLETE_DIR, splitext(basename(f))[0] + '.parquet')
        print('>>> Loading:', f)

        df = pd.read_csv(
            f,
            na_values='',
            keep_default_na=False,
        )

        print('>>> Saving:', target)
        df.to_parquet(target, index=False)

        del df
        gc.collect()


def compress_ban():
    print('[compress_ban]')
    source = join(RAW_DATA_DIR, 'ban_events.csv')
    target = join(VTLC_COMPLETE_DIR, 'ban_events.parquet')
    print('>>> Loading:', source)
    df = pd.read_csv(source, na_values='', keep_default_na=False)
    print('>>> Saving:', target)
    df.to_parquet(target, index=False)
    del df
    gc.collect()


def compress_deletion():
    print('[compress_deletion]')
    source = join(RAW_DATA_DIR, 'deletion_events.csv')
    target = join(VTLC_COMPLETE_DIR, 'deletion_events.parquet')
    print('>>> Loading:', source)
    df = pd.read_csv(source, na_values='', keep_default_na=False)
    print('>>> Saving:', target)
    df.to_parquet(target, index=False)
    del df
    gc.collect()


def generate_reduced_chats(matcher: str = '*'):
    print('[generate_reduced_chats]')
    for f in sorted(iglob(join(VTLC_COMPLETE_DIR,
                               f'chats_{matcher}.parquet'))):
        target = join(VTLC_DIR, splitext(basename(f))[0] + '.parquet')
        print('>>> Loading:', f)

        df = pd.read_parquet(
            f,
            columns=[
                'timestamp',
                # 'authorName',
                'body',
                'membership',
                #  'isModerator',
                #  'isVerified',
                # 'id',
                'authorChannelId',
                'videoId',
                'channelId',
            ])

        print('>>> Reducing data')

        # anonymize author channel id with grain of salt
        df['authorChannelId'] = df['authorChannelId'].apply(anonymize)

        df['isMember'] = df['membership'].apply(binMember)
        df['bodyLength'] = df['body'].str.len().fillna(0).astype('int32')
        df.drop(columns=['membership', 'body'], inplace=True)

        print('>>> Saving:', target)
        df.to_parquet(target, index=False)

        del df
        gc.collect()


def generate_reduced_superchats(matcher: str = '*'):
    print('[generate_reduced_superchats]')
    for source in sorted(
            iglob(join(VTLC_COMPLETE_DIR, f'superchats_{matcher}.parquet'))):
        target = join(VTLC_DIR, splitext(basename(source))[0] + '.parquet')
        print('>>> Loading:', source)

        df = pd.read_parquet(
            source,
            columns=[
                'timestamp',
                # 'authorName',
                'amount',
                'currency',
                #  'color',
                'significance',
                'body',
                # 'id',
                'authorChannelId',
                'videoId',
                'channelId',
            ])

        print('>>> Reducing data')

        # anonymize author channel id with grain of salt
        df['authorChannelId'] = df['authorChannelId'].apply(anonymize)

        df['bodylength'] = df['body'].str.len().fillna(0).astype('int')
        df.drop(columns=['body'], inplace=True)

        print('>>> Saving:', target)
        df.to_parquet(target, index=False)

        del df
        gc.collect()


def generate_reduced_ban():
    print('[generate_reduced_ban]')

    source = join(VTLC_COMPLETE_DIR, 'ban_events.parquet')
    target = join(VTLC_DIR, 'ban_events.parquet')

    print('>>> Loading:', source)

    df = pd.read_parquet(source,
                         columns=[
                             'timestamp',
                             'authorChannelId',
                             'videoId',
                             'channelId',
                         ])

    print('>>> Reducing data')

    # anonymize author channel id with grain of salt
    df['authorChannelId'] = df['authorChannelId'].apply(anonymize)

    print('>>> Saving:', target)
    # df.to_csv(target, index=False)
    df.to_parquet(target, index=False)

    del df
    gc.collect()


def generate_reduced_deletion():
    print('[generate_reduced_deletion]')

    source = join(VTLC_COMPLETE_DIR, 'deletion_events.parquet')
    target = join(VTLC_DIR, 'deletion_events.parquet')

    print('>>> Loading:', source)

    df = pd.read_parquet(source,
                         columns=[
                             'timestamp',
                             'id',
                             'retracted',
                             'videoId',
                             'channelId',
                         ])

    # print('>>> Reducing data')

    print('>>> Saving:', target)
    df.to_parquet(target, index=False)

    del df
    gc.collect()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='dataset generator')
    parser.add_argument('-m', '--matcher', type=str, default='*')
    parser.add_argument('-a', '--append-only', action='store_true')
    args = parser.parse_args()

    print('raw: ' + RAW_DATA_DIR)
    print('complete: ' + VTLC_COMPLETE_DIR)
    print('standard: ' + VTLC_DIR)
    print('elements: ' + VTLC_ELEMENTS_DIR)
    print('matcher:', args.matcher)
    print('appendOnly:', args.append_only)

    # RAW to COMPLETE
    compress_ban()
    compress_deletion()
    compress_superchats(matcher=args.matcher)
    compress_chats(matcher=args.matcher)

    # COMPLETE to STANDARD
    generate_reduced_ban()
    generate_reduced_deletion()
    generate_reduced_superchats(matcher=args.matcher)
    generate_reduced_chats(matcher=args.matcher)

    # COMPLETE to ELEMENTS
    generate_superchat_stats(matcher=args.matcher,
                             append_only=args.append_only)
    shutil.copy(join(RAW_DATA_DIR, 'superchat_stats.csv'), VTLC_ELEMENTS_DIR)

    generate_chat_stats(matcher=args.matcher, append_only=args.append_only)
    shutil.copy(join(RAW_DATA_DIR, 'chat_stats.csv'), VTLC_ELEMENTS_DIR)
