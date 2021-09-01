import gc
import shutil
from glob import iglob
import argparse
from os.path import basename, join, splitext

import numpy as np
import pandas as pd

from vtlc.constants import DATASET_DIR, DATASET_DIR_FULL
from vtlc.util.currency import applyJPY


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
    channels = pd.read_csv(join(DATASET_DIR_FULL, 'channels.csv'),
                           dtype=dtype_dict,
                           **kwargs)
    return channels


def load_moderation_events():
    delet_path = join(DATASET_DIR_FULL, 'deletion_events.csv')

    print('>>> Calculating:', delet_path)
    delet = pd.read_csv(join(DATASET_DIR_FULL, 'deletion_events.csv'),
                        index_col='timestamp',
                        parse_dates=True)
    delet['period'] = delet.index.strftime('%Y-%m')
    delet = delet.query('retracted == 0')
    delet = delet.groupby(
        ['channelId', 'period'],
        observed=True)['id'].nunique().rename('deletedChats').reset_index()
    # delet.info()

    ban_path = join(DATASET_DIR_FULL, 'ban_events.csv')
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


def load_superchat(f):
    print('>>> Calculating:', f)
    dtype_dict = {
        'amount': 'float64',
        'currency': 'category',
        'authorChannelId': 'category',
        'channelId': 'category',
    }
    try:
        sc = pd.read_csv(f,
                         usecols=[
                             'amount',
                             'currency',
                             'authorChannelId',
                             'channelId',
                             'color',
                             'body',
                         ],
                         dtype=dtype_dict)
    except:
        return None

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
        'currency': mode,
        'color': mode,
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


def load_chat(f):
    print('>>> Calculating:', f)
    # load chats
    dtype_dict = {
        'authorChannelId': 'category',
        'channelId': 'category',
        'membership': 'category',
    }
    chat = pd.read_csv(f,
                       usecols=[
                           'authorChannelId',
                           'channelId',
                           'membership',
                       ],
                       dtype=dtype_dict)

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
    mchats = chat[chat['membership'] != 'non-member']
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


def generate_chat_stats():
    print('[generate_chat_stats]')
    channel_stats = pd.DataFrame()

    for f in sorted(iglob(join(DATASET_DIR_FULL, 'chats_*.csv'))):
        period_string = splitext(basename(f))[0].split('_')[1]
        print('>>> Period:', period_string)

        chat_path = join(DATASET_DIR_FULL, 'chats_' + period_string + '.csv')

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
    print('>>> Chat Statistics')
    channel_stats.info()
    channel_stats.to_csv(join(DATASET_DIR_FULL, 'chat_stats.csv'), index=False)


def generate_superchat_stats():
    print('[generate_superchat_stats]')
    stats = pd.DataFrame()

    for f in sorted(iglob(join(DATASET_DIR_FULL, 'superchats_*.csv'))):
        period_string = splitext(basename(f))[0].split('_')[1]
        print('>>> Period:', period_string)

        sc_path = join(DATASET_DIR_FULL, 'superchats_' + period_string + '.csv')

        # calc sc
        stat = load_superchat(sc_path)

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
    print('>>> Super Chat Statistics')
    stats.info()
    stats.to_csv(join(DATASET_DIR_FULL, 'superchat_stats.csv'), index=False)


def generate_reduced_chats(matcher):
    print('[generate_reduced_chats]')
    for f in sorted(iglob(join(DATASET_DIR_FULL, f'chats_{matcher}.csv'))):
        target = join(DATASET_DIR, basename(f))
        print('>>> Loading:', f)

        df = pd.read_csv(
            f,
            na_values='',
            keep_default_na=False,
            parse_dates=['timestamp'],
            usecols=[
                'timestamp',
                # 'body',
                'membership',
                #  'isModerator',
                #  'isVerified',
                # 'id',
                'authorChannelId',
                'videoId',
                'channelId',
            ])

        print('>>> Reducing data')

        def binMember(x):
            if x == 'unknown':
                return None
            return 0 if x == 'non-member' else 1

        df['isMember'] = df['membership'].apply(binMember)
        df.drop(columns=['membership'], inplace=True)

        print('>>> Saving:', target)
        df.to_csv(target, index=False, date_format='%Y%m%dT%H%MZ')

        del df
        gc.collect()


def generate_reduced_superchats(matcher):
    print('[generate_reduced_superchats]')
    for f in sorted(iglob(join(DATASET_DIR_FULL, f'superchats_{matcher}.csv'))):
        target = join(DATASET_DIR, basename(f))
        print('>>> Loading:', f)

        df = pd.read_csv(
            f,
            na_values='',
            keep_default_na=False,
            parse_dates=['timestamp'],
            usecols=[
                'timestamp',
                'amount',
                'currency',
                #  'color',
                'significance',
                # 'body',
                # 'id',
                'authorChannelId',
                # 'videoId',
                'channelId',
            ])

        print('>>> Reducing data')
        # df.drop(columns=['body', 'id', 'videoId'], inplace=True)

        print('>>> Saving:', target)
        df.to_csv(target, index=False, date_format='%Y%m%dT%H%MZ')

        del df
        gc.collect()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='dataset generator')
    parser.add_argument('-m', '--matcher', type=str, default='*')
    args = parser.parse_args()

    print('source: ' + DATASET_DIR_FULL)
    print('target: ' + DATASET_DIR)

    # copy moderation events
    # TODO: remove this after everything
    shutil.copy(join(DATASET_DIR_FULL, 'deletion_events.csv'), DATASET_DIR)
    shutil.copy(join(DATASET_DIR_FULL, 'ban_events.csv'), DATASET_DIR)

    generate_reduced_chats(matcher=args.matcher)
    # generate_reduced_superchats(matcher=args.matcher)

    # generate_chat_stats()
    # shutil.copy(join(DATASET_DIR_FULL, 'chat_stats.csv'), DATASET_DIR)

    # generate_superchat_stats()
    # shutil.copy(join(DATASET_DIR_FULL, 'superchat_stats.csv'), DATASET_DIR)