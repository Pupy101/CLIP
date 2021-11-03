from train import train_clip
from inference import inference
from config import Config as clip_config


if __name__ == '__main__':
    if clip_config.TYPE_USING == 'train':
        train_clip(clip_config)
    elif clip_config.TYPE_USING == 'eval':
        inference(clip_config)
