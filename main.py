from src import train_clip, inference_clip
from config import Config as clip_config


if __name__ == '__main__':
    if clip_config.TYPE_USING == 'train':
        print('Training model')
        train_clip(clip_config)
    elif clip_config.TYPE_USING == 'eval':
        print('Evaluation model')
        inference_clip(clip_config)
