# Contribution Guide

## Accumulate data

We use [honeybee](https://github.com/uetchy/honeybee) to collect live chat data from YouTube.

## Generate CSV from MongoDB database

```
MONGODB_URI=<mongo_uri> make generate
```

## Upload new version of dataset (Maintainers only)

```
make upload
```
