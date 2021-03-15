generate:
	rm -rf data/*.csv
	python3 -m vtlc.generate

upload:
	kaggle datasets version -m "New version" --path data --delete-old-versions