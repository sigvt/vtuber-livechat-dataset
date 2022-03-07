![Header](https://github.com/holodata/vtuber-livechat-dataset/blob/master/.github/kaggle-dataset-header.png?raw=true)

# VTuber 1B: Live Chat and Moderation Events

**VTuber 1B** is an academic purpose NLP dataset, collecting over a billion live chats, superchats, and moderation events (bans/deletions) from virtual YouTubers' live streams.

Download the dataset from [Kaggle Datasets](https://www.kaggle.com/uetchy/vtuber-livechat) and join `#livechat-dataset` channel on [holodata Discord](https://holodata.org/discord) for discussions.

> We also offer [❤️‍🩹 Sensai](https://github.com/holodata/sensai-dataset), a live chat dataset specifically made for building ML models for spam detection / toxic chat classification.

## Provenance

- **Source:** YouTube live chat events collected by our [Honeybee](https://github.com/holodata/honeybee) cluster. [Holodex](https://holodex.net) is a stream index provider for Honeybee which covers Hololive, Nijisanji, 774inc, etc.
- **Temporal Coverage:**
  - Chats: from 2021-01-15
  - Super chats: from 2021-03-16
  - Super stickers: from 2022-01-20 (N/A yet)
  - Membership joining events: from 2021-10-18 (N/A yet)
  - Membership milestones: from 2021-10-20 (N/A yet)
  - Membership gifts: N/A
  - Placeholders: from 2022-01-21 (N/A yet)
- **Update Frequency:**
  - At least once every 6 months

## Research Ideas

- Toxic Chat Classification
- Spam Detection
- Demographic Visualization
- Superchat Analysis
- Training neural language models

See public notebooks built on [VTuber 1B](https://www.kaggle.com/uetchy/vtuber-livechat/code) and [VTuber 1B Elements](https://www.kaggle.com/uetchy/vtuber-livechat-elements/code) for ideas.

> We employed [Honeybee](https://github.com/holodata/honeybee) cluster to collect real-time live chat events across major Vtubers' live streams. All sensitive data such as author name or author profile image are omitted from the dataset, and author channel id is anonymized by SHA-1 hashing algorithm with a grain of salt.

## Editions

### VTuber 1B Elements

[Kaggle Datasets](https://www.kaggle.com/uetchy/vtuber-livechat-elements) (2 MB)

VTuber 1B Elements is most suitable for statistical visualizations and exploratory data analysis.

| filename              | summary               |
| --------------------- | --------------------- |
| `channels.csv`        | Channel index         |
| `chat_stats.csv`      | Chat statistics       |
| `superchat_stats.csv` | Super Chat statistics |

### VTuber 1B

[Kaggle Datasets](https://www.kaggle.com/uetchy/vtuber-livechat) (47 GB)

VTuber 1B is most suitable for frequency analysis. This edition includes only the essential columns in order to reduce dataset size and make it faster from Kaggle Kernels to load data in.

| filename                   | summary                            |
| -------------------------- | ---------------------------------- |
| `chats_%Y-%m.parquet`      | Live chat events (> 1,000,000,000) |
| `superchats_%Y-%m.parquet` | Super chat events (> 4,000,000)    |
| `deletion_events.parquet`  | Deletion events                    |
| `ban_events.parquet`       | Ban events                         |

### VTuber 1B Complete

VTuber 1B Complete is only available to those approved by the admins. If you are interested in conducting research using this edition, please reach us at `contact@holodata.org` (for organizations only).

| filename                   | summary                              |
| -------------------------- | ------------------------------------ |
| `chats_%Y-%m.parquet`      | Live chat messages (> 1,000,000,000) |
| `superchats_%Y-%m.parquet` | Super chat messages (> 4,000,000)    |
| `deletion_events.parquet`  | Deletion events                      |
| `ban_events.parquet`       | Ban events                           |

## Dataset Breakdown

> Ban and deletion are equivalent to `markChatItemsByAuthorAsDeletedAction` and `markChatItemAsDeletedAction` respectively.

### Channels (`channels.csv`)

| column            | type            | description            |
| ----------------- | --------------- | ---------------------- |
| channelId         | string          | channel id             |
| name              | string          | channel name           |
| englishName       | nullable string | channel name (English) |
| affiliation       | string          | channel affiliation    |
| group             | nullable string | group                  |
| subscriptionCount | number          | subscription count     |
| videoCount        | number          | uploads count          |
| photo             | string          | channel icon           |

Inactive channels have `INACTIVE` in `group` column.

#### Pandas usage

```python
import pandas as pd

dtype_dict = {
    'channelId': 'category',
    'name': 'category',
    'englishName': 'category',
    'affiliation': 'category',
    'subscriptionCount': 'int32',
    'videoCount': 'int16',
    'photo': 'category'
}
chats = pd.read_csv('../input/vtuber-livechat-elements/channels.csv', dtype=dtype_dict)
```

### Chat Statistics (`chat_stats.csv`)

| column         | type   | description                                        |
| -------------- | ------ | -------------------------------------------------- |
| channelId      | string | channel id                                         |
| period         | string | interested period (%Y-%M)                          |
| chats          | number | number of chats                                    |
| memberChats    | number | number of chats with membership status attached    |
| uniqueChatters | number | number of unique chatters                          |
| uniqueMembers  | number | number of unique members appeared on live chat     |
| bannedChatters | number | number of unique chatters marked as banned by mods |
| deletedChats   | number | number of chats deleted by mods                    |

#### Pandas usage

```python
import pandas as pd

chat_stats = pd.read_csv('../input/vtuber-livechat-elements/chat_stats.csv'))
sc_stats = pd.read_csv('../input/vtuber-livechat-elements/superchat_stats.csv'))
stats = pd.merge(chat_stats, sc_stats, on=['period', 'channelId'], how='left')
```

### Super Chat Statistics (`superchat_stats.csv`)

| column               | type   | description                        |
| -------------------- | ------ | ---------------------------------- |
| channelId            | string | channel id                         |
| period               | string | interested period (%Y-%M)          |
| superChats           | number | number of super chats              |
| uniqueSuperChatters  | number | number of unique super chatters    |
| totalSC              | number | total amount of super chats (JPY)  |
| averageSC            | number | average amount of super chat (JPY) |
| totalMessageLength   | number | total message length               |
| averageMessageLength | number | average mesage length              |
| mostFrequentCurrency | string | most frequent currency             |
| mostFrequentColor    | string | most frequent color                |

### Chats (`chats_%Y-%m.parquet`)

| column          | type             | description                 | in standard version   |
| --------------- | ---------------- | --------------------------- | --------------------- |
| timestamp       | string           | ISO 8601 UTC timestamp      | limited accuracy      |
| id              | string           | chat id                     | N/A                   |
| authorName      | string           | author name                 | N/A                   |
| authorChannelId | string           | author channel id           | anonymized            |
| body            | string           | chat message                | N/A                   |
| bodyLength      | number           | chat message length         | standard version only |
| membership      | string           | membership status           | N/A                   |
| isMember        | nullable boolean | is member (null if unknown) | standard version only |
| isModerator     | boolean          | is channel moderator        | N/A                   |
| isVerified      | boolean          | is verified account         | N/A                   |
| videoId         | string           | source video id             |                       |
| channelId       | string           | source channel id           |                       |

#### Membership status

| value      | duration                  |
| ---------- | ------------------------- |
| unknown    | Indistinguishable         |
| non-member | 0                         |
| new        | < 1 month                 |
| 1 month    | >= 1 month, < 2 months    |
| 2 months   | >= 2 months, < 6 months   |
| 6 months   | >= 6 months, < 12 months  |
| 1 year     | >= 12 months, < 24 months |
| 2 years    | >= 24 months              |

#### Pandas usage

```python
import pandas as pd

chats = pd.read_parquet('../input/vtuber-livechat/chats_2022-02.parquet')
```

### Superchats (`chats_:year:-:month:.parquet`)

| column          | type            | description                  | in standard version |
| --------------- | --------------- | ---------------------------- | ------------------- |
| timestamp       | string          | ISO 8601 UTC timestamp       | limited accuracy    |
| id              | string          | chat id                      | N/A                 |
| authorName      | string          | author name                  | N/A                 |
| authorChannelId | string          | author channel id            | anonymized          |
| body            | nullable string | chat message                 | N/A                 |
| amount          | number          | purchased amount             |                     |
| currency        | string          | three-letter currency symbol |                     |
| color           | string          | color                        | N/A                 |
| significance    | number          | significance                 |                     |
| videoId         | string          | source video id              | N/A                 |
| channelId       | string          | source channel id            |                     |

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

```python
import pandas as pd
from glob import iglob

sc = pd.concat([
    pd.read_parquet(f)
    for f in iglob('../input/vtuber-livechat/superchats_*.parquet')
], ignore_index=False)
sc.sort_index(inplace=True)
```

### Deletion Events (`deletion_events.parquet`)

| column    | type    | description                  | in standard version |
| --------- | ------- | ---------------------------- | ------------------- |
| timestamp | string  | UTC timestamp                |                     |
| id        | string  | chat id                      |                     |
| retracted | boolean | is deleted by author oneself |                     |
| videoId   | string  | source video id              |                     |
| channelId | string  | source channel id            |                     |

#### Pandas usage

Insert `deleted_by_mod` column to `chats` DataFrame:

```python
chats = pd.read_parquet('../input/vtuber-livechat/chats_2022-02.parquet')
delet = pd.read_parquet('../input/vtuber-livechat/deletion_events.parquet', columns=['id', 'retracted'])

delet = delet[delet['retracted'] == 0]

delet['deleted_by_mod'] = True
chats = pd.merge(chats, delet[['id', 'deleted_by_mod']], how='left')
chats['deleted_by_mod'].fillna(False, inplace=True)
```

### Ban Events (`ban_events.parquet`)

Here **Ban** means either to place user in time out or to permanently hide the user's comments on the channel's current and future live streams. This mixup is due to the fact that these actions are indistinguishable from others with the extracted data from `markChatItemsByAuthorAsDeletedAction` event.

| column          | type   | description       | in standard version |
| --------------- | ------ | ----------------- | ------------------- |
| timestamp       | string | UTC timestamp     |                     |
| authorChannelId | string | channel id        | anonymized          |
| videoId         | string | source video id   |                     |
| channelId       | string | source channel id |                     |

#### Pandas usage

Insert `banned` column to `chats` DataFrame:

```python
chats = pd.read_parquet('../input/vtuber-livechat/chats_2022-02.parquet')
ban = pd.read_parquet('../input/vtuber-livechat/ban_events.parquet', columns=['authorChannelId', 'videoId'])

ban['banned'] = True
chats = pd.merge(chats, ban, on=['authorChannelId', 'videoId'], how='left')
chats['banned'].fillna(False, inplace=True)
```

## Consideration

### Anonymization

`id` and `authorChannelId` are anonymized by SHA-1 hashing algorithm with a pinch of undisclosed salt.

### Handling Custom Emojis

All custom emojis are replaced with a Unicode replacement character � (`U+FFFD`).

### Redundant Ban and Deletion Events

Bans and deletions from multiple moderators for the same person or chat will be logged separately. For simplicity, you can safely ignore all but the first line recorded in time order.

## Citation

```latex
@misc{vtuber-livechat-dataset,
 author={Yasuaki Uechi},
 title={VTuber 1B: Large-scale Live Chat and Moderation Events Dataset},
 year={2022},
 month={2},
 version={37},
 url={https://holodata.org/vtuber-1b}
}
```

## License

- Code: [MIT License](https://github.com/holodata/vtuber-livechat-dataset/blob/master/LICENSE)
- Dataset: [ODC Public Domain Dedication and Licence (PDDL)](https://opendatacommons.org/licenses/pddl/1-0/index.html)
