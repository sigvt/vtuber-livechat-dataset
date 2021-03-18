all: build upload

build:
	rm -rf data/*.csv
	python3 -m vtlc.aggregate

upload:
	kaggle datasets version -m "New version" --path data --delete-old-versions
