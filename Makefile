all: build upload

build:
	python3 -m vtlc.preprocess

	python3 -m vtlc.aggregate -R0
	rm -f datasets/vtuber-livechat/superchats_2021-0{1,2}.csv

	python3 -m vtlc.postprocess

upload:
	kaggle datasets version -m "New version" --path datasets/vtuber-livechat
