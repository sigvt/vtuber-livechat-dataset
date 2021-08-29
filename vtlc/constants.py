import os
from os.path import join

DATASET_ROOT = os.environ['DATASET_ROOT']
DATASET_NAME = os.environ['DATASET_NAME']
DATASET_NAME_FULL = os.environ['DATASET_NAME_FULL']

DATASET_DIR = join(DATASET_ROOT, DATASET_NAME)
DATASET_DIR_FULL = join(DATASET_ROOT, DATASET_NAME_FULL)

os.makedirs(DATASET_DIR, exist_ok=True)
os.makedirs(DATASET_DIR_FULL, exist_ok=True)