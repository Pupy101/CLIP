"""
Module with augmentations for image
"""

import albumentations as A

from albumentations.pytorch import ToTensorV2

# augmentations for train
train = A.Compose([
    A.SmallestMaxSize(max_size=240),
    A.RandomCrop(height=224, width=224),
    A.Flip(),
    A.RandomBrightnessContrast(
        brightness_limit=0.2,
        contrast_limit=0.2,
        p=0.3
    ),
    A.CLAHE(),
    A.GaussNoise(),
    A.CoarseDropout(),
    A.ChannelDropout(),
    A.Rotate(limit=15),
    A.Normalize(),
    ToTensorV2(),
])

# augmentations for valid
valid = A.Compose([
    A.SmallestMaxSize(max_size=230),
    A.CenterCrop(height=224, width=224),
    A.Normalize(),
    ToTensorV2(),
])

augmentations = {
    'train': train,
    'valid': valid,
}


__all__ = ['augmentations']
