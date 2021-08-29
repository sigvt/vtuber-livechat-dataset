all: build upload

build: preprocess aggregate postprocess

preprocess:
	python3 -m vtlc.preprocess

aggregate:
	python3 -m vtlc.aggregate -I -R1
	rm -f $$DATASET_ROOT/$$DATASET_NAME/superchats_2021-0{1,2}.csv

postprocess:
	python3 -m vtlc.postprocess -sd

upload:
	kaggle datasets version -m "New version" --path $$DATASET_ROOT/$$DATASET_NAME

uploadFull:
	kaggle datasets version -m "New version" --path $$DATASET_ROOT/$$DATASET_NAME_FULL
