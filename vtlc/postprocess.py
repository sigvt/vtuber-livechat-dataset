import pandas as pd
from os.path import join, dirname, basename, splitext
from glob import iglob

DATA_DIR = join(dirname(__file__), '..', 'datasets', 'vtuber-livechat')

delet = pd.read_csv(join(DATA_DIR, 'deletion_events.csv'),
                    index_col='timestamp',
                    parse_dates=True)
delet = delet.query('retracted == 0')
delet['period'] = delet.index.to_period('M')
delet = delet.groupby(['originChannelId', 'period'
                      ])['id'].nunique().rename('deletionCount').reset_index()
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

symMap = {
    '$': 'USD',
    '£': 'GBP',
    '¥': 'JPY',
    '₩': 'KRW',
    '₪': 'ILS',
    '€': 'USD',
    '₱': 'PHP',
    '₹': 'INR',
    'A$': 'AUD',
    'AED': 'AED',
    'ARS': 'ARS',
    'BAM': 'BAM',
    'BGN': 'BGN',
    'BOB': 'BOB',
    'BYN': 'BYN',
    'CA$': 'CAD',
    'CHF': 'CHF',
    'CLP': 'CLP',
    'COP': 'COP',
    'CRC': 'CRC',
    'CZK': 'CZK',
    'DKK': 'DKK',
    'DOP': 'DOP',
    'GTQ': 'GTQ',
    'HK$': 'HKD',
    'HNL': 'HNL',
    'HRK': 'HRK',
    'HUF': 'HUF',
    'INR': 'INR',
    'ISK': 'ISK',
    'MAD': 'MAD',
    'MKD': 'MKD',
    'MX$': 'MXN',
    'MYR': 'MYR',
    'NIO': 'NIO',
    'NOK': 'NOK',
    'NT$': 'TWD',
    'NZ$': 'NZD',
    'PEN': 'USD',
    'PHP': 'PHP',
    'PLN': 'PLN',
    'PYG': 'PYG',
    'R$': 'BRL',
    'RON': 'RON',
    'RSD': 'RSD',
    'RUB': 'RUB',
    'SAR': "SAR",
    'SEK': 'SEK',
    'SGD': 'SGD',
    'TRY': 'TRY',
    'UYU': 'UYU',
    'ZAR': 'ZAR',
}

approxRates = {
    'AED': 0.03,
    'ARS': 1.26136,
    'AUD': 0.0127098151,
    'BAM': 0.01,
    'BGN': 0.01,
    'BOB': 0.06,
    'BRL': 0.0501367157,
    'BYN': 236.83,
    'CAD': 0.0123889679,
    'CHF': 0.009,
    'CLP': 6.61,
    'COP': 33.63,
    'CRC': 5.72,
    'CZK': 0.208,
    'DKK': 0.06,
    'DOP': 0.53,
    'GBP': 0.0071446183,
    'GTQ': 0.07,
    'HKD': 0.0748624941,
    'HNL': 0.22,
    'HRK': 0.06,
    'HUF': 2.872293346,
    'ILS': 0.03,
    'INR': 0.69,
    'INY': 0.703,
    'ISK': 1.16,
    'JPY': 1,
    'KRW': 10.5964122017,
    'MAD': 0.08,
    'MKD': 0.47,
    'MXN': 0.1921416153,
    'MYR': 0.04,
    'NIO': 0.32,
    'NOK': 0.0835411728,
    'NZD': 0.03559,
    'PHP': 0.44,
    'PLN': 0.03559,
    'PYG': 60.2,
    'RON': 0.04,
    'RSD': 0.91,
    'RUB': 0.706,
    'SAR': 0.03,
    'SEK': 0.08,
    'SGD': 0.0128315157,
    'TRY': 0.08,
    'TWD': 3.68028,
    'USD': 0.0093,
    'UYU': 0.41,
    'ZAR': 0.13,
}


def handleChats():

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

        sc['amountJPY'] = sc.apply(
            lambda x: x['amount'] / approxRates[symMap[x['currency']]], axis=1)

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
