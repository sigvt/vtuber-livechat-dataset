import os
from os.path import join
from glob import iglob
import numpy as np
import pandas as pd
import altair as alt
from altair import Chart, X, Y, Text, Axis, TitleParams, datum
import sys

sys.path.append('..')
from vtlc.constants import VTLC_COMPLETE_DIR, VTLC_ELEMENTS_DIR


def holodata_theme():
    bgColor = '#1E1D1F'
    fgColor = '#ffffff'
    mdColor = '#888888'
    gridColor = '#2F2D32'

    return {
        'config': {
            'padding': 20,
            'background': bgColor,
            'view': {
                'stroke': gridColor,
            },
            'title': {
                'color': fgColor,
                'subtitleColor': mdColor,
            },
            'style': {
                'guide-label': {
                    'fill': mdColor,
                },
                'guide-title': {
                    'fill': fgColor,
                    'fontSize': 14
                },
            },
            'axis': {
                'domain': False,
                'grid': True,
                'labels': True,
                'ticks': False,
                'labelPadding': 4,
                'gridColor': gridColor,
                'tickColor': mdColor,
                'titlePadding': 10,
            },
            'text': {
                'color': fgColor
            }
        }
    }


alt.themes.register('holodata', holodata_theme)
alt.themes.enable('holodata')


def load_chat(month, **kwargs):
    # https://towardsdatascience.com/optimize-pandas-memory-usage-while-reading-large-datasets-1b047c762c9b
    # groupby(sort=False, observed=True)
    # dtype_dict = {
    #     'isModerator': bool,
    #     'isVerified': bool,
    #     'membership': 'category',
    #     'channelId': 'category',
    #     'originChannelId': 'category',
    #     'originVideoId': 'category'
    # }
    df = pd.read_parquet(
        join(VTLC_COMPLETE_DIR, f'chats_{month}.parquet'),
        #  dtype=dtype_dict,
        **kwargs)

    return df


def load_sc():
    df = pd.concat([
        pd.read_parquet(f)
        for f in iglob(join(VTLC_COMPLETE_DIR, 'superchats_*.parquet'))
    ],
                   ignore_index=True)

    # body length
    df['bodylength'] = df['body'].str.len().fillna(0).astype('int16')

    df['impact'] = df['significance'].map({
        1: 1,
        2: 2,
        3: 5,
        4: 10,
        5: 20,
        6: 50,
        7: 100
    }).astype('int8')

    return df


def load_channels(**kwargs):
    dtype_dict = {
        'channelId': 'category',
        'name': 'category',
        'englishName': 'category',
        'affiliation': 'category',
        'subscriptionCount': 'int32',
        'videoCount': 'int16',
        'photo': 'category'
    }
    channels = pd.read_csv(join(VTLC_ELEMENTS_DIR, 'channels.csv'),
                           dtype=dtype_dict,
                           **kwargs)
    return channels


def load_hololive():
    stats = pd.read_csv(join(VTLC_ELEMENTS_DIR, 'chat_stats.csv'))
    sc_stats = pd.read_csv(join(VTLC_ELEMENTS_DIR, 'superchat_stats.csv'))
    stats = pd.merge(stats, sc_stats, on=['period', 'channelId'], how='left')

    channels = load_channels()

    channels = channels[(channels['affiliation'] == 'Hololive')
                        & (channels['group'] != 'INACTIVE')]
    channels['group'].fillna('No Group', inplace=True)

    # exclude official/secondary/graduated channels
    officialChannels = [
        'UCJFZiqLMntJufDCHc6bQixg',
        'UCfrWoRGlawPQDQxxeIDRP0Q',
        'UCotXwY6s8pWmuWd_snKYjhg',
        'UCWsfcksUUpoEvhia0_ut0bA',
    ]
    subChannels = [
        'UCHj_mh57PVMXhAUDphUQDFA',
        'UCLbtM3JZfRTg8v2KGag-RMw',
        'UCp3tgHXw_HI0QMk1K8qh3gQ',
    ]
    graduated = ['UCS9uQI-jC3DE0L4IpXyvr6w']
    channels = channels[~channels['channelId'].isin(officialChannels +
                                                    subChannels + graduated)]

    # merge stats columns
    numeric_columns = stats.select_dtypes(include=['number']).columns
    stats[numeric_columns] = stats[numeric_columns].fillna(0).astype('int')
    channels = pd.merge(channels, stats, on=['channelId'], how='left')

    # sex
    channels['sex'] = channels['group'].apply(
        lambda g: 'Male' if g.startswith('Holostars') else 'Female')

    # language
    def langmatch(channel):
        if channel['group'].startswith(
                'English') or channel['englishName'] == 'IRyS':
            return 'English'
        elif channel['group'].startswith('Indonesia'):
            return 'Indonesian'
        return 'Japanese'

    channels['language'] = channels.apply(langmatch, axis=1)

    # aggregate data
    overall = channels.groupby('englishName').agg({
        'subscriptionCount': 'first',
        'videoCount': 'first',
        'chats': 'sum',
        'uniqueChatters': 'mean',
        'bannedChatters': 'mean',
        'deletedChats': 'sum',
        'superChats': 'sum',
        'uniqueSuperChatters': 'mean',
        'totalSC': 'sum',
        'averageSC': 'last',
        'affiliation': 'first',
        'group': 'first',
        'name': 'first',
        'sex': 'first',
        'language': 'first',
        'photo': 'first'
    }).reset_index()

    overall['chatCountPerUser'] = overall['chats'] / overall['uniqueChatters']

    return (channels, overall)
