#!/usr/bin/env bash

# OPD baseline aligned to the EOPD paper's control setting:
# - student on-policy rollouts
# - teacher token distribution on student prefixes
# - reverse-KL objective
#
# Paper target:
#   student=Qwen3-1.7B-Base
#   teacher=Qwen3-8B (non-thinking mode)
#   train_data=MATH
#   lr=3e-6, cosine, AdamW
#   batch=128, mini-batch=32, epochs=3
#   temp=1.0, top-p=1.0, max_response_length=4096
#
# ms-swift mapping:
#   OPD            -> --rlhf_type gkd --lmbda 1.0 --beta 1.0 --seq_kd false
#   non-thinking   -> --template qwen3 --enable_thinking false
#   empty <think>  -> --add_non_thinking_prefix true
#
# Dataset note:
#   The repo already registers `AI-ModelScope/math-trn-format` as a math training set in
#   `swift/dataset/dataset/llm.py`. It is the closest built-in training entry to the paper's MATH setup.
#   If you want a larger math-only alternative, override TRAIN_DATASET with `TIGER-Lab/MATH-plus:train`.
#
# Default runtime target:
#   8 x A100
#
# Paper batch mapping:
#   With 8 GPUs, per_device_train_batch_size=4 and gradient_accumulation_steps=4 gives:
#     mini-batch   = 8 * 4  = 32
#     global batch = 32 * 4 = 128

set -euo pipefail

NPROC_PER_NODE="${NPROC_PER_NODE:-8}"
CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0,1,2,3,4,5,6,7}"

STUDENT_MODEL="${STUDENT_MODEL:-Qwen/Qwen3-1.7B-Base}"
TEACHER_MODEL="${TEACHER_MODEL:-Qwen/Qwen3-8B}"
TRAIN_DATASET="${TRAIN_DATASET:-AI-ModelScope/math-trn-format}"
OUTPUT_DIR="${OUTPUT_DIR:-output/opd_baseline/qwen3_1_7b_math}"

PER_DEVICE_TRAIN_BATCH_SIZE="${PER_DEVICE_TRAIN_BATCH_SIZE:-}"
GRADIENT_ACCUMULATION_STEPS="${GRADIENT_ACCUMULATION_STEPS:-4}"

NUM_TRAIN_EPOCHS="${NUM_TRAIN_EPOCHS:-3}"
LEARNING_RATE="${LEARNING_RATE:-3e-6}"
MAX_LENGTH="${MAX_LENGTH:-4096}"
MAX_COMPLETION_LENGTH="${MAX_COMPLETION_LENGTH:-4096}"

SEED="${SEED:-42}"
WEIGHT_DECAY="${WEIGHT_DECAY:-0.0}"
MAX_GRAD_NORM="${MAX_GRAD_NORM:-1.0}"

DEEPSPEED_STAGE="${DEEPSPEED_STAGE:-zero2}"
TEACHER_DEEPSPEED_STAGE="${TEACHER_DEEPSPEED_STAGE:-zero3_offload}"
OFFLOAD_TEACHER_MODEL="${OFFLOAD_TEACHER_MODEL:-false}"

USE_VLLM="${USE_VLLM:-true}"
VLLM_MODE="${VLLM_MODE:-colocate}"
VLLM_GPU_MEMORY_UTILIZATION="${VLLM_GPU_MEMORY_UTILIZATION:-0.30}"
VLLM_TENSOR_PARALLEL_SIZE="${VLLM_TENSOR_PARALLEL_SIZE:-1}"
VLLM_MAX_MODEL_LEN="${VLLM_MAX_MODEL_LEN:-10240}"
SLEEP_LEVEL="${SLEEP_LEVEL:-1}"

ATTN_IMPL="${ATTN_IMPL:-flash_attn}"
LOGGING_STEPS="${LOGGING_STEPS:-1}"
SAVE_STEPS="${SAVE_STEPS:-100}"
SAVE_TOTAL_LIMIT="${SAVE_TOTAL_LIMIT:-3}"
DATALOADER_NUM_WORKERS="${DATALOADER_NUM_WORKERS:-8}"
DATASET_NUM_PROC="${DATASET_NUM_PROC:-8}"

# In-training evaluation:
# - Supported by ms-swift via EvalScope hooks.
# - Default to a light math checkpoint-selection setting on AIME-2025.
# - Use the standalone eval script for final full-benchmark numbers.
EVAL_DURING_TRAIN="${EVAL_DURING_TRAIN:-true}"
EVAL_STRATEGY="${EVAL_STRATEGY:-steps}"
EVAL_STEPS="${EVAL_STEPS:-100}"
PER_DEVICE_EVAL_BATCH_SIZE="${PER_DEVICE_EVAL_BATCH_SIZE:-1}"
EVAL_DATASETS="${EVAL_DATASETS:-aime25}"
EVAL_LIMIT="${EVAL_LIMIT:-}"
EVAL_GENERATION_CONFIG="${EVAL_GENERATION_CONFIG:-{\"max_tokens\":8192,\"temperature\":0.0,\"do_sample\":false}}"

if [[ -z "${PER_DEVICE_TRAIN_BATCH_SIZE}" ]]; then
    if (( 32 % NPROC_PER_NODE == 0 )); then
        PER_DEVICE_TRAIN_BATCH_SIZE="$((32 / NPROC_PER_NODE))"
    else
        PER_DEVICE_TRAIN_BATCH_SIZE=4
        echo "Warning: NPROC_PER_NODE=${NPROC_PER_NODE} cannot exactly preserve paper mini-batch=32." >&2
        echo "Falling back to PER_DEVICE_TRAIN_BATCH_SIZE=${PER_DEVICE_TRAIN_BATCH_SIZE}." >&2
    fi
fi

MINI_BATCH_SIZE="$((NPROC_PER_NODE * PER_DEVICE_TRAIN_BATCH_SIZE))"
GLOBAL_BATCH_SIZE="$((MINI_BATCH_SIZE * GRADIENT_ACCUMULATION_STEPS))"
read -r -a EVAL_DATASET_ARR <<< "${EVAL_DATASETS}"

echo "Student model: ${STUDENT_MODEL}"
echo "Teacher model: ${TEACHER_MODEL}"
echo "Train dataset: ${TRAIN_DATASET}"
echo "Mini-batch size (paper target 32): ${MINI_BATCH_SIZE}"
echo "Global batch size (paper target 128): ${GLOBAL_BATCH_SIZE}"
if [[ "${EVAL_DURING_TRAIN}" == "true" ]]; then
    echo "In-train eval: enabled"
    echo "Eval datasets: ${EVAL_DATASETS}"
    echo "Eval every ${EVAL_STEPS} step(s)"
else
    echo "In-train eval: disabled"
fi

if [[ "${MINI_BATCH_SIZE}" -ne 32 || "${GLOBAL_BATCH_SIZE}" -ne 128 ]]; then
    echo "Warning: current batch mapping differs from the paper target (mini-batch=32, global batch=128)." >&2
fi

TRAIN_CMD=(
    swift
    rlhf
    --rlhf_type gkd
    --model "${STUDENT_MODEL}"
    --teacher_model "${TEACHER_MODEL}"
    --tuner_type full
    --dataset "${TRAIN_DATASET}"
    --load_from_cache_file true
    --split_dataset_ratio 0
    --template qwen3
    --enable_thinking false
    --add_non_thinking_prefix true
    --seq_kd false
    --lmbda 1.0
    --beta 1.0
    --temperature 1.0
    --top_p 1.0
    --torch_dtype bfloat16
    --num_train_epochs "${NUM_TRAIN_EPOCHS}"
    --per_device_train_batch_size "${PER_DEVICE_TRAIN_BATCH_SIZE}"
    --gradient_accumulation_steps "${GRADIENT_ACCUMULATION_STEPS}"
    --learning_rate "${LEARNING_RATE}"
    --lr_scheduler_type cosine
    --warmup_ratio 0.0
    --weight_decay "${WEIGHT_DECAY}"
    --adam_beta1 0.9
    --adam_beta2 0.999
    --max_grad_norm "${MAX_GRAD_NORM}"
    --max_length "${MAX_LENGTH}"
    --max_completion_length "${MAX_COMPLETION_LENGTH}"
    --seed "${SEED}"
    --save_steps "${SAVE_STEPS}"
    --save_total_limit "${SAVE_TOTAL_LIMIT}"
    --logging_steps "${LOGGING_STEPS}"
    --save_only_model true
    --gradient_checkpointing true
    --dataloader_num_workers "${DATALOADER_NUM_WORKERS}"
    --dataset_num_proc "${DATASET_NUM_PROC}"
    --deepspeed "${DEEPSPEED_STAGE}"
    --teacher_deepspeed "${TEACHER_DEEPSPEED_STAGE}"
    --offload_teacher_model "${OFFLOAD_TEACHER_MODEL}"
    --use_vllm "${USE_VLLM}"
    --vllm_mode "${VLLM_MODE}"
    --vllm_gpu_memory_utilization "${VLLM_GPU_MEMORY_UTILIZATION}"
    --vllm_tensor_parallel_size "${VLLM_TENSOR_PARALLEL_SIZE}"
    --vllm_max_model_len "${VLLM_MAX_MODEL_LEN}"
    --sleep_level "${SLEEP_LEVEL}"
    --attn_impl "${ATTN_IMPL}"
    --log_completions true
    --report_to tensorboard
    --output_dir "${OUTPUT_DIR}"
)

if [[ "${EVAL_DURING_TRAIN}" == "true" ]]; then
    TRAIN_CMD+=(
        --eval_strategy "${EVAL_STRATEGY}"
        --eval_steps "${EVAL_STEPS}"
        --per_device_eval_batch_size "${PER_DEVICE_EVAL_BATCH_SIZE}"
        --eval_use_evalscope
        --eval_backend Native
        --eval_dataset "${EVAL_DATASET_ARR[@]}"
        --eval_generation_config "${EVAL_GENERATION_CONFIG}"
    )
    if [[ -n "${EVAL_LIMIT}" ]]; then
        TRAIN_CMD+=(
            --eval_limit "${EVAL_LIMIT}"
        )
    fi
fi

PYTORCH_CUDA_ALLOC_CONF='expandable_segments:True' \
NPROC_PER_NODE="${NPROC_PER_NODE}" \
CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES}" \
"${TRAIN_CMD[@]}"
