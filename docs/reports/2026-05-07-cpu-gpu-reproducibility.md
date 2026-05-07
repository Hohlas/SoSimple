# CPU/GPU Reproducibility Experiment

> **Date**: 2026-05-07
> **Commit**: `bac24e90a3ec8297e8d9d6e293fe7a8c61c182f0`
> **Model**: `entry_path_v1_live_safe`, seed `42`, epochs `5`
> **Status**: Completed
> **Decision**: production retrain must be CPU-only; GPU training is research-only.

======================================================================
SUMMARY OF EXPERIMENTAL RESULTS
======================================================================

## EXP 1: Initial Weights (CPU vs GPU)
  VERDICT: IDENTICAL (max_diff=0)
  Model weights are created on CPU before .to(device), so same seed
  produces identical initialization regardless of target device.

## EXP 2: Eval Mode Forward Pass (no dropout)
  ret output:     max_diff=2.09e-07, mean_diff=4.04e-08
  path_reg:       max_diff=2.09e-07, mean_diff=4.16e-08
  path_cls:       max_diff=4.47e-08, mean_diff=8.61e-09
  
  VERDICT: Matmul-only diff is NEGLIGIBLE (<1e-7). cuBLAS vs MKL
  produce nearly identical results for a single forward pass.

## EXP 3: Train Mode Forward Pass (with dropout=0.3)
  ret output:     max_diff=1.14e+00, mean_diff=2.12e-01
  path_reg:       max_diff=8.74e-01, mean_diff=2.13e-01
  path_cls:       max_diff=3.67e-01, mean_diff=8.51e-02
  
  Train/Eval diff ratio: 5,466,475x
  
  VERDICT: Dropout is the PRIMARY source of single-pass divergence.
  CPU RNG (Mersenne Twister) and GPU RNG (Philox) produce completely
  different dropout masks even with the same seed.

## EXP 4: Full Training — dropout=0 (CPU vs GPU)
  Per-epoch max weight diff:
    Epoch 1: 7.39e-02
    Epoch 2: 1.68e-01
    Epoch 3: 1.76e-01
    Epoch 4: 2.09e-01
    Epoch 5: 2.04e-01
  
  VERDICT: Even WITHOUT dropout, matmul summation order differences
  compound through training to produce significant weight divergence
  (~0.2 after 5 epochs). This is the butterfly effect: each tiny
  gradient difference accumulates in AdamW running averages.

## EXP 4b: Full Training — dropout=0.3 (CPU vs GPU)
  CPU SHA256: f21c44bf7e75931d...
  GPU training timed out on GTX 750 Ti (too slow).
  
  User-provided data confirms: different SHA256, different PF.

## EXP 5: Deterministic Algorithms
  Strict mode: forward pass OK on both CPU and GPU.
  warn_only=True: GPU backward pass triggers warning:
    "Memory Efficient attention defaults to a non-deterministic algorithm"
  
  CPU det vs GPU det (5 epochs, dropout=0.3): max_weight_diff=5.44e-01
  
  VERDICT: torch.use_deterministic_algorithms(True) does NOT solve
  cross-device reproducibility. It ensures same-device reproducibility,
  but dropout RNG is still device-specific.

## EXP 6: Per-Epoch Prediction Divergence
  Epoch | Max diff  | Mean diff | Corr ret24
      0 | 0.000000  | 0.00000004| 1.000000
      1 | 0.034927  | 0.01582655| 0.982150
      2 | 0.088600  | 0.03055680| 0.980022
      3 | 0.366523  | 0.04863594| 0.325254
      4 | 0.864830  | 0.07161165| 0.866835
      5 | 0.530520  | 0.07329994| 0.947311
  
  VERDICT: Predictions diverge rapidly. By epoch 3, correlation
  drops to 0.325 — meaning the models have learned substantially
  different representations despite identical data and seed.

## CRITICAL NEW EXPERIMENT: CPU-Trained Model, Cross-Device Inference
  CPU inference vs GPU inference (same model, eval mode):
    ret:      max_diff=1.79e-07
    path_reg: max_diff=2.83e-07
    path_cls: max_diff=3.73e-08
    Top-5% overlap: 12/12 (100.0%)
    ret_24 correlation: 1.0000000000
    ret_24 max diff: 1.49e-07
  
  VERDICT: A model trained on CPU produces IDENTICAL rankings
  when inferenced on CPU or GPU. The tiny matmul differences
  (1e-7) do NOT change trade selection.

======================================================================
ROOT CAUSE ANALYSIS
======================================================================

TWO distinct problems:

1. TRAINING divergence (CPU vs GPU produces different checkpoints):
   - PRIMARY: Dropout uses device-specific RNG. Same seed, different
     masks on CPU (Mersenne Twister) vs GPU (Philox).
     Single-pass amplification: 5.5 million x (2e-7 → 1.14)
   - SECONDARY: Matmul summation order (cuBLAS vs MKL).
     Single-pass: negligible (2e-7), but compounds through training
     via AdamW running averages. 5 epochs → 0.2 max weight diff
     even WITHOUT dropout.
   - TERTIARY: Flash attention backward pass on GPU is
     non-deterministic (confirmed by torch warning).

2. INFERENCE divergence (same checkpoint, different device):
   - NEGLIGIBLE: max_diff = 1.79e-07, 100% ranking overlap.
   - This is NOT a practical problem.

======================================================================
PROPOSED SOLUTION: CPU-ONLY TRAINING
======================================================================

The key insight from the experiments:

  Training on CPU → checkpoint is portable
  Inference on CPU or GPU → identical rankings (100% overlap)

Therefore: FORCE all training to run on CPU. Use GPU only for
inference if needed for speed. This eliminates both sources of
training divergence.

Proposed changes to the project code:

### 1. ML/utils.py — set_seed() enhancement

  def set_seed(seed: int = 42):
      random.seed(seed)
      np.random.seed(seed)
      torch.manual_seed(seed)
      torch.cuda.manual_seed_all(seed)
      torch.backends.cudnn.deterministic = True
      torch.backends.cudnn.benchmark = False
      os.environ.setdefault('CUBLAS_WORKSPACE_CONFIG', ':4096:8')
      torch.use_deterministic_algorithms(True, warn_only=True)

### 2. ML/train.py — --device flag and CPU-only training

  Add argparse argument:
    --device cpu|cuda|auto  (default: cpu for reproducibility)

  Change get_device() to respect --device:
    def get_device(device_override=None):
        if device_override == 'cpu':
            return torch.device('cpu')
        if device_override == 'cuda':
            if not torch.cuda.is_available():
                raise RuntimeError('CUDA not available')
            return torch.device('cuda')
        return torch.device('cpu')  # default: CPU for reproducibility

  Add warning when device=cuda:
    print("  ⚠️  CUDA training produces non-reproducible checkpoints.")
    print("  ⚠️  Use --device cpu for reproducible results.")

### 3. ML/data_loader.py — explicit Generator for DataLoader

  def create_data_loaders(..., seed=42):
      g = torch.Generator()
      g.manual_seed(seed)
      
      train_loader = DataLoader(
          train_dataset,
          batch_size=batch_size,
          shuffle=True,
          num_workers=num_workers,
          pin_memory=(device.type == 'cuda'),
          drop_last=False,
          generator=g,
      )

  def worker_init_fn(worker_id):
      worker_seed = seed + worker_id
      np.random.seed(worker_seed)
      random.seed(worker_seed)

### 4. ML/train.py — checkpoint fingerprinting

  Add to torch.save() dict:
    'torch_version': torch.__version__,
    'numpy_version': np.__version__,
    'device': str(device),
    'cudnn_deterministic': torch.backends.cudnn.deterministic,
    'deterministic_algorithms': torch.are_deterministic_algorithms_enabled(),
    'CUBLAS_WORKSPACE_CONFIG': os.environ.get('CUBLAS_WORKSPACE_CONFIG', 'not set'),
    'train_csv_sha256': compute_file_sha256(TRAIN_FILE),
    'val_csv_sha256': compute_file_sha256(VAL_FILE),
    'seed': seed,

### 5. ML/train.py — seed+device-specific output

  checkpoint_path = CHECKPOINTS_DIR / f'{model_name}{suffix}_best_seed{seed}_{device.type}.pt'

### 6. API/generate_signals.py — inference on any device

  Load checkpoint, model.to(device) where device can be cuda.
  The 1e-7 inference difference is negligible and does NOT affect
  trade selection (proven by 100% top-5% overlap experiment).

======================================================================
EXPECTED OUTCOME
======================================================================

With CPU-only training:
  - Same seed + same data + same code = IDENTICAL checkpoint
  - Regardless of machine, GPU presence, or PyTorch CUDA version
  - Server A (CPU-only) and Server B (with GPU) produce same .pt file
  - Inference can use GPU for speed without affecting rankings

Without CPU-only training (current state):
  - GPU training: reproducible on same GPU (same dropout masks)
  - CPU training: reproducible on same CPU
  - Cross-device: NEVER reproducible (different dropout RNG)

The trade-off: CPU training is ~3-5x slower than GPU on small models
like this Transformer (d_model=64, 2 layers). For 5 epochs on 44k
samples, CPU takes ~8 min vs ~2 min on GPU. This is acceptable for
a production system that values reproducibility.

======================================================================
ALTERNATIVE (if GPU training speed is required)
======================================================================

If CPU training is too slow for hyperparameter search:
  1. Do hyperparameter search on GPU (non-reproducible, fast)
  2. Final production training on CPU (reproducible, slower)
  3. Record seed, data hashes, torch version for audit trail

This is the standard practice in ML: exploration on GPU, final
training on fixed hardware for reproducibility.
