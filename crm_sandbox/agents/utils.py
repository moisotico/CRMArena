import re
import string
from collections import Counter
from sacrebleu.metrics import BLEU
from rouge import Rouge

## MODEL MAP ##
BEDROCK_MODELS_MAP = {
    # AWS Bedrock (all in us-west-2)
    "meta.llama3-1-8b-instruct-v1:0": {
        "provider": "bedrock",
        "name": "meta.llama3-1-8b-instruct-v1:0",
        "region": "us-west-2",
    },
    "us.meta.llama3-2-1b-instruct-v1:0": {
        "provider": "bedrock",
        "name": "us.meta.llama3-2-1b-instruct-v1:0",
        "region": "us-west-2",
    },
    "us.meta.llama3-2-3b-instruct-v1:0": {
        "provider": "bedrock",
        "name": "us.meta.llama3-2-3b-instruct-v1:0",
        "region": "us-west-2",
    },
    "us.meta.llama3-3-70b-instruct-v1:0": {
        "provider": "bedrock",
        "name": "us.meta.llama3-3-70b-instruct-v1:0",
        "region": "us-west-2",
    },
    "us.meta.llama4-maverick-17b-instruct-v1:0": {
        "provider": "bedrock",
        "name": "us.meta.llama4-maverick-17b-instruct-v1:0",
        "region": "us-west-2",
    },
    # OpenAI GPT-OSS models via Bedrock
    "gpt-oss-20b": {
        "provider": "bedrock",
        "name": "openai.gpt-oss-20b-1:0",
        "region": "us-west-2",
    },
    "gpt-oss-120b": {
        "provider": "bedrock", 
        "name": "openai.gpt-oss-120b-1:0",
        "region": "us-west-2",
    },
}

TOGETHER_MODELS_MAP = {
    "llama3.1-405b-instruct" : {
        "name": "together_ai/meta-llama/Meta-Llama-3.1-405B-Instruct-Turbo",
    },
    "mixtral_8x22b_instruct" : {
        "name": "together_ai/mistralai/Mixtral-8x22B-Instruct-v0.1"
    },
    "llama3.1-8b-instruct" : {
        "name": "together_ai/meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo"
    },
    "llama3.1-70b-instruct" : {
        "name": "together_ai/meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo"
    },
    "llama4-maverick-17b-128e-instruct" : {
        "name": "together_ai/meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8"
    },
    "deepseek-r1" : {
        "name": "together_ai/deepseek-ai/DeepSeek-R1"
    }
}

VERTEX_MODELS_MAP = {
  "llama3.1-405b-instruct": {
    "name": "vertex_ai/meta/llama3-405b-instruct-maas"
  },
  "llama3.1-70b-instruct" : {
        "name": "vertex_ai/meta/llama3-70b-instruct-maas"
    },
  "llama3.1-8b-instruct" : {
        "name": "vertex_ai/meta/llama3-8b-instruct-maas"
    },
  "llama4-maverick-17b-128e-instruct": {
        "name": "vertex_ai/meta/llama-4-maverick-17b-128e-instruct-maas"
  },
  "gemini-2.5-flash-preview-04-17": {
        "name": "vertex_ai/gemini-2.5-flash-preview-04-17"
  },
  "gemini-2.5-flash-preview-04-17-thinking-4096":{
        "name": "vertex_ai/gemini-2.5-flash-preview-04-17"
  },
  "gemini-2.5-pro-preview-03-25": {
        "name": "vertex_ai/gemini-2.5-pro-preview-03-25"
  },
  "gemini-2.0-flash-001":{
        "name": "vertex_ai/gemini-2.0-flash-001"
  }
}

ANTHROPIC_MODELS_MAP = {
    "claude-3-5-sonnet-20240620": {
        "name": "claude-3-5-sonnet-20240620"
    },
    "claude-3-opus-20240229": {
        "name": "claude-3-opus-20240229"
    },
    "claude-3-haiku-20240307": {
        "name": "claude-3-haiku-20240307"
    },
    "claude-3-sonnet-20240229": {
        "name": "claude-3-sonnet-20240229"
    },
    "claude-sonnet-4-20250514": {
        "name": "claude-sonnet-4-20250514"
    },
    "claude-3-7-sonnet-20240229": {
        "name": "claude-3-7-sonnet-20240229"
    },
    "claude-3-5-haiku-20241022": {
        "name": "claude-3-5-haiku-20241022"
    }
}

### Utils ###
def parse_wrapped_response(reg_exp, text_phrase):
    match = re.search(reg_exp, text_phrase, re.DOTALL)
    if match:
        return match.group(1)
    return ""

def fc_prompt_builder(tools):
    """
    tools: tool_info [tool.__info__ for tool in tools]
    """
    
    output = []
    for tool in tools:
        tool_name = tool['function']['name']
        tool_description = tool['function']['description']

        tool_string = f"> Tool Name: {tool_name}\n"
        tool_string += f"Tool Description: {tool_description}\n"
        tool_string += "Tool Args:\n"

        parameters = tool['function']['parameters']['properties']
        required_params = tool['function']['parameters'].get('required', [])

        for param, details in parameters.items():
            param_type = details['type']
            required = param in required_params
            required_str = ", required" if required else ""
            description = details.get('description', '')

            if param_type == 'array':
                item_type = details.get('items', {}).get('type', '')
                # param_type += f", where each item should be {item_type}" if item_type else ""

            tool_string += f"  - {param} ({param_type}{required_str}): {description.strip()}\n"

        output.append(tool_string.strip())

    output = "You have access to the following tools:\n" + "\n\n".join(output).strip()
    output += """
    Use the following format if using a tool:
    ```
    Action: tool name (one of [get_agents_with_max_cases, get_agents_with_min_cases, calculate_average_handle_time, get_start_date, get_period, get_agent_handled_cases_by_period, get_qualified_agent_ids_by_case_count, get_cases, get_non_transferred_case_ids, get_agent_transferred_cases_by_period, get_shipping_state, calculate_region_average_closure_times, get_order_item_ids_by_product, get_issue_counts, find_id_with_max_value, find_id_with_min_value, get_account_id_by_contact_id, get_purchase_history, get_month_to_case_count, search_knowledge_articles, search_products, get_issues, submit, get_livechat_transcript_by_case_id, get_email_messages_by_case_id])
    Action Input: the input to the tool, in a JSON format representing the kwargs (e.g. ```{"input": "hello world", "num_beams": 5}```)
    ```
    """
    return output

    
### Metrics ###
bleu_scorer = BLEU()
rouge_scorer = Rouge()

def normalize_answer(s):
    """Lower text and remove punctuation, articles and extra whitespace."""

    def remove_articles(text):
        return re.sub(r'\b(a|an|the)\b', ' ', text)

    def white_space_fix(text):
        return ' '.join(text.split())

    def handle_punc(text):
        exclude = set(string.punctuation + "".join([u"‘", u"’", u"´", u"`"]))
        return ''.join(ch if ch not in exclude else ' ' for ch in text)

    def lower(text):
        return text.lower()

    def replace_underscore(text):
        return text.replace('_', ' ')

    return white_space_fix(remove_articles(handle_punc(lower(replace_underscore(s))))).strip()


def exact_match_score(prediction, ground_truth):
    return normalize_answer(prediction) == normalize_answer(ground_truth)


def f1_score(prediction, ground_truth):
    prediction_tokens = normalize_answer(prediction).split()
    ground_truth_tokens = normalize_answer(ground_truth).split()
    common = Counter(prediction_tokens) & Counter(ground_truth_tokens)
    num_same = sum(common.values())
    if num_same == 0:
        return 0
    precision = 1.0 * num_same / len(prediction_tokens)
    recall = 1.0 * num_same / len(ground_truth_tokens)
    f1 = (2 * precision * recall) / (precision + recall)
    return f1


def bleu_score(prediction, ground_truth):
    score = bleu_scorer.sentence_score(
        hypothesis=normalize_answer(prediction),
        references=[normalize_answer(ground_truth)],
    )
    return score.score / 100

def rouge_score(prediction, ground_truth):
    score = rouge_scorer.get_scores(
        hyps=normalize_answer(prediction),
        refs=normalize_answer(ground_truth),
    )
    return {
        "rouge-1": score[0]["rouge-1"]["f"],
        "rouge-2": score[0]["rouge-2"]["f"],
        "rouge-l": score[0]["rouge-l"]["f"],
    }
    
def get_all_metrics(prediction, ground_truth):
    em = exact_match_score(prediction, ground_truth)
    f1 = f1_score(prediction, ground_truth)
    bleu = bleu_score(prediction, ground_truth)
    rouge = rouge_score(prediction, ground_truth)
    return {
        "em": em,
        "f1": f1,
        "bleu": bleu,
        "rouge": rouge,
    }