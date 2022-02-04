"""
Module with CLIP model. It contains separated vision part of CLIP.
Vision part is separated, because only it will be trained in this library.
"""

from typing import Optional, Tuple

import torch
import numpy as np

from torch import nn
from torch.nn.functional import normalize


class VisionPartCLIP(nn.Module):
    """
    Vision part of clip with scale logit
    """
    def __init__(self, vision_model: nn.Module) -> None:
        """
        Method for init vision part CLIP

        Args:
            vision_model: CNN model for getting image embedding
        """
        super().__init__()
        self.vision_model: nn.Module = vision_model
        self.logit_scale: nn.Parameter = nn.Parameter(
            torch.ones([]) * np.log(1 / 0.07)
        )

    def forward(
            self,
            image: torch.Tensor,
            text_embedding: torch.Tensor,
            image_features: Optional[torch.Tensor] = None,
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        Forward method of vision part with computing image and text embedding
        cosine similarity

        Args:
            image: input image
            text_embedding: normalized text embedding
            image_features: vector representation of image from vision model

        Returns:
            image and text logits, image embedding
        """
        if image_features is None:
            image_features = self.vision_model(image)
        image_embedding = normalize(image_features)
        logit_scale = self.logit_scale.exp()
        image_logit = logit_scale * image_embedding@text_embedding.t()
        text_logit = image_logit.t()
        return image_logit, text_logit, image_embedding

    @property
    def device(self) -> torch.device:
        """
        Method for know device on which the model is located.

        Returns:
            model device
        """
        return next(iter(self.parameters())).device


class CLIP(nn.Module):
    """
    CLIP model with 2 parts:
    image part and text part
    """
    def __init__(
            self,
            vision_part: VisionPartCLIP,
            text_model: nn.Module,
    ) -> None:
        """
        Method for init CLIP

        Args:
            vision_part: vision part of clip
            text_model: Transform for embedding text
        """
        super().__init__()
        self.vision_part = vision_part
        self.text_model = text_model

    def forward(
            self,
            image: torch.Tensor,
            text: torch.Tensor,
            image_features: Optional[torch.Tensor] = None,
            text_features: Optional[torch.Tensor] = None,
    ) -> Tuple[torch.Tensor, torch.Tensor, Tuple[torch.Tensor, torch.Tensor]]:
        """
        Forward method CLIP

        Args:
            image: input image
            text: text description
            image_features: vector representation of image from vision model
            text_features: vector representation of text from text model

        Returns:
            image and text logits, (image and text embeddings)
        """
        if text_features is None:
            text_features = self.text_model(text)
        text_embedding = normalize(text_features)
        image_logit, text_logit, image_embedding = self.vision_part(
            image=image,
            text_embedding=text_embedding,
            image_features=image_features,
        )
        return image_logit, text_logit, (image_embedding, text_embedding)

    @torch.no_grad()
    def inference(
            self,
            image: torch.Tensor,
            text: torch.Tensor,
            image_features: Optional[torch.Tensor] = None,
            text_features: Optional[torch.Tensor] = None,
    ) -> Tuple[torch.Tensor, Tuple[torch.Tensor, torch.Tensor]]:
        """
        Inference forward CLIP

        Args:
            image: input image
            text: input text classes
            image_features: images embedding vectors
            text_features: text embedding vectors

        Returns:
            classes of input images
        """
        image_logit, _, (image_embedding, text_embedding) = (
            self.forward(image, text, image_features, text_features)
        )
        classes = torch.argmax(image_logit, dim=1)
        return classes, (image_embedding, text_embedding)

    @property
    def device(self) -> torch.device:
        """
        Method for know device on which the model is located.

        Returns:
            model device
        """
        return next(iter(self.parameters())).device
