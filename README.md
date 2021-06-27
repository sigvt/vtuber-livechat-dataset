![Header](https://github.com/holodata/vtuber-livechat-dataset/blob/master/.github/kaggle-dataset-header.png?raw=true)

# Vtuber 300M: Live Chat and Moderation Events

Huge collection of hundreds of millions of live chat and super chat messages and moderation events (ban and deletion) all across Virtual YouTubers' live streams, ready for academic research and any kinds of NLP projects.

Download the dataset from [Kaggle Datasets](https://www.kaggle.com/uetchy/vtuber-livechat).

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
- Sentence Transformer for Live Chat

See [public notebooks](https://www.kaggle.com/uetchy/vtuber-livechat/code?datasetId=1209921) for ideas.

## Dataset Breakdown

| filename                        | summary                                        | size     |
| ------------------------------- | ---------------------------------------------- | -------- |
| `chats_:year:-:month:.csv`      | Live chat messages (300,000,000+)              | ~ 55 GB  |
| `superchats_:year:-:month:.csv` | Super chat messages (1,000,000+)               | ~ 250 MB |
| `deletion_events.csv`           | Deletion events                                | ~ 100 MB |
| `ban_events.csv`                | Ban events                                     | ~ 20 MB  |
| `channels.csv`                  | Channel index                                  | < 1 MB   |
| `chat_stats.csv`                | Statistics for chats, ban, and deletion events | < 1 MB   |
| `superchat_stats.csv`           | Statistics for super chats                     | < 1 MB   |

> Ban and deletion are equivalent to `markChatItemsByAuthorAsDeletedAction` and `markChatItemAsDeletedAction` respectively.

We employed [Honeybee](https://github.com/holodata/honeybee) cluster to collect live chat events across Vtubers' live streams. All sensitive data such as author name or author profile image are omitted from the dataset, and author channel id is anonymized by SHA-1 hashing algorithm with a grain of salt.

### Chats (`chats_:year:-:month:.csv`)

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

### Chat Statistics (`chat_stats.csv`)

| column        | type   | description                                     |
| ------------- | ------ | ----------------------------------------------- |
| channelId     | string | channel id                                      |
| period        | string | interested period (%Y-%M)                       |
| chatCount     | number | number of chats                                 |
| chatNunique   | number | number of unique users                          |
| banCount      | number | number of ban events                            |
| banNunique    | number | number of unique users marked as banned by mods |
| deletionCount | number | number of chats deleted by mods                 |

### Super Chat Statistics (`superchat_stats.csv`)

| column     | type   | description                        |
| ---------- | ------ | ---------------------------------- |
| channelId  | string | channel id                         |
| period     | string | interested period (%Y-%M)          |
| scCount    | number | number of super chats              |
| scNunique  | number | number of unique users             |
| scTotalJPY | number | total amount of super chats (JPY)  |
| scMeanJPY  | number | average amount of super chat (JPY) |

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
 title={Vtuber 300M: Large Scale Virtual YouTubers Live Chat Dataset},
 year={2021},
 month={3},
 version={29},
 url={https://github.com/holodata/vtuber-livechat-dataset}
}
```

## License

- Code: [MIT License](https://github.com/holodata/vtuber-livechat-dataset/blob/master/LICENSE)
- Dataset: [ODC Public Domain Dedication and Licence (PDDL)](https://opendatacommons.org/licenses/pddl/1-0/index.html)
