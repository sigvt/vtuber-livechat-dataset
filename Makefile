all: build upload

build:
	python3 -m vtlc.aggregate

upload:
	kaggle datasets version -m "New version" --path data --delete-old-versions
