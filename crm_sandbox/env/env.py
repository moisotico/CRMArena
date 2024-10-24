import random
from typing import Any, Callable, Dict, List, Type, Optional, Set, Union, Tuple
from crm_sandbox.env.connect_sandbox import SalesforceConnector
from concurrent.futures import ThreadPoolExecutor
from crm_sandbox.agents.utils import get_all_metrics

class ChatEnv(object):
    def __init__(
        self,
        tasks: List[Dict],
        task_index: Optional[int] = None,
    ) -> None:
        super().__init__()
        self.tasks = tasks
        if task_index is not None:
            self.task_index = task_index
        else:
            self.task_index = random.choice(list(tasks.keys()))
        self.task = tasks[self.task_index]
        self.actions: List = []
        self.sf_connector = SalesforceConnector()

    def reset(self, task_index: int = 0):
        self.task = self.tasks[task_index]
        self.actions = []
        initial_observation, metadata = self.task.get("query", ""), self.task.get("metadata", "")
        return initial_observation, metadata
        

    def step(self, action):
        self.actions.append(action)
        reward = 0
        done = False
        info = {}
        if action["name"] == "execute":
            result, status = self.sf_connector.run_query(action["content"])
            observation = result
            if status == 0:
                info["end_reason"] = {
                    "source": "agent",
                    "message": "SOQL/SOSL query error",
                    "content":  observation
                }
            else:
                info["observation_size"] = len(result)
        elif action["name"] == "submit":
            observation = "DONE"
            done = True
            info["end_reason"] = {
                "source": "agent",
                "message": "Submit action",
                "content":  action["content"]
            }
            reward = self.calculate_reward()
        print("Observation:", observation)
        info["agent_actions"] = self.actions
        return str(observation), reward, done, info

    def calculate_reward(self, is_end=False) -> float:
        proposed_answer = self.actions[-1]["content"]
        gt_answer = self.task["answer"]
        if gt_answer == None:
            gt_answer = "None"
        reward = 0
        print(gt_answer, "||", proposed_answer)
        if self.task["reward_metric"] == "exact_match":
            
            if proposed_answer == gt_answer:
                reward = 1
        elif self.task["reward_metric"] == "fuzzy_match":
            reward = get_all_metrics(proposed_answer, gt_answer)
        return reward
        
            
class ToolEnv(object):
    def __init__(
        self,
        tools: List[Callable],
        tasks: List[Dict],
        task_index: Optional[int] = None
    ) -> None:
        super().__init__()
        self.tasks = tasks
        if task_index is not None:
            self.task_index = task_index
        else:
            self.task_index = random.choice(list(tasks.keys()))
        self.task = tasks[self.task_index]
        self.actions: List = []
        self.sf_connector = SalesforceConnector()
        
        self.tools = tools
        self.tools_dict = {tool.__name__: tool for tool in tools}
        self.tools_info = [tool.__info__ for tool in tools]

    def reset(self, task_index: int = 0):
        self.task = self.tasks[task_index]
        self.actions = []
        initial_observation, metadata = self.task.get("query", ""), self.task.get("metadata", "")
        return initial_observation, metadata
        

    def step(self, action):
        self.actions.append(action)
        reward = 0
        done = False
        info = {}
        
        if action["name"] in self.tools_dict:
            observation = "DONE"
            if action["name"] == "submit":
                done = True
                info["end_reason"] = {
                    "source": "agent",
                    "message": "Submit action",
                    "content":  action["arguments"]["content"]
                }
                reward = self.calculate_reward()
            else:
                try:
                    observation = self.tools_dict[action["name"]](
                        **action["arguments"], sf_connector=self.sf_connector
                    )
                except Exception as e:
                    observation = f"Error: {e}"
                reward, done = 0, False
                info["end_reason"] = {
                    "source": "tool",
                    "message": f"tool_call error: {action['name']}",
                    "content":  observation
                }
        else:
            observation = f"Unknown action {action['name']}"
            reward, done = 0, False
            info["end_reason"] = {
                "source": "agent",
                "message": f"Invalid tool: {action['name']}",
                "content":  observation
            }

        print("Observation:", observation, flush=True)
        info["agent_actions"] = self.actions
        return str(observation), reward, done, info

    def calculate_reward(self, is_end=False) -> float:
        proposed_answer = self.actions[-1]["arguments"]["content"]
        gt_answer = self.task["answer"]
        if gt_answer == None:
            gt_answer = "None"
        reward = 0
        print(gt_answer, "||", proposed_answer)
        if self.task["reward_metric"] == "exact_match":
            
            if proposed_answer == gt_answer:
                reward = 1
        elif self.task["reward_metric"] == "fuzzy_match":
            reward = get_all_metrics(proposed_answer, gt_answer)
        return reward
