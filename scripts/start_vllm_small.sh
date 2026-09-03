#!/usr/bin/env bash
# Real vLLM on Linux/WSL with a pinned local Qwen snapshot; no API emulation.
set -euo pipefail

repo_dir="$(cd -- "$(dirname -- "$0")/.." && pwd)"
vllm_bin="${LAB28_VLLM_BIN:-$HOME/.cache/lab28-vllm/bin/vllm}"
model_dir="$repo_dir/.lab28/vllm-model"

if [[ ! -x "$vllm_bin" || ! -f "$model_dir/model.safetensors" ]]; then
    echo "Install vLLM and download the pinned model first; see submission/vllm-local.md." >&2
    exit 1
fi

export VLLM_NO_USAGE_STATS=1
# WSL on this laptop does not expose CUDA Unified Virtual Addressing. The
# supported vLLM V1 runner works without the V2 runner's UVA staging buffers.
export VLLM_USE_V2_MODEL_RUNNER=0
export VLLM_USE_FLASHINFER_SAMPLER=0
export HF_HUB_OFFLINE=1
export OMP_NUM_THREADS=2
printf '%s\n' "$$" > "$repo_dir/.lab28/vllm.pid"

exec "$vllm_bin" serve "$model_dir" \
    --served-model-name Qwen/Qwen2.5-0.5B-Instruct \
    --host 0.0.0.0 --port "${LAB28_VLLM_PORT:-8001}" \
    --dtype half --enforce-eager \
    --max-model-len 2048 --max-num-seqs 1 --max-num-batched-tokens 512 \
    --gpu-memory-utilization "${LAB28_VLLM_GPU_MEMORY_UTILIZATION:-0.65}"
