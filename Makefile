all: build upload

build: preprocess aggregate postprocess

preprocess:
	python3 -m vtlc.preprocess

aggregate:
	python3 -m vtlc.aggregate -I -R1
	rm -f $$RAW_DATA_DIR/superchats_2021-0{1,2}.csv

postprocess:
	python3 -m vtlc.postprocess

upload:
	kaggle datasets version -m "New version" --path $$VTLC_ELEMENTS_DIR
	kaggle datasets version -m "New version" --path $$VTLC_DIR

upload-complete:
	kaggle datasets version -m "New version" --path $$VTLC_COMPLETE_DIR
