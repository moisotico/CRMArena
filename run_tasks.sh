#!/bin/bash

AGENT_MODEL=gpt-4o-2024-08-06
# AGENT_MODEL=claude-3-5-sonnet-20240620
# AGENT_MODEL=llama3.1-405b-instruct

TASK_CATEGORY=top_issue_identification

# RESULT_DIR=results_natural_1002
RESULT_DIR=results_tc_natural_1002

# AGENT_STRATEGY=react
AGENT_STRATEGY=tool_call

# LITELLM_PROVIDER=together_ai
# LITELLM_PROVIDER=bedrock
LITELLM_PROVIDER=openai
# LITELLM_PROVIDER=vertex_ai

EVAL_MODE=aided
LOG_DIR=logs_natural_1002

mkdir -p $LOG_DIR

python run_tasks.py \
    --model $AGENT_MODEL \
    --task_category $TASK_CATEGORY \
    --agent_eval_mode $EVAL_MODE \
    --log_dir $RESULT_DIR \
    --agent_strategy $AGENT_STRATEGY \
    --llm_provider $LITELLM_PROVIDER > ${LOG_DIR}/run_${AGENT_MODEL}_${AGENT_STRATEGY}_${TASK_CATEGORY}_${EVAL_MODE}.log 2>&1 &

## MODELS
# claude-3-5-sonnet-20240620
# claude-3-opus-20240229
# gpt-4o-2024-08-06
# gpt-3.5-turbo-0125
# llama3.1-8b-instruct
# llama3.1-70b-instruct
# llama3.1-405b-instruct
# mixtral_8x22b_instruct


## TASKS
# policy_violation_identification
# monthly_trend_analysis
# top_issue_identification
# named_entity_disambiguation
# best_region_identification
# handle_time
# knowledge_qa
# transfer_count
# case_routing

## PROVIDER
# bedrock
# openai
# together_ai
# vertex_ai

## AGENT_STRATEGY
# act
# react
# tool_call
# tool_call_flex