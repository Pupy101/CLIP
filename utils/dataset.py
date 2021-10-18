import re

from typing import Callable
from os.path import join as join_path

import cv2
import torch
import pandas as pd

from numpy.random import shuffle, choice
from torch.utils.data import Dataset


class TextAndImage(Dataset):

    def __init__(
            self,
            csv: pd.DataFrame,
            tokenizer: Callable,
            max_size_seq_len: int,
            transform: Callable = None
    ):
        self.csv = csv
        self.tokenizer = tokenizer
        self.max_size_seq_len = max_size_seq_len
        self.transform = transform

    def __getitem__(self, item):
        img = cv2.cvtColor(
            cv2.imread(self.csv['image_name'][item]),
            cv2.COLOR_BGR2RGB
        )
        if self.transform is not None:
            img = self.transform(image=img)['image']

        texts = self.csv['comment'][item]
        marks = [5 - x for x in self.csv['comment_number'][item]]
        probability = [x / sum(marks) for x in marks]

        text = choice(texts, p=probability)
        tokenized_text = self.tokenizer(
            text,
            return_tensors="pt"
        )['input_ids'].squeeze(0)[:self.max_size_seq_len]
        padding_count = self.max_size_seq_len - len(tokenized_text)
        if padding_count:
            tokenized_text = torch.cat(
                [
                    tokenized_text,
                    torch.tensor([0] * padding_count, dtype=torch.int64)
                ]
            )
        return {
            'image': img,
            'text': tokenized_text
        }

    def __len__(self):
        return self.csv.shape[0]


def create_dataset(
        path_to_csv: str,
        dir_image: str,
        tokenizer: Callable,
        max_size_seq_len: int,
        transform: Callable
):
    df = pd.read_csv(path_to_csv, delimiter='|')
    df.columns = [x.strip() for x in df.columns]
    for column in df.columns:
        df[column] = df[column].apply(lambda x: x.strip() if isinstance(x, str) else x)
    index = df['comment_number'].str.isdigit()
    df = df[index]
    df['image_name'] = df['image_name'].apply(lambda x: join_path(dir_image, x))
    df['comment_number'] = pd.to_numeric(df['comment_number'])
    shuffled_index = shuffle(df.index)
    count_examples = len(shuffled_index)
    train_index = shuffled_index[:round(count_examples * 0.8)]
    valid_index = shuffled_index[round(count_examples * 0.8):]
    train_df, valid_df = df[train_index], df[valid_index]
    return (
        TextAndImage(
            csv=train_df,
            tokenizer=tokenizer,
            max_size_seq_len=max_size_seq_len,
            transform=transform['train']
        ),
        TextAndImage(
            csv=valid_df,
            tokenizer=tokenizer,
            max_size_seq_len=max_size_seq_len,
            transform=transform['valid']
        )
    )
