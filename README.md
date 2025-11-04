# CRMArena

### Installation

#### Option 1: Using uv (Recommended for faster installation)
```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create a virtual environment and install dependencies
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e .
```

#### Option 2: Using pip (Traditional)
```bash
# Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install the package
pip install -e .
```

#### Alternative: Install from requirements file
```bash
# If you prefer to use the requirements file directly
uv pip install -r requirements-fixed.txt  # with uv
# or
pip install -r requirements-fixed.txt     # with pip
```/abs/2505.18878"><img src="figures/crmarena_logo.png" height="120" ></a>
</div>


<div align="center">
<strong>Salesforce AI Research</strong>
</div>
This repo contains the evaluation code for the paper "<a href="https://arxiv.org/abs/2505.18878">CRMArena-Pro: Holistic Assessment of LLM Agents Across Diverse Business Scenarios and Interactions</a>" and "<a href="https://arxiv.org/abs/2411.02305">CRMArena: Understanding the Capacity of LLM Agents to Perform Professional CRM Tasks in Realistic Environments</a>"
<hr>





### 📚 CRMArena
<a href='https://arxiv.org/abs/2411.02305'><img src='https://img.shields.io/badge/📄_arXiv-2411.02305-b31b1b.svg?style=for-the-badge' alt='arXiv: CRMArena Paper'></a>
<a href='https://huggingface.co/datasets/Salesforce/CRMArena'><img src='https://img.shields.io/badge/🤗_Dataset-CRMArena-blue.svg?style=for-the-badge' alt='CRMArena Data on Hugging Face'></a>
<a href='https://huggingface.co/spaces/Salesforce/CRMArena-Leaderboard'><img src='https://img.shields.io/badge/🏆_Leaderboard-CRMArena-orange.svg?style=for-the-badge' alt='CRMArena Leaderboard on Hugging Face'></a>

### 🚀 CRMArena-Pro
<a href='https://arxiv.org/abs/2505.18878'><img src='https://img.shields.io/badge/📄_arXiv-2505.18878-b31b1b.svg?style=for-the-badge' alt='arXiv: CRMArena-Pro Paper'></a>
<a href='https://huggingface.co/datasets/Salesforce/CRMArenaPro'><img src='https://img.shields.io/badge/🤗_Dataset-CRMArenaPro-blue.svg?style=for-the-badge' alt='CRMArena-Pro Data on Hugging Face'></a>


<!-- Common License -->
<a href='https://github.com/SalesforceAIResearch/CRMArena/blob/main/LICENSE.txt'><img src='https://img.shields.io/badge/License-CC_NC_4.0-blue' alt='License: CC BY-NC 4.0'></a>


## 🔔News

- **🌟 [2025-05] Introducing [CRMArena-Pro](https://arxiv.org/abs/2505.18878) - a major expansion of the original CRMArena featuring enhanced support for diverse business applications, industry types, and interactive scenarios! 🚀**
- **🎉 [2024-01] CRMArena has been accepted by NAACL 2025!**



**Note: This repository is for research purposes only and not for commerical.**


## Quickstart

### Installation

#### Option 1: Using pip (Traditional)
```bash
pip install -e .
```

#### Option 2: Using uv (Recommended)
```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies using uv
uv pip install -r requirements-fixed.txt
uv pip install -e .
```

### Environment Setup

To access our org, use the following credentials. 

```bash
# the original CRMArena
SALESFORCE_USERNAME=kh.huang+00dws000004urq4@salesforce.com
SALESFORCE_PASSWORD=crmarenatest0
SALESFORCE_SECURITY_TOKEN=ugvBSBv0ArI7dayfqUY0wMGu

# CRMArena-Pro B2B
SALESFORCE_B2B_USERNAME=crmarena_b2b@gmaill.com
SALESFORCE_B2B_PASSWORD=crmarenatest0
SALESFORCE_B2B_SECURITY_TOKEN=zdaqqSYBEQTjjLuq0zLUHkC3

# CRMArena-Pro B2C
SALESFORCE_B2C_USERNAME=crmarena_b2c@gmaill.com
SALESFORCE_B2C_PASSWORD=crmarenatest0
SALESFORCE_B2C_SECURITY_TOKEN=QAqyxjPiLJGQuGAAG9YsOHKhn
```

### Accessing the Org via GUI

To access the GUI of our Org, follow the steps below:

1. Head to https://login.salesforce.com/.
2. Type in the user name and password using the above credentials.
<div align="center">
<a href="https://pluslabnlp.github.io/"><img src="figures/GUI_login.png" height="400" ></a>
</div>

3. You can now see the GUI of our Org.




### Accessing the Org via API

First, create a `.env` file by copying from `.env.example` which already contains the credentials for the Org.

```bash
cp .env.example .env
```

Then, store your Salesforce org / OpenAI / Anthropic / AWS Bedrock / TogetherAI API keys in `.env`
```bash
OPENAI_API_KEY=...
ANTHROPIC_API_KEY=...
...
```

After that, you can use Simple Salesforce to connect to our Org.

```python
from simple_salesforce import Salesforce
import os

sf = Salesforce(username=os.getenv("SALESFORCE_USERNAME"), password=os.getenv("SALESFORCE_PASSWORD"), security_token=os.getenv("SALESFORCE_SECURITY_TOKEN"))

sf.query.query_all(...)
```


## Running experiments

To run experiments, you first need to ensure that the necessary data is available. The data is loaded from Hugging Face datasets "Salesforce/CRMArena" and "Salesforce/CRMArenaPro" as defined in `crm_sandbox/data/assets.py`.

```python
from datasets import load_dataset

# Original CRMArena data
crmarena_queries = load_dataset("Salesforce/CRMArena", "CRMArena")
crmarena_schema = load_dataset("Salesforce/CRMArena", "schema")

# CRMArena-Pro data
crmarena_pro_queries = load_dataset("Salesforce/CRMArenaPro", "CRMArenaPro")
b2b_schema = load_dataset("Salesforce/CRMArenaPro", "b2b_schema")
b2c_schema = load_dataset("Salesforce/CRMArenaPro", "b2c_schema")
```
For more details on data loading and structure, please refer to `crm_sandbox/data/assets.py`.

### Command Line Arguments

The `run_tasks.py` script supports various command-line arguments for customization:

#### Core Arguments:
- `--model`: The LLM model to use (e.g., `gpt-4o-mini-2024-07-18`, `o1-2024-12-17`)
- `--agent_strategy`: Agent strategy (`react`, `act`, `tool_call`, `tool_call_flex`)
- `--task_category`: Specific task category or `all` for all tasks
- `--org_type`: Organization type (`b2b`, `b2c`, `original`)
- `--interactive`: Enable interactive mode (only supported with `react` strategy)

#### Rate Limiting Arguments:
- `--task_delay`: Delay between tasks in seconds (default: 1.0, recommended: 3.0+ for OpenAI)

#### Other Arguments:
- `--llm_provider`: LLM provider (`openai`, `anthropic`, `vertex_ai`, `together_ai`, `bedrock`)
- `--agent_eval_mode`: Evaluation mode (`default`, `aided`)
- `--max_turns`: Maximum agent turns per task (default: 20)
- `--max_user_turns`: Maximum user turns in interactive mode (default: 10)
- `--reuse_results`: Reuse results from previous runs
- `--privacy_aware_prompt`: Use privacy-aware prompts (`true`/`false`)
- `--log_dir`: Directory for saving results and logs

#### Example Usage:
```bash
# Run specific task with custom rate limiting
python run_tasks.py \
    --model gpt-4o-mini-2024-07-18 \
    --task_category knowledge_qa \
    --agent_strategy react \
    --org_type b2b \
    --llm_provider openai \
    --task_delay 5.0 \
    --reuse_results
```

We have prepared evaluation scripts to simplify the process of running experiments.

### Running CRMArena Experiments

To run experiments for the original CRMArena:
1. Configure your desired settings (agent models, tasks, strategies, etc.) in `run_tasks_crmarena.sh`.
2. Launch the experiments using the following command:

```bash
bash run_tasks_crmarena.sh
```

### Running CRMArena-Pro Experiments

To run experiments for CRMArena-Pro:
1. Configure your desired settings (agent models, tasks, strategies, interactive mode, org type, etc.) in `run_tasks_crmarena_pro.sh`.
2. Launch the experiments using the following command:

```bash
bash run_tasks_crmarena_pro.sh
```

**Note**: The shell scripts are pre-configured with `--task_delay 3.0` for better rate limiting when using OpenAI models.

These scripts will execute `run_tasks.py` with the specified configurations and save the results and logs in appropriately named directories.

### Rate Limiting and API Management

The evaluation scripts include built-in rate limiting to prevent API timeouts, especially when using OpenAI models:

#### Built-in Rate Limiting Features:
- **Task-level delays**: Configurable delay between tasks (default: 1.0 seconds, increased to 3.0 seconds in shell scripts)
- **Provider-specific delays**: 2-second delays for OpenAI API calls, 5-second delays for other providers
- **Tool call delays**: 3-second delays between tool calls in tool-based strategies

#### Customizing Rate Limits:
You can adjust rate limiting by modifying the `--task_delay` parameter in the shell scripts or when running `run_tasks.py` directly:

```bash
# Example: Use 5-second delays between tasks for conservative rate limiting
python run_tasks.py --task_delay 5.0 --model gpt-4o-mini-2024-07-18 --task_category knowledge_qa
```

#### Additional Options for Rate Limiting:
- Run specific task categories instead of "all" tasks to reduce load
- Monitor your API provider's rate limit dashboard
- Consider running tasks sequentially instead of in parallel by removing `&` from shell scripts


## Citation

If you find this work useful, please consider citing:

```bibtex
@inproceedings{huang-etal-2025-crmarena,
    title = "CRMArena: Understanding the Capacity of LLM Agents to Perform Professional CRM Tasks in Realistic Environments",
    author = "Huang, Kung-Hsiang  and
      Prabhakar, Akshara  and
      Dhawan, Sidharth  and
      Mao, Yixin  and
      Wang, Huan  and
      Savarese, Silvio  and
      Xiong, Caiming  and
      Laban, Philippe  and
      Wu, Chien-Sheng",
    booktitle = "Proceedings of the 2025 Conference of the Nations of the Americas Chapter of the Association for Computational Linguistics: Human Language Technologies (Volume 1: Long Papers)",
    year = "2025",
}

@article{huang-etal-2025-crmarena-pro,
    title = "CRMArena-Pro: Holistic Assessment of LLM Agents Across Diverse Business Scenarios and Interactions",
    author = "Huang, Kung-Hsiang  and
      Prabhakar, Akshara  and
      Thorat, Onkar  and
      Agarwal, Divyansh  and
      Choubey, Prafulla Kumar  and
      Mao, Yixin  and
      Savarese, Silvio  and
      Xiong, Caiming  and
      Wu, Chien-Sheng",
    journal = "arXiv preprint arXiv:2505.18878",
    year = "2025",
}
```

## Ethical Considerations
This release is for research purposes only in support of an academic paper. Our models, datasets, and code are not specifically designed or evaluated for all downstream purposes. We strongly recommend users evaluate and address potential concerns related to accuracy, safety, and fairness before deploying this model. We encourage users to consider the common limitations of AI, comply with applicable laws, and leverage best practices when selecting use cases, particularly for high-risk scenarios where errors or misuse could significantly impact people's lives, rights, or safety. For further guidance on use cases, refer to our AUP and AI AUP. 

