generate:
	rm -rf data/*.csv
	python3 vtlc/generate.py
	tar zcvf dataset.tar.gz data/*.csv

upload:
	kaggle datasets version -m "New version" --path data --delete-old-versions