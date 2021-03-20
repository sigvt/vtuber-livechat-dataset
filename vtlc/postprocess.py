#%%
import pandas as pd
from os.path import join, dirname

DATA_DIR = join(dirname(__file__), '..', 'data')


def create_affiliation_column(df):

    channels = pd.read_csv(join(DATA_DIR, 'channels.csv'))

    df['originAffiliation'] = pd.merge(df,
                                       channels,
                                       left_on='originChannelId',
                                       right_on='channelId')['affiliation']

    df['originChannel'] = pd.merge(df,
                                   channels,
                                   left_on='originChannelId',
                                   right_on='channelId')['name_en']

    df.drop(columns=['originChannelId'], inplace=True)

    return df


if __name__ == '__main__':
    pass
