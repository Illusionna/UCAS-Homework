PRETRAINED_PATH = '/data2/lyx/ckpts/bert-large-uncased'
MODEL_COUNT = 5
EPOCHS = 10

import os
for mid in range(MODEL_COUNT):
    os.system(f"python adaboost_staged.py -m {PRETRAINED_PATH} -e {EPOCHS} -s {mid}")