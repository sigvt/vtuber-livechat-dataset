import os
import sys
from glob import iglob
from os.path import join

import altair as alt
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
from altair import Axis, Chart, Text, TitleParams, X, Y, datum

from vtlc.constants import VTLC_COMPLETE_DIR, VTLC_DIR, VTLC_ELEMENTS_DIR

# Plotly

pio.templates["holodata"] = go.layout.Template()
pio.templates["holodata"].layout.paper_bgcolor = '#1E1D1F'
pio.templates["holodata"].layout.plot_bgcolor = '#1E1D1F'

pio.templates.default = "plotly_dark+holodata"


def plotly_add_footer(fig):
    fig.layout.annotations = [
        dict(
            name="watermark",
            text="holodata.org",
            opacity=1,
            font=dict(color="white", size=20),
            xref="paper",
            yref="paper",
            x=0,
            y=0,
            showarrow=False,
        ),
        dict(
            name="info",
            text="Data Source: VTuber 1B (holodata.org/vtuber-1b)",
            opacity=1,
            font=dict(color="white", size=15),
            xref="paper",
            yref="paper",
            xanchor='right',
            x=1,
            y=0,
            showarrow=False,
        )
    ]

    return fig


# Altair


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


def vtlc_path(name: str):
    return os.path.join(VTLC_DIR, name)


def vtlc_elements_path(name: str):
    return os.path.join(VTLC_ELEMENTS_DIR, name)


def vtlc_complete_path(name: str):
    return os.path.join(VTLC_COMPLETE_DIR, name)


def load_channels(**kwargs):
    return pd.read_csv(vtlc_elements_path('channels.csv'), **kwargs)


def load_complete_chat(month, **kwargs):
    return pd.read_parquet(vtlc_complete_path(f'chats_{month}.parquet'),
                           **kwargs)


def load_complete_sc(glob_pattern='superchats_*.parquet'):
    df = pd.concat(
        [pd.read_parquet(f) for f in iglob(vtlc_complete_path(glob_pattern))],
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


def load_hololive():
    stats = pd.read_csv(vtlc_elements_path('chat_stats.csv'))
    sc_stats = pd.read_csv(vtlc_elements_path('superchat_stats.csv'))
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
