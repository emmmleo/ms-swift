#!/usr/bin/env bash

# Standalone evaluation for the Qwen3 math OPD baseline.
#
# Default targets:
# - AIME-2025
# - MATH-500
#
# This is intended for final checkpoint comparison after training.

set -euo pipefail

CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0,1}"

MODEL_PATH="${MODEL_PATH:-output/opd_baseline/qwen3_1_7b_math/checkpoint-100}"
EVAL_OUTPUT_DIR="${EVAL_OUTPUT_DIR:-eval_output/opd_baseline/qwen3_1_7b_math}"
EVAL_DATASETS="${EVAL_DATASETS:-aime25 math_500}"
EVAL_BACKEND="${EVAL_BACKEND:-Native}"
INFER_BACKEND="${INFER_BACKEND:-vllm}"
EVAL_NUM_PROC="${EVAL_NUM_PROC:-8}"
EVAL_LIMIT="${EVAL_LIMIT:-}"

VLLM_TENSOR_PARALLEL_SIZE="${VLLM_TENSOR_PARALLEL_SIZE:-2}"
VLLM_GPU_MEMORY_UTILIZATION="${VLLM_GPU_MEMORY_UTILIZATION:-0.90}"
VLLM_MAX_MODEL_LEN="${VLLM_MAX_MODEL_LEN:-10000}"
EVAL_GENERATION_CONFIG="${EVAL_GENERATION_CONFIG:-{\"max_tokens\":8192,\"temperature\":0.0,\"do_sample\":false}}"

read -r -a EVAL_DATASET_ARR <<< "${EVAL_DATASETS}"

echo "Model path: ${MODEL_PATH}"
echo "Eval datasets: ${EVAL_DATASETS}"
echo "Infer backend: ${INFER_BACKEND}"

EVAL_CMD=(
    swift
    eval
    --model "${MODEL_PATH}"
    --template qwen3
    --enable_thinking false
    --eval_dataset "${EVAL_DATASET_ARR[@]}"
    --eval_backend "${EVAL_BACKEND}"
    --infer_backend "${INFER_BACKEND}"
    --eval_generation_config "${EVAL_GENERATION_CONFIG}"
    --eval_num_proc "${EVAL_NUM_PROC}"
    --eval_output_dir "${EVAL_OUTPUT_DIR}"
)

if [[ "${INFER_BACKEND}" == "vllm" ]]; then
    EVAL_CMD+=(
        --vllm_tensor_parallel_size "${VLLM_TENSOR_PARALLEL_SIZE}"
        --vllm_gpu_memory_utilization "${VLLM_GPU_MEMORY_UTILIZATION}"
        --vllm_max_model_len "${VLLM_MAX_MODEL_LEN}"
    )
fi

if [[ -n "${EVAL_LIMIT}" ]]; then
    EVAL_CMD+=(
        --eval_limit "${EVAL_LIMIT}"
    )
fi

CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES}" "${EVAL_CMD[@]}"
