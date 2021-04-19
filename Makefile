all: build upload

build:
	python3 -m vtlc.preprocess
	python3 -m vtlc.aggregate -R
	cp datasets/vtuber-livechat/superchats.csv datasets/vtuber-superchats/superchats.csv

upload:
	kaggle datasets version -m "New version" --path datasets/vtuber-livechat
