# Vtuber 50M: Live Chat Dataset

Massive collection of chat messages and moderation events (ban and deletion) all across Virtual YouTubers' live streams, carefully crafted that can be used for academic research and all other NLP projects.

Download dataset from [Kaggle Datasets](https://www.kaggle.com/uetchy/vtuber-livechat).

## Format

| filename              | summary                         | size    |
| --------------------- | ------------------------------- | ------- |
| `chat.csv`            | Live chat message (64,000,000+) | ~13 GiB |
| `markedAsBan.csv`     | ban event (80,000+)             | ~9 MiB  |
| `markedAsDeleted.csv` | deletion event (200,000+)       | ~25 MiB |

> Ban and deletion are equivalent to `markChatItemsByAuthorAsDeletedAction` and `markChatItemAsDeletedAction` respectively.

We employed [Honeybee](https://github.com/uetchy/honeybee) cluster to collect live chat events across Vtubers' live streams. All sensitive data such as author name or author profile image are omitted from dataset, and author channel id are anonymized by hashing algorithm (with grain of salt).

### Chat

| column          | type             | description                  |
| --------------- | ---------------- | ---------------------------- |
| timestamp       | number           | unixtime                     |
| body            | nullable string  | chat message                 |
| isModerator     | boolean          | is moderator                 |
| isVerified      | boolean          | is verified                  |
| isOwner         | boolean          | is channel owner             |
| isSuperchat     | nullable boolean | is superchat                 |
| isMembership    | nullable boolean | membership status            |
| originVideoId   | string           | origin video id              |
| originChannelId | string           | origin channel id            |
| id              | string           | anonymized chat id           |
| channelId       | string           | anonymized author channel id |

### Ban

| column          | type            | description           |
| --------------- | --------------- | --------------------- |
| timestamp       | nullable number | unixtime              |
| channelId       | string          | anonymized channel id |
| originVideoId   | string          | origin video id       |
| originChannelId | string          | origin channel id     |

### Deletion

| column          | type    | description                  |
| --------------- | ------- | ---------------------------- |
| timestamp       | number  | unixtime                     |
| id              | string  | anonymized chat id           |
| originVideoId   | string  | origin video id              |
| originChannelId | string  | origin channel id            |
| retracted       | boolean | is deleted by author oneself |

## Consideration

### Anonymization for Privacy

`id` and `channelId` are anonymized by SHA-256 hashing algorithm with a pinch of undisclosed salt.

### Handling Custom Emojis

All custom emojis are replaced with a Unicode replacement character `U+FFFD`.

### Redundant Ban/Deletion Events

Bans/deletions from multiple moderators for the same person/chat will be logged separately. For simplicity, you can safely ignore all but the first line recorded in time order.

### Membership

Because we started collecting membership status since 2021-03-14T06:23:14+09:00, chats with empty `membership` before then can be either members or non-members.

### Superchat

Combining the fact that we cannot write a blank chat (except for superchat) with that we started collecting superchat details since 2021-03-14T06:23:14+09:00, chats with empty `body` before then suppose to be superchat.

## Provenance

- **Source:** YouTube Live Chat events (all live streams covered by [Holodex](https://holodex.net))
- **Temporal Coverage:** from 2021-01-16
- **Tool:** [Honeybee](https://github.com/uetchy/honeybee) cluster

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
  url={https://github.com/uetchy/vtuber-livechat-dataset}
}
```

## License

- Code: [MIT License](./LICENSE)
- Dataset: [ODC Public Domain Dedication and Licence (PDDL)](https://opendatacommons.org/licenses/pddl/1-0/index.html)
