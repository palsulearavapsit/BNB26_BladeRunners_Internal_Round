import torch.nn as nn

from models.univfd.clip import clip
from univfd.clip_models import CHANNELS, CLIPModel


def test_univfd_clip_model_architecture(monkeypatch):
    assert "ViT-L/14" in clip.available_models()
    assert CHANNELS["ViT-L/14"] == 768

    monkeypatch.setattr(
        clip,
        "load",
        lambda name, device: (nn.Identity(), object()),
    )

    model = CLIPModel("ViT-L/14")

    assert model.fc.in_features == 768
    assert model.fc.out_features == 1
