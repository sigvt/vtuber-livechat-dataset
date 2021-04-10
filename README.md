![Header](https://github.com/holodata/vtuber-livechat-dataset/blob/master/.github/kaggle-dataset-header.png?raw=true)

# Vtuber 100M: Live Chat and Moderation Events

Huge collection of hundreds of millions of chat messages and moderation events (ban and deletion) all across Virtual YouTubers' live streams, ready for academic research and any kinds of NLP projects.

Download the dataset from [Kaggle Datasets](https://www.kaggle.com/uetchy/vtuber-livechat).

## Format

| filename                   | summary                                                  | size    |
| -------------------------- | -------------------------------------------------------- | ------- |
| `chats_<year>-<month>.csv` | Live chat messages (50,000,000+)                         | ~10 GiB |
| `superchats.csv`           | Super chat messages (200,000+)                           | ~50 MiB |
| `deletion_events.csv`      | Deletion events                                          | ~40 MiB |
| `ban_events.csv`           | Ban events                                               | ~10 MiB |
| `channels.csv`             | Channel index                                            | 40 KiB  |
| `chats_legacy.csv`         | Live chat messages w/o membership info (will be removed) | ~13 GiB |

> Ban and deletion are equivalent to `markChatItemsByAuthorAsDeletedAction` and `markChatItemAsDeletedAction` respectively.

We employed [Honeybee](https://github.com/holodata/honeybee) cluster to collect live chat events across Vtubers' live streams. All sensitive data such as author name or author profile image are omitted from the dataset, and author channel id is anonymized by SHA-1 hashing algorithm with a grain of salt.

### Chats (`chats_%Y-%m.csv`)

| column          | type            | description                  |
| --------------- | --------------- | ---------------------------- |
| timestamp       | string          | UTC timestamp                |
| body            | nullable string | chat message                 |
| membership      | string          | membership status            |
| isModerator     | boolean         | is channel moderator         |
| isVerified      | boolean         | is verified account          |
| id              | string          | anonymized chat id           |
| channelId       | string          | anonymized author channel id |
| originVideoId   | string          | origin video id              |
| originChannelId | string          | origin channel id            |

#### Membership status

| value             | duration                  |
| ----------------- | ------------------------- |
| non-member        | N/A                       |
| less than 1 month | < 1 month                 |
| 1 month           | >= 1 month, < 2 months    |
| 2 months          | >= 2 months, < 6 months   |
| 6 months          | >= 6 months, < 12 months  |
| 1 year            | >= 12 months, < 24 months |
| 2 years           | >= 24 months              |

### Superchats (`superchats.csv`)

| column            | type            | description                  |
| ----------------- | --------------- | ---------------------------- |
| timestamp         | string          | UTC timestamp                |
| amount            | number          | purchased amount             |
| currency          | string          | currency symbol              |
| significance      | number          | significance                 |
| color             | string          | color                        |
| body              | nullable string | chat message                 |
| id                | string          | anonymized chat id           |
| channelId         | string          | anonymized author channel id |
| originVideoId     | string          | origin video id              |
| originChannel     | string          | origin channel name          |
| originAffiliation | string          | origin affiliation           |
| originGroup       | string          | origin group                 |

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

### Deletion Events (`deletion_events.csv`)

| column          | type    | description                  |
| --------------- | ------- | ---------------------------- |
| timestamp       | string  | UTC timestamp                |
| id              | string  | anonymized chat id           |
| retracted       | boolean | is deleted by author oneself |
| originVideoId   | string  | origin video id              |
| originChannelId | string  | origin channel id            |

### Ban Events (`ban_events.csv`)

Here **Ban** means either to place user in time out or to permanently hide the user's comments on the channel's current and future live streams. This mixup is due to the fact that these actions are indistinguishable from others with the extracted data from `markChatItemsByAuthorAsDeletedAction` event.

| column          | type   | description           |
| --------------- | ------ | --------------------- |
| timestamp       | string | UTC timestamp         |
| channelId       | string | anonymized channel id |
| originVideoId   | string | origin video id       |
| originChannelId | string | origin channel id     |

### Channels (`channels.csv`)

| column            | type            | description            |
| ----------------- | --------------- | ---------------------- |
| channelId         | string          | channel id             |
| name              | string          | channel name           |
| name.en           | nullable string | channel name (English) |
| affiliation       | string          | channel affiliation    |
| group             | nullable string | group                  |
| subscriptionCount | string          | subscription count     |
| videoCount        | string          | uploads count          |

## Consideration

### Anonymization

`id` and `channelId` are anonymized by SHA-1 hashing algorithm with a pinch of undisclosed salt.

### Handling Custom Emojis

All custom emojis are replaced with a Unicode replacement character `U+FFFD`.

### Redundant Ban/Deletion Events

Bans/deletions from multiple moderators for the same person/chat will be logged separately. For simplicity, you can safely ignore all but the first line recorded in time order.

## Provenance

- **Source:** YouTube Live Chat events (all streams covered by [Holodex](https://holodex.net), including Hololive, Nijisanji, 774inc, etc)
- **Temporal Coverage (UTC):**
  - Chats: from 2021-03-14
  - Superchats: from 2021-03-16
  - Legacy Chats: from 2021-01-16
- **Tool:** [Honeybee](https://github.com/holodata/honeybee)

## Research Ideas

- Toxic Chat Classification
- Spam Detection
- Demographic Visualization
- Sentence Encoder

## Citation

```latex
@misc{vtuber-livechat-dataset,
 author={Yasuaki Uechi},
 title={Vtuber 100M: Large Scale Virtual YouTubers Live Chat Dataset},
 year={2021},
 month={3},
 version={19},
 url={https://github.com/holodata/vtuber-livechat-dataset}
}
```

## License

- Code: [MIT License](https://github.com/holodata/vtuber-livechat-dataset/blob/master/LICENSE)
- Dataset: [ODC Public Domain Dedication and Licence (PDDL)](https://opendatacommons.org/licenses/pddl/1-0/index.html)
