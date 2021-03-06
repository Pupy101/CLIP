from typing import Optional, Tuple, Union

import torch
import numpy as np
import transformers

from torch import nn
from torchvision import models


class CLIP(nn.Module):
    """
    CLIP model with 2 parts:
        image part - CNN and text part - Transformer
    """

    def __init__(
            self,
            image_embedding: nn.Module,
            image_shape: int,
            text_embedding: nn.Module,
            text_shape: int
    ):
        """
        Method for init CLIP
        :param image_embedding: CNN for embedding image
        :param image_shape: dimension of image embedding
        :param text_embedding: Transform for embedding text
        :param text_shape: dimension of text embedding
        """
        super().__init__()
        # it's need for inference
        self.text_model = text_embedding
        # overall dim is 'text_shape'
        self.image_model = (
            image_embedding
            if image_shape == text_shape
            else nn.Sequential(
                image_embedding,
                nn.Linear(in_features=image_shape, out_features=text_shape)
            )
        )
        self.logit_scale = nn.Parameter(torch.ones([]) * np.log(1 / 0.07))

    def _forward_image(self, image: torch.Tensor) -> torch.Tensor:
        """
        Forward method image part CLIP
        :param image: input image
        :return: normalized image embedding
        """
        image_embedding = self.image_model(image)
        image_features = image_embedding / image_embedding.norm(
            dim=-1,
            keepdim=True
        )
        return image_features

    def _forward_text(self, text: torch.Tensor) -> torch.Tensor:
        """
        Forward method text part CLIP
        :param text: input text description
        :return: normalized text embedding
        """
        text_embedding = self.text_model(text)
        text_features = text_embedding / text_embedding.norm(
            dim=-1,
            keepdim=True
        )
        return text_features

    def forward(
            self,
            image: torch.Tensor,
            text: torch.Tensor
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Forward method CLIP
        :param image: input image
        :param text: input text description
        :return: image and text logits
        """
        image_features = self._forward_image(image)
        text_features = self._forward_text(text)

        logits_image, logits_text = self._cosine_similarity(
            image_features,
            text_features
        )
        return logits_image, logits_text, (image_features, text_features)

    @torch.no_grad()
    def inference(
            self,
            image: torch.Tensor,
            text: torch.Tensor,
            image_features: Optional[torch.Tensor] = None,
            text_features: Optional[torch.Tensor] = None,
            is_raw_output: Optional[bool] = False
    ) -> torch.Tensor:
        """
        Inference forward CLIP
        :param image: input image
        :param text: input text classes
        :param image_features: images embedding vectors
        :param text_features: text embedding vectors
        :param is_raw_output: is return also image and text embedding vectors
        :return: classes of input images
        """
        if image_features is None:
            image_features = self._forward_image(image)
        if text_features is None:
            text_features = self._forward_text(text)
        logits_image, _ = self._cosine_similarity(
            image_features, text_features
        )
        classes = torch.argmax(logits_image, dim=1)
        if is_raw_output:
            return classes, (image_features, text_features)
        return classes

    @property
    def device(self):
        return next(iter(self.parameters())).device

    def _cosine_similarity(
            self,
            image_features: torch.Tensor,
            text_features: torch.Tensor
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Function of cosine similarity of image and text vector embedding
        :param image_features: image embedding
        :param text_features: text embedding
        :return: tuple of image and text logits
        """
        logit_scale = self.logit_scale.exp()
        logits_image = logit_scale * image_features@text_features.t()
        logits_text = logits_image.t()
        return logits_image, logits_text


def configuration_image_model(
        name_model: str, *args, **kwargs
) -> Tuple[nn.Module, int]:
    """
    Function for init cnn model from torchvision.models
    :param name_model: name model from torchvision.models
    :param args: args for init model
    :param kwargs: kwargs for init model
    :return: cnn model and it's output vector dimension
    """
    if name_model in models.__dict__:
        try:
            # init model
            model = models.__dict__[name_model](*args, **kwargs)
            # change last layer and
            name_last_layer, last_layer = list(model.named_modules())[-1]
            output_shape = last_layer.in_features
            setattr(model, name_last_layer, nn.Identity())
            return model, output_shape
        except Exception as err:
            raise ValueError('Please type right image model name') from err
    else:
        raise ValueError('Please type right image model name')


class WrapperModelFromHuggingFace(nn.Module):
    """
    Class wrapper for models from hugging face
    """

    def __init__(self, hugging_face_model: nn.Module):
        """
        Method for init model
        :param hugging_face_model: torch model from hugging face
        """
        super().__init__()
        self.model = hugging_face_model

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward method of model
        :param x: input tensor
        :return: model logits
        """
        return self.model(x).pooler_output


def configuration_text_model(
        name_model: str, *args, **kwargs
) -> Tuple[nn.Module, int]:
    """
    Function for init transformer model from transformers (hugging face)
    :param name_model: name model from transformers
    :param args: args for init model
    :param kwargs: kwargs for init model
    :return: transformer and it's output vector dimension
    """
    name_text_models = transformers.__dict__['_class_to_module']
    if name_model in name_text_models:
        module = eval(f'transformers.{name_text_models[name_model]}')
        try:
            if kwargs['pretrained'] and 'name_pretrained' in kwargs:
                model = getattr(module, name_model).from_pretrained(
                    kwargs['name_pretrained']
                )
            else:
                model = getattr(module, name_model)(*args, **kwargs)
            # find last dimension
            for i in range(10):
                _, last_layer = list(model.named_modules())[-i]
                if hasattr(last_layer, 'in_features'):
                    output_shape = last_layer.in_features
                    break
            return WrapperModelFromHuggingFace(model), output_shape
        except Exception as err:
            raise ValueError('Please type right text model name') from err
    else:
        raise ValueError('Please type right text model name')
