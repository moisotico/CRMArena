from dotenv import load_dotenv
import json, os
from crm_sandbox.agents import ChatAgent, ToolCallAgent
from crm_sandbox.agents.utils import BEDROCK_MODELS_MAP, TOGETHER_MODELS_MAP, VERTEX_MODELS_MAP
from crm_sandbox.data.assets import TASKS, TASKS_NATURAL, SCHEMA
from crm_sandbox.env.env import ChatEnv, ToolEnv
from crm_sandbox.env import TOOLS, TOOLS_FULL
import traceback
import argparse
from datetime import datetime
import time

def run():
    if not os.path.exists(args.log_dir):
        os.makedirs(args.log_dir)
    ckpt_path = f"{args.log_dir}/results_{args.model}_{args.agent_strategy}_{args.task_category}.json"
    if args.task_category == "all":
        selected_tasks = TASKS_NATURAL
    elif "," in args.task_category:
        selected_tasks = [task for task in TASKS_NATURAL if task["type"] in args.task_category.split(",")]
    else:
        selected_tasks = [task for task in TASKS_NATURAL if task["type"] == args.task_category]
    print(f"Loaded {len(selected_tasks)} tasks")
    start_time = datetime.now()
    print(f"Starting evaluation at {start_time}")
    selected_tasks = {t['idx']: t for t in selected_tasks}
    if args.agent_strategy in ["act", "react"]:
        env = ChatEnv(tasks=selected_tasks)
    elif args.agent_strategy == "tool_call":
        env = ToolEnv(tools=TOOLS, tasks=selected_tasks)
    elif args.agent_strategy == "tool_call_flex":
        env = ToolEnv(tools=TOOLS_FULL, tasks=selected_tasks)
    
    for idx,task in selected_tasks.items():
        if args.agent_strategy in ["act", "react"]:
            agent = ChatAgent(
                model=args.model,
                schema_obj=SCHEMA,
                eval_mode=args.agent_eval_mode,
                max_turns=args.max_turns,
                strategy=args.agent_strategy,
                provider=args.llm_provider
            )
        else:
            agent = ToolCallAgent(
                model=args.model,
                tools=env.tools_info,
                schema_obj=SCHEMA,
                eval_mode=args.agent_eval_mode,
                max_turns=args.max_turns,
                strategy=args.agent_strategy,
                provider=args.llm_provider
            )
        print(f"Running task {idx}")
        try:
            reward = agent.act(
                env,
                idx
            )
            result = {
                "task_id": idx,
                "task_type": task["type"],
                "gt_answer": task["answer"],
                "reward": reward,
                "agent_info": agent.info,
                "traj": agent.get_messages(),
            }
        except Exception as e:
            traceback.print_exc()
            result = {
                "task_id": idx,
                "task_type": task["type"],
                "gt_answer": task["answer"],
                "reward": 0,
                "agent_info": {
                    "source": "api",
                    "content": "Error: " + str(e)
                },
                "traj": agent.get_messages(),
            }
        print(
            "✅" if result["reward"] == 1 else "❌",
            f"task_id={idx}"
        )
        print("-----")
        data_res = []
        if os.path.exists(ckpt_path):
            with open(ckpt_path, "r") as f:
                data_res = json.load(f)
        with open(ckpt_path, "w") as f:
            json.dump(data_res + [result], f, indent=2)
        time.sleep(1)
    end_time = datetime.now()
    print(f"Finished evaluation at {end_time}")
    
if __name__ == "__main__":
    load_dotenv()
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--model",
        type=str,
        help="The model to use for the agent",
        default="o1-mini",
        choices = ["o1-mini", "gpt-4o", "gpt-4-turbo"].extend(BEDROCK_MODELS_MAP.keys()),
    )
    parser.add_argument(
        "--agent_strategy",
        type=str,
        default="react",
        choices=["tool_call", "act", "react", "tool_call_flex"],
    )
    parser.add_argument(
        "--agent_eval_mode",
        type=str,
        default="default",
        choices=["default", "aided"],
    )
    parser.add_argument(
        "--llm_provider",
        type=str,
        default="bedrock",
        choices=["bedrock", "together_ai", "openai", "vertex_ai"]
    )
    parser.add_argument(
        "--task_category",
        type=str,
        default="all",
        choices=["handle_time", "transfer_count", "knowledge_qa", "best_region_identification", "case_routing", "named_entity_disambiguation", "policy_violation_identification", "top_issue_identification", "monthly_trend_analysis", "all"],
        help="The category of tasks to evaluate (comma separated)",
    )
    parser.add_argument(
        "--max_turns",
        type=int,
        default=20
    )
    parser.add_argument("--log_dir", type=str, default="logs")
    args = parser.parse_args()
    print(args)

    run()
    