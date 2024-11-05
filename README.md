# CRMArena: Understanding the Capacity of LLM Agents to Perform Professional CRM Tasks in Realistic Environments

<div align="center">
<a href="https://pluslabnlp.github.io/"><img src="crmarena_logo.png" height="120" ></a>
</div>

<div align="center">
<a href="https://khuangaf.github.io/">Kung-Hsiang Huang</a>, Akshara Prabhakar, Sidharth Dhawan, Yixin Mao, Huan Wang, Silvio Savarese, Caiming Xiong, Philippe Laban, Chien-Sheng Wu

</div>
<div align="center">
<strong>Salesforce AI Research</strong>
</div>

<hr>

<!-- [![arXiv](https://img.shields.io/badge/arXiv-2312.10160-b31b1b.svg?style=for-the-badge)](https://arxiv.org/abs/2312.10160) -->

<a href='https://arxiv.org/abs/2312.10160'><img src='https://img.shields.io/badge/arXiv-2312.10160-b31b1b.svg'></a> &nbsp;&nbsp;&nbsp;
<a href='https://github.com/SalesforceAIResearch/CRMArena/blob/main/LICENSE.txt'><img src='https://img.shields.io/badge/License-CC_NC_4.0-blue'></a> &nbsp;&nbsp;&nbsp;
[![CRMArena](https://img.shields.io/badge/%F0%9F%A4%97%20Hugging%20Face-CRMArena_Data-blue)](https://huggingface.co/datasets/Salesforce/CRMArena) &nbsp;&nbsp;&nbsp;&nbsp;
[![CRMArenaBenchmark](https://img.shields.io/badge/%F0%9F%A4%97%20Hugging%20Face-CRMArena_Leaderboard-blue)](https://huggingface.co/spaces/Salesforce/CRMArena-Leaderboard) &nbsp;&nbsp;&nbsp;&nbsp;

## Abstract

Customer Relationship Management (CRM) systems are vital for modern enterprises, providing a foundation for managing customer interactions and data. Integrating AI agents into CRM systems can automate routine processes and enhance personalized service. However, deploying and evaluating these agents is challenging due to the lack of realistic benchmarks that reflect the complexity of real-world CRM tasks. To address this issue, we introduce CRMArena, a novel benchmark designed to evaluate AI agents on realistic tasks grounded in professional work environments. Following guidance from CRM experts and industry best practices, we designed CRMArena with nine customer service tasks distributed across three personas: service agent, analyst, and manager. The benchmark includes 16 commonly used industrial objects (e.g., account, order, knowledge article, case) with high interconnectivity, along with latent variables (e.g., complaint habits, policy violations) to simulate realistic data distributions. Experimental results reveal that state-of-the-art LLM agents succeed in less than 40% of the tasks with ReAct prompting, and less than 55% even with function-calling abilities. Our findings highlight the need for enhanced agent capabilities in function-calling and rule-following to be deployed in real-world work environments. CRMArena is an open challenge to the community: systems that can reliably complete tasks showcase direct business value in a popular work environment.

**Note: This repository is for research purposes only and not for commerical.**


## Quickstart

```bash
pip install -e .
```

To access our org, use the following credentials.

```
SALESFORCE_USERNAME=kh.huang+00dws000004urq4@salesforce.com
SALESFORCE_PASSWORD=crmarenatest
SALESFORCE_SECURITY_TOKEN=ugvBSBv0ArI7dayfqUY0wMGu
```

Store your Salesforce org / OpenAI / AWS Bedrock / TogetherAI API keys in `.env`
```bash
OPENAI_API_KEY=...
...
```

Configure your setup and launch experiments
```bash
bash run_tasks.sh
```

## Citation

If you find this work useful, please consider citing:

```bibtex
@misc{huang-etal-2024-crmarena,
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
    year = "2024",
    archivePrefix = "arXiv",
    eprint={2411.02305},
    primaryClass={cs.CL}
}
```