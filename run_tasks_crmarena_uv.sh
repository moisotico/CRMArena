#!/bin/bash

# List of agent models to iterate over
AGENT_MODELS=(
    # "o1-2024-12-17"
    # "gpt-4o-2024-11-20"
    # "gpt-4o-mini-2024-07-18"
    "us.meta.llama3-2-3b-instruct-v1:0"  # Bedrock Llama model for testing
    # "claude-3-5-sonnet-20240620"    # Anthropic model for testing
    # "llama3.1-405b-instruct"
    # "llama3.1-70b-instruct"
    # "llama3.1-8b-instruct"
    # "llama4-maverick-17b-128e-instruct"
    # "gemini-2.5-pro-preview-03-25"
    # "gemini-2.5-flash-preview-04-17"
    # "gemini-2.0-flash-001"
)

TASKS=(
    # "policy_violation_identification"
    # "monthly_trend_analysis"
    # "named_entity_disambiguation"
    # "best_region_identification"
    # "handle_time"
    "knowledge_qa"
    # "transfer_count"
    # "case_routing"
    # "top_issue_identification"
)

STRATEGIES=(
    # "react"
    # "act"
    "tool_call"
)


EVAL_MODE=aided

ORG_TYPE=original
PRIVACY_AWARE_PROMPT=false

for AGENT_MODEL in "${AGENT_MODELS[@]}"; do
    for TASK_CATEGORY in "${TASKS[@]}"; do
        for AGENT_STRATEGY in "${STRATEGIES[@]}"; do

            if [[ "$AGENT_MODEL" == gpt* ]] || [[ "$AGENT_MODEL" == o1* ]]; then
                LITELLM_PROVIDER=openai
            elif [[ "$AGENT_MODEL" == claude* ]]; then
                LITELLM_PROVIDER=anthropic
            elif [[ "$AGENT_MODEL" == *meta* ]] || [[ "$AGENT_MODEL" == anthropic.* ]] || [[ "$AGENT_MODEL" == mistral.* ]]; then
                LITELLM_PROVIDER=bedrock
            elif [[ "$AGENT_MODEL" == llama4* ]]; then
                LITELLM_PROVIDER=together_ai
            else
                LITELLM_PROVIDER=vertex_ai
            fi            

            if [ "$INTERACTIVE" = true ]; then
                RESULT_DIR=results/${ORG_TYPE}_interactive/${AGENT_STRATEGY}_${LITELLM_PROVIDER}
                LOG_DIR=logs/${ORG_TYPE}_interactive/${AGENT_STRATEGY}_${LITELLM_PROVIDER}
            else
                RESULT_DIR=results/${ORG_TYPE}/${AGENT_STRATEGY}_${LITELLM_PROVIDER}
                LOG_DIR=logs/${ORG_TYPE}/${AGENT_STRATEGY}_${LITELLM_PROVIDER}
            fi

            if [ "$PRIVACY_AWARE_PROMPT" = true ]; then
                RESULT_DIR=${RESULT_DIR}_privacy_aware
                LOG_DIR=${LOG_DIR}_privacy_aware
            fi

            echo "LOG_DIR: $LOG_DIR"
            echo "RESULT_DIR: $RESULT_DIR"

            mkdir -p $LOG_DIR
            mkdir -p $RESULT_DIR

            echo "Running task: $TASK_CATEGORY with strategy: $AGENT_STRATEGY and model: $AGENT_MODEL and provider: $LITELLM_PROVIDER and privacy_aware_prompt: $PRIVACY_AWARE_PROMPT"

            # Construct log file name including the model
            LOG_FILE="${LOG_DIR}/run_${AGENT_MODEL}_${AGENT_STRATEGY}_${TASK_CATEGORY}_${EVAL_MODE}.log"

           
            uv run python -u run_tasks.py \
                --model "$AGENT_MODEL" \
                --task_category "$TASK_CATEGORY" \
                --agent_eval_mode "$EVAL_MODE" \
                --log_dir "$RESULT_DIR" \
                --agent_strategy "$AGENT_STRATEGY" \
                --llm_provider "$LITELLM_PROVIDER" \
                --reuse_results \
                --privacy_aware_prompt "$PRIVACY_AWARE_PROMPT" \
                --org_type "$ORG_TYPE" > "$LOG_FILE" 2>&1 &
                    
            
        done
    done
done
