generate:
	rm -rf data/*.csv
	python3 vtlc/generate.py

upload:
	kaggle datasets version -m "New version" --path data --delete-old-versions