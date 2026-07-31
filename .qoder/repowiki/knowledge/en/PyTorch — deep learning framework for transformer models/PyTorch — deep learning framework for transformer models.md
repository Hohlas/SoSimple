---
kind: external_dependency
name: PyTorch — deep learning framework for transformer models
slug: pytorch
category: external_dependency
category_hints:
    - vendor_identity
    - sdk_real_api
scope:
    - '**'
---

### PyTorch
- Role: backbone for all neural architectures (Transformer, BiLSTM, CNN1D, Hybrid, entry_path, take_skip) trained via `ML/train.py` and stored as `.pt` checkpoints in `ML/checkpoints/`.
- Installation uses CUDA 12.1 wheels from `https://download.pytorch.org/whl/cu121` (extra-index-url in `requirements.txt`).
- Stable usage: models are saved/restored via standard `torch.save`/`torch.load`; checkpoint path is part of the frozen rule contract and must not change between validation and locked_test.
- The triple_barrier track requires transfer learning from an existing encoder checkpoint (`--encoder_ckpt`) to avoid encoder collapse.
- Verify exact model class names, checkpoint schemas, and GPU/CPU device handling against the PyTorch API.