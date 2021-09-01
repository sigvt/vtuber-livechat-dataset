import os

DATASET_DIR_FULL = os.environ['DATASET_DIR_FULL']
DATASET_DIR = os.environ['DATASET_DIR']

os.makedirs(DATASET_DIR_FULL, exist_ok=True)
os.makedirs(DATASET_DIR, exist_ok=True)