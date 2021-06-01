from glob import iglob
from os.path import basename, dirname, join, splitext

import pandas as pd

from vtlc.util.currency import applyJPY

DATA_DIR = join(dirname(__file__), '..', 'datasets', 'vtuber-livechat')


def load_moderations():
    delet = pd.read_csv(join(DATA_DIR, 'deletion_events.csv'),
                        index_col='timestamp',
                        parse_dates=True)
    delet = delet.query('retracted == 0')
    delet['period'] = delet.index.to_period('M')
    delet = delet.groupby(
        ['originChannelId',
         'period'])['id'].nunique().rename('deletionCount').reset_index()
    delet.rename(columns={'originChannelId': 'channelId'}, inplace=True)
    delet.info()

    ban = pd.read_csv(join(DATA_DIR, 'ban_events.csv'),
                      index_col='timestamp',
                      parse_dates=True)
    ban['period'] = ban.index.to_period('M')
    ban = ban.groupby(['originChannelId',
                       'period']).agg({'channelId': ['size', 'nunique']})
    ban.columns = ['_'.join(col) for col in ban.columns.values]
    ban.reset_index(inplace=True)
    ban.rename(columns={
        'channelId_size': 'banCount',
        'channelId_nunique': 'banNunique',
        'originChannelId': 'channelId'
    },
               inplace=True)
    ban.info()
    return [ban, delet]


def handleChats():
    [ban, delet] = load_moderations()

    stat_all = pd.DataFrame()

    for f in sorted(iglob(join(DATA_DIR, 'chats_*.csv'))):
        print('Handling', splitext(basename(f))[0])
        chat = pd.read_csv(
            f, usecols=['timestamp', 'originChannelId', 'channelId'])

        stat = chat.groupby('originChannelId').agg(
            {'channelId': ['size', 'nunique']})
        stat.columns = ['_'.join(col) for col in stat.columns.values]
        stat.reset_index(inplace=True)
        stat = stat.rename(
            columns={
                'channelId_size': 'chatCount',
                'channelId_nunique': 'chatNunique',
                'originChannelId': 'channelId'
            })

        ts = pd.to_datetime(chat.iloc[0].timestamp)
        stat['period'] = ts.to_period('M')

        stat.info()

        stat_all = pd.concat([stat_all, stat])

    stat_all = pd.merge(left=stat_all,
                        right=ban,
                        on=['channelId', 'period'],
                        how='left')
    stat_all = pd.merge(left=stat_all,
                        right=delet,
                        on=['channelId', 'period'],
                        how='left')
    stat_all = stat_all.reindex(columns=[
        'channelId',
        'period',
        'chatCount',
        'chatNunique',
        'banCount',
        'banNunique',
        'deletionCount',
    ])
    numeric_columns = stat_all.select_dtypes(include=['number']).columns
    stat_all[numeric_columns] = stat_all[numeric_columns].fillna(0).astype(
        'int')

    stat_all.info()

    stat_all.to_csv(join(DATA_DIR, 'chat_stats.csv'), index=False)


def handleSuperChats():

    stat_all = pd.DataFrame()

    for f in sorted(iglob(join(DATA_DIR, 'superchats_*.csv'))):
        print('Handling', splitext(basename(f))[0])
        sc = pd.read_csv(f,
                         usecols=[
                             'timestamp', 'originChannelId', 'channelId',
                             'amount', 'currency'
                         ])

        sc['amountJPY'] = sc.apply(applyJPY, axis=1)

        stat = sc.groupby('originChannelId').agg({
            'channelId': ['size', 'nunique'],
            'amountJPY': ['sum', 'mean']
        })
        stat.columns = ['_'.join(col) for col in stat.columns.values]
        stat.reset_index(inplace=True)
        stat = stat.rename(
            columns={
                'channelId_size': 'scCount',
                'channelId_nunique': 'scNunique',
                'amountJPY_sum': 'scTotalJPY',
                'amountJPY_mean': 'scMeanJPY',
                'originChannelId': 'channelId'
            })

        ts = pd.to_datetime(sc.iloc[0].timestamp)
        stat['period'] = ts.to_period('M')

        stat_all = stat_all.reindex(columns=[
            'channelId',
            'period',
            'scCount',
            'scNunique',
            'scTotalJPY',
            'scMeanJPY',
        ])

        stat.info()

        stat_all = pd.concat([stat_all, stat])

    numeric_columns = stat_all.select_dtypes(include=['number']).columns
    stat_all[numeric_columns] = stat_all[numeric_columns].fillna(0).astype(
        'int')

    stat_all.info()

    stat_all.to_csv(join(DATA_DIR, 'superchat_stats.csv'), index=False)


if __name__ == '__main__':
    handleSuperChats()
    handleChats()
