![Header](https://github.com/holodata/vtuber-livechat-dataset/blob/master/.github/kaggle-dataset-header.png?raw=true)

# Vtuber 50M: Live Chat Dataset

Massive collection of chat messages and moderation events (ban and deletion) all across Virtual YouTubers' live streams, carefully crafted that can be used for academic research and all other NLP projects.

Download all datasets from [Kaggle Datasets](https://www.kaggle.com/uetchy/vtuber-livechat).

## Format

| filename              | summary                                                | size    |
| --------------------- | ------------------------------------------------------ | ------- |
| `chat.csv`            | Live chat messages (16,000,000+)                       | ~4 GiB  |
| `chatLegacy.csv`      | Live chat messages w/ incomplete columns (60,000,000+) | ~12 GiB |
| `markedAsDeleted.csv` | Deletion events (250,000+)                             | ~40 MiB |
| `markedAsBanned.csv`  | Ban events (80,000+)                                   | ~10 MiB |
| `superchat.csv`       | Superchat messages (40,000+)                           | ~13 MiB |
| `channels.csv`        | Channel index                                          | 40 KiB  |

> Ban and deletion are equivalent to `markChatItemsByAuthorAsDeletedAction` and `markChatItemAsDeletedAction` respectively.

We employed [Honeybee](https://github.com/holodata/honeybee) cluster to collect live chat events across Vtubers' live streams. All sensitive data such as author name or author profile image are omitted from dataset, and author channel id are anonymized by SHA-256 hashing algorithm with grain of salt.

### Chat (`chat.csv`)

| column          | type            | description                  |
| --------------- | --------------- | ---------------------------- |
| timestamp       | string          | UTC timestamp                |
| body            | nullable string | chat message                 |
| isModerator     | boolean         | is moderator                 |
| isVerified      | boolean         | is verified                  |
| isSuperchat     | boolean         | is superchat                 |
| isMembership    | boolean         | membership status            |
| originVideoId   | string          | origin video id              |
| originChannelId | string          | origin channel id            |
| id              | string          | anonymized chat id           |
| channelId       | string          | anonymized author channel id |

### Superchat (`superchat.csv`)

| column            | type            | description                  |
| ----------------- | --------------- | ---------------------------- |
| timestamp         | string          | UTC timestamp                |
| amount            | number          | purchased amount             |
| currency          | string          | currency symbol              |
| significance      | number          | significance                 |
| color             | string          | color                        |
| body              | nullable string | chat message                 |
| originVideoId     | string          | origin video id              |
| originChannel     | string          | origin channel name          |
| originAffiliation | string          | origin affiliation           |
| originGroup       | string          | origin group                 |
| id                | string          | anonymized chat id           |
| channelId         | string          | anonymized author channel id |

#### Color and Significance

| color     | significance |
| --------- | ------------ |
| blue      | 1            |
| lightblue | 2            |
| green     | 3            |
| yellow    | 4            |
| orange    | 5            |
| magenta   | 6            |
| red       | 7            |

### Ban (`markedAsBanned.csv`)

| column          | type   | description           |
| --------------- | ------ | --------------------- |
| timestamp       | string | UTC timestamp         |
| channelId       | string | anonymized channel id |
| originVideoId   | string | origin video id       |
| originChannelId | string | origin channel id     |

### Deletion (`markedAsDeleted.csv`)

| column          | type    | description                  |
| --------------- | ------- | ---------------------------- |
| timestamp       | string  | UTC timestamp                |
| id              | string  | anonymized chat id           |
| originVideoId   | string  | origin video id              |
| originChannelId | string  | origin channel id            |
| retracted       | boolean | is deleted by author oneself |

### Channels (`channels.csv`)

| column      | type            | description         |
| ----------- | --------------- | ------------------- |
| channelId   | string          | channel id          |
| name        | string          | channel name        |
| name_en     | nullable string | channel name (en)   |
| affiliation | string          | channel affiliation |
| group       | nullable string | group               |
| sub_count   | string          | subscription count  |
| video_count | string          | uploads count       |

## Consideration

### Anonymization

`id` and `channelId` are anonymized by SHA-256 hashing algorithm with a pinch of undisclosed salt.

### Handling Custom Emojis

All custom emojis are replaced with a Unicode replacement character `U+FFFD`.

### Redundant Ban/Deletion Events

Bans/deletions from multiple moderators for the same person/chat will be logged separately. For simplicity, you can safely ignore all but the first line recorded in time order.

### Membership

Because we started collecting membership status since 2021-03-14T06:23:14+09:00, chats with empty `membership` before then can be either members or non-members.

### Superchat

Combining the fact that we cannot write a blank chat (except for superchat) with that we started collecting superchat details since 2021-03-14T06:23:14+09:00, chats with empty `body` before then can be treated as superchat.

## Provenance

- **Source:** YouTube Live Chat events (all streams covered by [Holodex](https://holodex.net))
- **Temporal Coverage:** start from 2021-01-16 (live chat), 2021-03-16 (superchat)
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
  title={Vtuber 50M: Large Scale Virtual YouTubers Live Chat Dataset},
  year={2021},
  month={3},
  version={1.0},
  url={https://github.com/holodata/vtuber-livechat-dataset}
}
```

## License

- Code: [MIT License](https://github.com/holodata/vtuber-livechat-dataset/blob/master/LICENSE)
- Dataset: [ODC Public Domain Dedication and Licence (PDDL)](https://opendatacommons.org/licenses/pddl/1-0/index.html)
