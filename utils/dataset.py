from typing import Callable, Dict, Optional

import cv2
import torch
import pandas as pd

from torch.utils.data import Dataset


class TextAndImageFromCSV(Dataset):
    """
    Torch dataset for training CLIP
    """

    def __init__(
            self,
            csv: pd.DataFrame,
            tokenizer: Callable,
            max_seq_len: int,
            transform: Optional[Callable] = None
    ):
        """
        Method for init dataset
        :param csv: pandas.DataFrame with 2 columns:
            first - path to image;
            second - text description.
        :param tokenizer: tokenizer for text
        :param max_seq_len: max length for token sequence
        :param transform: augmentation for image
        """
        self.csv = csv
        self.tokenizer = tokenizer
        self.max_seq_len = max_seq_len
        self.transform = transform

    def __getitem__(self, item) -> Dict[str, torch.Tensor]:
        """
        Method for getting pair of image and text
        :param item: index of item
        :return: dict with two keys: image and text
        """
        img = cv2.cvtColor(
            cv2.imread(self.csv.iloc[item, 0]),
            cv2.COLOR_BGR2RGB
        )
        if self.transform is not None:
            img = self.transform(image=img)['image']

        description = self.csv.iloc[item, 1]
        text = self.tokenizer(
            description,
            return_tensors="pt"
        )['input_ids'].squeeze(0)[:self.max_seq_len]
        padding_count = self.max_seq_len - len(text)
        if padding_count:
            text = torch.cat([
                text,
                torch.tensor([0] * padding_count, dtype=torch.int)
            ])

        return {
            'image': img,
            'text': text
        }

    def __len__(self) -> int:
        """
        Method for getting count of pairs
        :return: count of pairs
        """
        return self.csv.shape[0]


class ImageFromCSV(Dataset):
    """
    Torch dataset for inference CLIP with image
    """

    def __init__(
            self,
            csv: pd.DataFrame,
            transform: Optional[Callable] = None
    ):
        """
        Method for init dataset
        :param csv: pandas.DataFrame with 1 column - path to image
        :param transform: augmentation for image
        """
        self.csv = csv
        self.transform = transform

    def __getitem__(self, item) -> Dict[str, torch.Tensor]:
        """
        Method for getting image and it's index in pandas.DataFrame
        :param item: index of item
        :return: dict with two keys: image and index
        """
        img = cv2.cvtColor(
            cv2.imread(self.csv.iloc[item, 0]),
            cv2.COLOR_BGR2RGB
        )
        if self.transform is not None:
            img = self.transform(image=img)['image']

        return {
            'image': img,
            'index': torch.tensor(item).long()
        }

    def __len__(self) -> int:
        """
        Method for getting count of pairs
        :return: count of pairs
        """
        return self.csv.shape[0]
