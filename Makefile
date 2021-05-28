all: build upload

preprocess:
	python3 -m vtlc.preprocess

aggregate:
	python3 -m vtlc.aggregate -R0
	rm -f datasets/vtuber-livechat/superchats_2021-0{1,2}.csv

postprocess:
	python3 -m vtlc.postprocess

build: preprocess aggregate postprocess

upload:
	kaggle datasets version -m "New version" --path datasets/vtuber-livechat
