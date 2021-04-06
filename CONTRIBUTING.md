# Contribution Guide

## Accumulate data

We use [Honeybee](https://github.com/holodata/honeybee) to collect live chat data from YouTube.

## Generate CSV from MongoDB database

```
MONGODB_URI=<mongo_uri> make build
```

## Upload new version of dataset (Maintainers only)

```
make upload
```
