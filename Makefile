all: build upload

build:
	python3 -m vtlc.preprocess
	python3 -m vtlc.aggregate -R

upload:
	kaggle datasets version -m "New version" --path data
