![Header](https://github.com/holodata/vtuber-livechat-dataset/blob/master/.github/kaggle-dataset-header.png?raw=true)

# VTuber 400M: Live Chat and Moderation Events

VTuber 400M is a huge collection of hundreds of millions of live chat, super chat, and moderation events (ban and deletion) all across Virtual YouTubers' live streams, ready for academic research and any kinds of NLP projects.

Download the dataset from [Kaggle Datasets](https://www.kaggle.com/uetchy/vtuber-livechat) and join `#livechat-dataset` channel on [holodata Discord](https://holodata.org/discord) for discussions.

## Provenance

- **Source:** YouTube Live Chat events (all streams covered by [Holodex](https://holodex.net), including Hololive, Nijisanji, 774inc, etc)
- **Temporal Coverage:**
  - Chats: from 2021-01-15T05:15:33Z
  - Superchats: from 2021-03-16T08:19:38Z
- **Update Frequency:**
  - At least once per month
- **Tool:** [Honeybee](https://github.com/holodata/honeybee)

## Research Ideas

- Toxic Chat Classification
- Spam Detection
- Demographic Visualization
- Superchat Analysis
- Sentence Transformer for Live Chats

See [public notebooks](https://www.kaggle.com/uetchy/vtuber-livechat/code?datasetId=1209921) for ideas.

We employed [Honeybee](https://github.com/holodata/honeybee) cluster to collect real-time live chat events across major Vtubers' live streams. All sensitive data such as author name or author profile image are omitted from the dataset, and author channel id is anonymized by SHA-1 hashing algorithm with a grain of salt.

## Editions

### Standard version

Standard version is available at [Kaggle Datasets](https://www.kaggle.com/uetchy/vtuber-livechat).

| filename                  | summary                                                        | size     |
| ------------------------- | -------------------------------------------------------------- | -------- |
| `channels.csv`            | Channel index                                                  | < 1 MB   |
| `channel_stats.csv`       | Channel statistics                                             | < 1 MB   |
| `chats_flagged_%Y-%m.csv` | Chats flagged as either deleted or banned by mods (3,000,000+) | ~ 500 MB |
| `chats_nonflag_%Y-%m.csv` | Non-flagged chats (3,000,000+)                                 | ~ 500 MB |
| `superchats_%Y-%m.csv`    | Super chat messages (1,400,000+)                               | ~ 400 MB |

To make it a balanced dataset, the number of `chats_nonflags` is adjusted (randomly sampled) to be the same as `chats_flagged`.

### Full version

Full version is only available to those approved by the admins. If you are interested in conducting research or analysis using the dataset, please reach us at `#vtuber-livechat` channel on [holodata Discord server](https://holodata.org/discord) or at `uechiy@acm.org` (for organizations).

| filename               | summary                           | size     |
| ---------------------- | --------------------------------- | -------- |
| `chats_%Y-%m.csv`      | Live chat messages (480,000,000+) | ~ 80 GB  |
| `superchats_%Y-%m.csv` | Super chat messages (1,400,000+)  | ~ 400 MB |
| `deletion_events.csv`  | Deletion events                   | ~ 150 MB |
| `ban_events.csv`       | Ban events                        | ~ 25 MB  |
| `channels.csv`         | Channel index                     | < 1 MB   |
| `channel_stats.csv`    | Channel statistics                | < 1 MB   |

## Dataset Breakdown

Ban and deletion are equivalent to `markChatItemsByAuthorAsDeletedAction` and `markChatItemAsDeletedAction` respectively.

### Chats (`chats_%Y-%m.csv`)

| column          | type    | description                  |
| --------------- | ------- | ---------------------------- |
| timestamp       | string  | UTC timestamp                |
| body            | string  | chat message                 |
| membership      | string  | membership status            |
| isModerator     | boolean | is channel moderator         |
| isVerified      | boolean | is verified account          |
| id              | string  | anonymized chat id           |
| channelId       | string  | anonymized author channel id |
| originVideoId   | string  | source video id              |
| originChannelId | string  | source channel id            |

#### Membership status

| value             | duration                  |
| ----------------- | ------------------------- |
| unknown           | Indistinguishable         |
| non-member        | 0                         |
| less than 1 month | < 1 month                 |
| 1 month           | >= 1 month, < 2 months    |
| 2 months          | >= 2 months, < 6 months   |
| 6 months          | >= 6 months, < 12 months  |
| 1 year            | >= 12 months, < 24 months |
| 2 years           | >= 24 months              |

#### Pandas usage

Set `keep_default_na` to `False` and `na_values` to `''` in `read_csv`. Otherwise, chat message like `NA` would incorrectly be treated as NaN value.

```python
chats = pd.read_csv('../input/vtuber-livechat/chats_2021-03.csv',
                    na_values='',
                    keep_default_na=False,
                    index_col='timestamp',
                    parse_dates=True)
```

### Superchats (`chats_:year:-:month:.csv`)

| column          | type            | description                  |
| --------------- | --------------- | ---------------------------- |
| timestamp       | string          | UTC timestamp                |
| amount          | number          | purchased amount             |
| currency        | string          | currency symbol              |
| color           | string          | color                        |
| significance    | number          | significance                 |
| body            | nullable string | chat message                 |
| id              | string          | anonymized chat id           |
| channelId       | string          | anonymized author channel id |
| originVideoId   | string          | source video id              |
| originChannelId | string          | source channel id            |

#### Color and Significance

| color     | significance | purchase amount (¥) | purchase amount ($) | max. message length |
| --------- | ------------ | ------------------- | ------------------- | ------------------- |
| blue      | 1            | ¥ 100 - 199         | $ 1.00 - 1.99       | 0                   |
| lightblue | 2            | ¥ 200 - 499         | $ 2.00 - 4.99       | 50                  |
| green     | 3            | ¥ 500 - 999         | $ 5.00 - 9.99       | 150                 |
| yellow    | 4            | ¥ 1000 - 1999       | $ 10.00 - 19.99     | 200                 |
| orange    | 5            | ¥ 2000 - 4999       | $ 20.00 - 49.99     | 225                 |
| magenta   | 6            | ¥ 5000 - 9999       | $ 50.00 - 99.99     | 250                 |
| red       | 7            | ¥ 10000 - 50000     | $ 100.00 - 500.00   | 270 - 350           |

#### Pandas usage

Set `keep_default_na` to `False` and `na_values` to `''` in `read_csv`. Otherwise, chat message like `NA` would incorrectly be treated as NaN value.

```python
import pandas as pd
from glob import iglob

sc = pd.concat([
    pd.read_csv(f,
                na_values='',
                keep_default_na=False,
                index_col='timestamp',
                parse_dates=True)
    for f in iglob('../input/vtuber-livechat/superchats_*.csv')
],
               ignore_index=False)
sc.sort_index(inplace=True)
```

### Deletion Events (`deletion_events.csv`)

| column          | type    | description                  |
| --------------- | ------- | ---------------------------- |
| timestamp       | string  | UTC timestamp                |
| id              | string  | anonymized chat id           |
| retracted       | boolean | is deleted by author oneself |
| originVideoId   | string  | source video id              |
| originChannelId | string  | source channel id            |

#### Pandas usage

Insert `deleted_by_mod` column to `chats` DataFrame:

```python
chats = pd.read_csv('../input/vtuber-livechat/chats_2021-03.csv',
                    na_values='',
                    keep_default_na=False)
delet = pd.read_csv('../input/vtuber-livechat/deletion_events.csv',
                    usecols=['id', 'retracted'])

delet = delet[delet['retracted'] == 0]

delet['deleted_by_mod'] = True
chats = pd.merge(chats, delet[['id', 'deleted_by_mod']], how='left')
chats['deleted_by_mod'].fillna(False, inplace=True)
```

### Ban Events (`ban_events.csv`)

Here **Ban** means either to place user in time out or to permanently hide the user's comments on the channel's current and future live streams. This mixup is due to the fact that these actions are indistinguishable from others with the extracted data from `markChatItemsByAuthorAsDeletedAction` event.

| column          | type   | description           |
| --------------- | ------ | --------------------- |
| timestamp       | string | UTC timestamp         |
| channelId       | string | anonymized channel id |
| originVideoId   | string | source video id       |
| originChannelId | string | source channel id     |

#### Pandas usage

Insert `banned` column to `chats` DataFrame:

```python
chats = pd.read_csv('../input/vtuber-livechat/chats_2021-03.csv',
                    na_values='',
                    keep_default_na=False)
ban = pd.read_csv('../input/vtuber-livechat/ban_events.csv',
                  usecols=['channelId', 'originVideoId'])

ban['banned'] = True
chats = pd.merge(chats, ban, on=['channelId', 'originVideoId'], how='left')
chats['banned'].fillna(False, inplace=True)
```

### Channels (`channels.csv`)

| column            | type            | description            |
| ----------------- | --------------- | ---------------------- |
| channelId         | string          | channel id             |
| name              | string          | channel name           |
| name.en           | nullable string | channel name (English) |
| affiliation       | string          | channel affiliation    |
| group             | nullable string | group                  |
| subscriptionCount | number          | subscription count     |
| videoCount        | number          | uploads count          |
| photo             | string          | channel icon           |

Inactive channels have `INACTIVE` in `group` column.

### Channel Statistics (`channel_stats.csv`)

| column              | type   | description                                        |
| ------------------- | ------ | -------------------------------------------------- |
| channelId           | string | channel id                                         |
| period              | string | interested period (%Y-%M)                          |
| chats               | number | number of chats                                    |
| memberChats         | number | number of chats with membership status attached    |
| superChats          | number | number of super chats                              |
| uniqueChatters      | number | number of unique chatters                          |
| uniqueMembers       | number | number of unique members appeared on live chat     |
| uniqueSuperChatters | number | number of unique super chatters                    |
| totalSC             | number | total amount of super chats (JPY)                  |
| averageSC           | number | average amount of super chat (JPY)                 |
| bannedChatters      | number | number of unique chatters marked as banned by mods |
| deletedChats        | number | number of chats deleted by mods                    |

## Consideration

### Anonymization

`id` and `channelId` are anonymized by SHA-1 hashing algorithm with a pinch of undisclosed salt.

### Handling Custom Emojis

All custom emojis are replaced with a Unicode replacement character `U+FFFD`.

### Redundant Ban and Deletion Events

Bans and deletions from multiple moderators for the same person or chat will be logged separately. For simplicity, you can safely ignore all but the first line recorded in time order.

## Citation

```latex
@misc{vtuber-livechat-dataset,
 author={Yasuaki Uechi},
 title={VTuber 400M: Large Scale Virtual YouTubers Live Chat Dataset},
 year={2021},
 month={3},
 version={31},
 url={https://github.com/holodata/vtuber-livechat-dataset}
}
```

## License

- Code: [MIT License](https://github.com/holodata/vtuber-livechat-dataset/blob/master/LICENSE)
- Dataset: [ODC Public Domain Dedication and Licence (PDDL)](https://opendatacommons.org/licenses/pddl/1-0/index.html)
