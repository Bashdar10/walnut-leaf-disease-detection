"""Model loading and prediction utilities for Walnut Leaf Disease Detection."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, Tuple

import torch
import torch.nn as nn

from config import CLASS_NAMES


BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "models" / "swin_cbam_224.pth"


class ChannelAttention(nn.Module):
    def __init__(self, in_planes: int, ratio: int = 16):
        super().__init__()
        hidden = max(in_planes // ratio, 1)

        self.avg_pool = nn.AdaptiveAvgPool2d(1)
        self.max_pool = nn.AdaptiveMaxPool2d(1)

        self.fc = nn.Sequential(
            nn.Conv2d(in_planes, hidden, 1, bias=False),
            nn.ReLU(inplace=True),
            nn.Conv2d(hidden, in_planes, 1, bias=False),
        )

        self.sigmoid = nn.Sigmoid()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        avg_out = self.fc(self.avg_pool(x))
        max_out = self.fc(self.max_pool(x))
        return self.sigmoid(avg_out + max_out)


class SpatialAttention(nn.Module):
    def __init__(self, kernel_size: int = 7):
        super().__init__()
        padding = kernel_size // 2
        self.conv = nn.Conv2d(2, 1, kernel_size, padding=padding, bias=False)
        self.sigmoid = nn.Sigmoid()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        avg_out = torch.mean(x, dim=1, keepdim=True)
        max_out, _ = torch.max(x, dim=1, keepdim=True)
        x = torch.cat([avg_out, max_out], dim=1)
        return self.sigmoid(self.conv(x))


class CBAM(nn.Module):
    def __init__(self, in_planes: int, ratio: int = 16, kernel_size: int = 7):
        super().__init__()
        self.channel_att = ChannelAttention(in_planes, ratio)
        self.spatial_att = SpatialAttention(kernel_size)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = x * self.channel_att(x)
        x = x * self.spatial_att(x)
        return x


class SwinCBAM(nn.Module):
    def __init__(self, num_classes: int):
        super().__init__()

        try:
            import timm
        except ImportError as exc:
            raise ImportError(
                "timm is not installed. Run: pip install timm"
            ) from exc

        self.backbone = timm.create_model(
            "swin_base_patch4_window7_224",
            pretrained=False,
            num_classes=0,
        )

        self.cbam = CBAM(in_planes=1024, ratio=16, kernel_size=7)
        self.head = nn.Linear(1024, num_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.backbone.forward_features(x)

        # Swin output usually: [B, H, W, C]
        # CBAM needs: [B, C, H, W]
        if x.ndim == 4 and x.shape[-1] == 1024:
            x = x.permute(0, 3, 1, 2).contiguous()

        if x.ndim == 2:
            x = x[:, :, None, None]

        x = self.cbam(x)
        x = torch.mean(x, dim=(2, 3))
        x = self.head(x)
        return x


def clean_state_dict(state_dict: Dict[str, torch.Tensor]) -> Dict[str, torch.Tensor]:
    cleaned = {}

    for key, value in state_dict.items():
        new_key = key

        if new_key.startswith("module."):
            new_key = new_key.replace("module.", "", 1)

        cleaned[new_key] = value

    return cleaned


class ModelManager:
    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = None
        self.available = False
        self.error_message = None

        self._load()

    def _load(self):
        try:
            if not MODEL_PATH.exists():
                raise FileNotFoundError(
                    f"Model file not found at: {MODEL_PATH}"
                )

            model = SwinCBAM(num_classes=len(CLASS_NAMES))

            checkpoint = torch.load(
                MODEL_PATH,
                map_location=self.device,
            )

            if isinstance(checkpoint, dict):
                if "state_dict" in checkpoint:
                    checkpoint = checkpoint["state_dict"]
                elif "model_state_dict" in checkpoint:
                    checkpoint = checkpoint["model_state_dict"]
                elif "model" in checkpoint:
                    checkpoint = checkpoint["model"]

            checkpoint = clean_state_dict(checkpoint)

            model.load_state_dict(checkpoint, strict=True)
            model.to(self.device)
            model.eval()

            self.model = model
            self.available = True
            self.error_message = None

            print("MODEL LOADED SUCCESSFULLY")
            print("MODEL PATH:", MODEL_PATH)
            print("DEVICE:", self.device)

        except Exception as exc:
            self.model = None
            self.available = False
            self.error_message = str(exc)

            print("MODEL LOAD ERROR:")
            print(self.error_message)

    @torch.inference_mode()
    def predict(self, image_tensor: torch.Tensor) -> Tuple[str, float]:
        if self.model is None:
            raise RuntimeError(
                self.error_message or "Model is not loaded."
            )

        image_tensor = image_tensor.to(self.device)

        outputs = self.model(image_tensor)
        probabilities = torch.softmax(outputs, dim=1)[0]

        confidence_value, predicted_index = torch.max(probabilities, dim=0)

        predicted_index = int(predicted_index.item())
        confidence = float(confidence_value.item() * 100)

        predicted_class = CLASS_NAMES[predicted_index]

        return predicted_class, round(confidence, 2)


def load_model() -> ModelManager:
    return ModelManager()