import os
import pickle
from collections import namedtuple
import lmdb
import tensorflow as tf


CodeRow = namedtuple('CodeRow', ['top', 'bottom', 'filename'])


class LMDBDataset(tf.data.Dataset):
    def __init__(self, path):
        self.env = lmdb.open(
            path,
            max_readers=32,
            readonly=True,
            lock=False,
            readahead=False,
            meminit=False,
        )

        if not self.env:
            raise IOError('Cannot open lmdb dataset', path)

        with self.env.begin(write=False) as txn:
            self.length = int(txn.get('length'.encode('utf-8')).decode('utf-8'))

    def __len__(self):
        return self.length

    def __getitem__(self, index):
        with self.env.begin(write=False) as txn:
            key = str(index).encode('utf-8')

            row = pickle.loads(txn.get(key))

        return tf.convert_to_tensor(row.top), tf.convert_to_tensor(row.bottom), row.filename
