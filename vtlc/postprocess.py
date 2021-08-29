import gc
import shutil
from glob import iglob
import argparse
from os.path import basename, join, splitext

import pandas as pd

from vtlc.constants import DATASET_DIR, DATASET_DIR_FULL
from vtlc.util.currency import applyJPY

# chats total,nunique,mean/u
# memberchats total,nunique,mean/u
# superchats total,nunique,mean/u
# ban total,nunique
# deletion total,nunique


def load_channels(**kwargs):
    dtype_dict = {
        'channelId': 'category',
        'name': 'category',
        'name.en': 'category',
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
    ], observed=True).agg({'channelId': ['nunique',]})
    ban.columns = ['_'.join(col) for col in ban.columns.values]
    ban.reset_index(inplace=True)
    ban.rename(columns={'channelId_nunique': 'bannedChatters'}, inplace=True)
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
                         ],
                         dtype=dtype_dict)
    except:
        return None

    sc['amountJPY'] = sc.apply(applyJPY, axis=1)

    stat = sc.groupby('channelId', observed=True, sort=False).agg({
        'authorChannelId': [
            'size',
            'nunique',
        ],
        'amountJPY': [
            'sum',
            'mean',
        ]
    })
    stat.columns = ['_'.join(col) for col in stat.columns.values]
    stat.reset_index(inplace=True)

    stat = stat.rename(
        columns={
            'authorChannelId_size': 'superChats',
            'authorChannelId_nunique': 'uniqueSuperChatters',
            'amountJPY_sum': 'totalSC',
            'amountJPY_mean': 'averageSC'
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


def generate_channel_stats():
    print('[generate_channel_stats]')
    channel_stats = pd.DataFrame()

    for f in sorted(iglob(join(DATASET_DIR_FULL, 'chats_*.csv'))):
        period_string = splitext(basename(f))[0].split('_')[1]
        print('>>> Period:', period_string)

        chat_path = join(DATASET_DIR_FULL, 'chats_' + period_string + '.csv')
        sc_path = join(DATASET_DIR_FULL, 'superchats_' + period_string + '.csv')

        # calc chat
        stat = load_chat(chat_path)

        # calc sc
        sc_stat = load_superchat(sc_path)
        if sc_stat is not None:
            stat = pd.merge(stat, sc_stat, on='channelId', how='left')

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

    # channel_stats['superChats'] = channel_stats['superChats'].astype('int')
    # channel_stats['uniqueSuperChatters'] = channel_stats[
    #     'uniqueSuperChatters'].astype('int')
    # channel_stats['totalSC'] = channel_stats['totalSC'].astype('int')
    # channel_stats['bannedChatters'] = channel_stats['bannedChatters'].astype(
    #     'int')
    # channel_stats['deletedChats'] = channel_stats['deletedChats'].astype('int')

    # re-order columns
    channel_stats = channel_stats.reindex(columns=[
        'channelId',
        'period',
        'chats',
        'memberChats',
        'superChats',
        'uniqueChatters',
        'uniqueMembers',
        'uniqueSuperChatters',
        'totalSC',
        'averageSC',
        'bannedChatters',
        'deletedChats',
    ])

    # save df as csv
    print('>>> Channel Stats')
    channel_stats.info()
    channel_stats.to_csv(join(DATASET_DIR_FULL, 'channel_stats.csv'),
                         index=False)


def generate_chat_dataset(matcher):
    print('[generate_chat_dataset]')

    delet_path = join(DATASET_DIR_FULL, 'deletion_events.csv')
    del_events = pd.read_csv(delet_path, usecols=['id', 'retracted'])
    del_events = del_events.query('retracted == 0').copy()
    del_events.drop(columns=['retracted'], inplace=True)
    del_events['deleted'] = True

    ban_path = join(DATASET_DIR_FULL, 'ban_events.csv')
    ban_events = pd.read_csv(ban_path, usecols=['authorChannelId', 'videoId'])
    ban_events['banned'] = True

    for f in sorted(iglob(join(DATASET_DIR_FULL, matcher))):
        period_string = splitext(basename(f))[0].split('_')[1]
        print('>>> Period:', period_string)

        # load chat
        print('>>> Loading chats')
        chat_path = join(DATASET_DIR_FULL, 'chats_' + period_string + '.csv')
        chat_dtype = {'authorChannelId': 'category'}
        chats = pd.read_csv(chat_path,
                            dtype=chat_dtype,
                            usecols=[
                                'id', 'authorChannelId', 'body', 'membership',
                                'videoId', 'channelId'
                            ])

        # apply mods
        print('>>> Merging deletion')
        chats = pd.merge(chats, del_events, on=['id'], how='left')
        chats['deleted'].fillna(False, inplace=True)

        # apply mods
        print('>>> Merging bans')
        chats = pd.merge(chats,
                         ban_events,
                         on=['authorChannelId', 'videoId'],
                         how='left')
        chats['banned'].fillna(False, inplace=True)

        flagged = chats[(chats['deleted'] | chats['banned'])].copy()

        # to make balanced dataset
        nbFlagged = flagged.shape[0]
        print('nbFlagged', nbFlagged)
        if nbFlagged == 0:
            continue

        nonflag = chats[~(chats['deleted'] | chats['banned'])].sample(nbFlagged)

        print('>>> Writing dataset')

        columns_to_delete = ['deleted', 'banned', 'id', 'videoId']

        flagged.drop(columns=columns_to_delete, inplace=True)
        flagged.to_csv(join(DATASET_DIR, f'chats_flagged_{period_string}.csv'),
                       index=False)
        nonflag.drop(columns=columns_to_delete, inplace=True)
        nonflag.to_csv(join(DATASET_DIR, f'chats_nonflag_{period_string}.csv'),
                       index=False)

        # free up memory
        del nonflag
        del flagged
        del chats
        gc.collect()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='dataset generator')
    parser.add_argument('-m', '--matcher', type=str, default='chats_*.csv')
    parser.add_argument('-s', '--stats', nargs='?', const=True, default=False)
    parser.add_argument('-d', '--dataset', nargs='?', const=True, default=False)
    args = parser.parse_args()

    print('target: ' + DATASET_DIR)
    print('source: ' + DATASET_DIR_FULL)

    if args.stats:
        generate_channel_stats()
        shutil.copy(join(DATASET_DIR_FULL, 'channel_stats.csv'), DATASET_DIR)

    if args.dataset:
        generate_chat_dataset(matcher=args.matcher)

    print('>>> Copying superchats')
    for f in iglob(join(DATASET_DIR_FULL, 'superchats_*.csv')):
        shutil.copy(f, DATASET_DIR)
