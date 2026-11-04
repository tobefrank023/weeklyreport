# Source this file from a checkout under your persistent task storage.
export PUBLIC_FIN_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
export TMPDIR="$PUBLIC_FIN_ROOT/tmp" TMP="$PUBLIC_FIN_ROOT/tmp" TEMP="$PUBLIC_FIN_ROOT/tmp"
export XDG_CACHE_HOME="$PUBLIC_FIN_ROOT/cache" UV_CACHE_DIR="$PUBLIC_FIN_ROOT/cache/uv" PIP_CACHE_DIR="$PUBLIC_FIN_ROOT/cache/pip"
export HF_HOME="$PUBLIC_FIN_ROOT/cache/hf" TORCH_HOME="$PUBLIC_FIN_ROOT/cache/torch" CUDA_CACHE_PATH="$PUBLIC_FIN_ROOT/cache/cuda"
export TRITON_CACHE_DIR="$PUBLIC_FIN_ROOT/cache/triton" TORCHINDUCTOR_CACHE_DIR="$PUBLIC_FIN_ROOT/cache/torchinductor" TORCH_EXTENSIONS_DIR="$PUBLIC_FIN_ROOT/cache/torch_extensions"
export PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$PUBLIC_FIN_ROOT/vendor${PYTHONPATH:+:$PYTHONPATH}"
