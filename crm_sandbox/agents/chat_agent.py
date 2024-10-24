import os
from litellm import completion
import litellm
litellm.set_verbose = False
from typing import Dict, List
import time, traceback
from crm_sandbox.agents.prompts import SCHEMA_STRING, ACT_RULE_STRING, REACT_RULE_STRING, ACT_PROMPT, SYSTEM_METADATA, REACT_PROMPT
from crm_sandbox.agents.utils import parse_wrapped_response, BEDROCK_MODELS_MAP, TOGETHER_MODELS_MAP
import together

def together_handler(messages, model="llama-3-70b-chat-hf", max_tokens=2000, temperature=0.0, top_p=1.0):
    client = together.Together(api_key=os.getenv("TOGETHER_API_KEY"))
    output = None
    for _ in range(10):
        try:
            output = client.chat.completions.create(
                messages = messages,
                model = model,
                max_tokens = max_tokens,
                temperature = temperature,
                top_p = top_p
            )
        except:
            traceback.print_exc()
            time.sleep(1)
        if not (output is None):
            break
    return output


class ChatAgent:
    def __init__(
        self, schema_obj, model: str = "gpt-4o", max_turns: int = 20, eval_mode="default", strategy="react", provider="bedrock"
    ):
        schema = self._build_schema(schema_obj)
        if strategy == "react":
            self.sys_prompt = REACT_PROMPT.format(system_description=schema, system="Salesforce instance") # add strategy template and schema description
        elif strategy == "act":
            self.sys_prompt = ACT_PROMPT.format(system_description=schema, system="Salesforce instance")
        self.model = model
        self.eval_mode = eval_mode
        self.max_turns = max_turns
        self.strategy = strategy
        self.info = {}
        self.usage = {"cost": [], "completion_tokens": [], "prompt_tokens": [], "total_tokens": []}
        self.provider = provider
        if provider == "bedrock" and self.model in BEDROCK_MODELS_MAP:
            os.environ["AWS_REGION_NAME"] = BEDROCK_MODELS_MAP[self.model]["region"]
            self.model = BEDROCK_MODELS_MAP[self.model]["name"]
        elif provider == "together_ai" and self.model in TOGETHER_MODELS_MAP:
            self.model = TOGETHER_MODELS_MAP[self.model]["name"]
        else:
            assert self.model in ["o1-mini", "o1-preview", "gpt-4o-2024-08-06", "gpt-3.5-turbo-0125"], "Invalid model name"

    def _build_schema(self, schema_obj):
        object_description = dict()
        for item in schema_obj:
            object_description[item["object"]] = "\n".join([f"  - {k}: {v}" for k,v in item["fields"].items()])
            
        template = SCHEMA_STRING.format(
            object_names=", ".join(object_description.keys()),
            object_fields="\n".join(
                [f"{obj}\n{fields}" for obj, fields in object_description.items()]
            )
        )
        return template
    
    def reset(self, args):
        if args["metadata"]["required"]:
            self.sys_prompt += SYSTEM_METADATA.format(system_metadata=args["metadata"]["required"], system="Salesforce instance") # add task/query-specific metadata here
        if self.eval_mode == "aided" and "optional" in args["metadata"]:
            self.sys_prompt += "\n" + args["metadata"]["optional"]
        if self.model not in ["o1-mini", "o1-preview"]:
            self.messages = [{"role": "system", "content": self.sys_prompt.strip()}]
            self.messages.append({"role": "user", "content": args["query"].strip()})
        else:
            # No system role for o1-mini and o1-preview
            self.messages = [{"role": "user", "content": self.sys_prompt + "\n\n" + args["query"]}]
        self.usage = {"cost": [], "completion_tokens": [], "prompt_tokens": [], "total_tokens": []}
        
    def act(self, env, index=None, temperature=0.0):
        query, metadata = env.reset(task_index=index)
        self.reset({"query": query, "metadata": metadata})
        # print("----")
        # print(self.sys_prompt)
        # print("----")
        total_cost = 0.0
        self.info["observation_sizes"] = []
        done = False
        reward = 0
        
        for turn_id in range(self.max_turns):
            info = {}
            # if self.provider == "together":
            #     res = together_handler(
            #         model=self.model,
            #         messages=self.messages,
            #         temperature=0.0,
            #         max_tokens=2000,
            #         top_p=1.0
            #     )
            #     message = res.choices[0].message
            #     usage = res.usage
            # else:
            res = completion(
                messages=self.messages,
                model=self.model,
                temperature=0.0,
                max_tokens=2000,
                top_p=1.0,
                # custom_llm_provider=self.provider,
                additional_drop_params=["temperature"] if self.model in ["o1-mini", "o1-preview"] else []
            )
            message = res.choices[0].message.model_dump()
            usage = res.usage
            # print(res)
            for key in self.usage.keys():
                if key != "cost":
                    self.usage[key].append(usage.get(key, 0))
            # print("cst", res._hidden_params["response_cost"])
            # self.usage["cost"].append(completion_cost(completion_response=res))
            # print(self.usage["cost"])
            self.usage["cost"].append(res._hidden_params["response_cost"])
            action = self.message_action_parser(message)
            print("#", turn_id, "Agent:", message["content"].strip())
            self.messages.append({"role": "assistant", "content": message["content"].strip()})
            if action is None:
                self.info["end_reason"] = {
                    "source": "agent",
                    "message": "Invalid action",
                    "content":  message["content"].strip()
                }
                info["end_reason"] = self.info["end_reason"]
                if self.strategy == "react":
                    self.messages.append({"role": "user", "content": REACT_RULE_STRING})
                elif self.strategy == "act":
                    self.messages.append({"role": "user", "content": ACT_RULE_STRING})
                continue
            obs, reward, done, info = env.step(action)
            if "observation_size" in info:
                self.info["observation_sizes"].append(info["observation_size"])
            if "end_reason" in info: # implies error in query
                self.info["end_reason"] = info["end_reason"]
            if done: # implies submit action
                break
            else:
                self.messages.append({"role": "user", "content": f"Salesforce instance output: {obs}"})
        
        # Here when either max_turns is reached or submitted
        if not done: 
            if "end_reason" not in info: # no error in last query
                self.info["end_reason"] = {
                    "source": "agent",
                    "message": "Max turns reached",
                    "content":  message["content"].strip()
                }
        self.info["usage"] = self.usage
        self.info["total_cost"] = sum(self.usage["cost"])
        self.info["num_turns"] = turn_id + 1
        return reward

    def get_messages(self) -> List[Dict[str, str]]:
        return self.messages

    @staticmethod
    def message_action_parser(message: str) -> Dict[str, str]:
        action = None
        resp = parse_wrapped_response(r'<execute>(.*?)</execute>', message["content"].strip()).strip()
        if resp:
            action = {"name": "execute", "content": resp}
            return action
        resp = parse_wrapped_response(r'<submit>(.*?)</submit>', message["content"].strip()).strip()
        if resp:
            action = {"name": "submit", "content": resp}
            return action
        return action