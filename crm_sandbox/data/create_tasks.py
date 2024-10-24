import json, os

data_path = "data/crm_arena"
files = [os.path.join(data_path,f) for f in os.listdir(data_path) if f.endswith('.jsonl')]
data = []
for file in files:
    with open(file, 'r') as f:
        contents = f.readlines()
        for line in (contents):
            line = json.loads(line)
            data.append(line)

print("Total tasks:", len(data))

domain_metadata = {
    "quarters_info": """\
## Quarters of the Year
- Q1: January 1 to March 31 (both inclusive).
- Q2: April 1 to June 30 (both inclusive).
- Q3: July 1 to September 30 (both inclusive).
- Q4: October 1 to December 31 (both inclusive).""",
    "seasons_info": """\
## Seasons
- Winter: December 1 to February 28/29 (both inclusive).
- Spring: March 1 to May 31 (both inclusive).
- Summer: June 1 to August 31 (both inclusive).
- Autumn/Fall: September 1 to November 30 (both inclusive).""",
    "time_periods_info": """\
## Time Periods
- Past 2 quarters: This refers to any timeframe spanning two quarters back from a specified `end_date`. That translates to a six-month period retrospectively from the `end_date`.
- Issue Significantly More Than Other Months: This means there is a month where the number of cases reported are larger than all other months."""
}


tasks = []
for i,item in enumerate(data):
    task = {}
    task["idx"] = i
    task["answer"] = item["answer"]
    assert len(task["answer"]) == 1, "Only single answer supported"
    task["answer"] = task["answer"][0]
    task["type"] = item["metadata"]["task"]
    task["metadata"] = {
        "required": "",
        "optional": "# Domain Details\n" + "\n".join([v for k,v in domain_metadata.items()]) # adding all domain-specific metadata as optional
    }
    task["reward_metric"] = "exact_match"
    task["query"] = item["query"]
    
    if task["type"] in ["handle_time", "transfer_time", "named_entity_disambiguation", "top_issue_identification", "best_region_identification", "seasonality_identification"]:
        date = item["metadata"]["today"]
    
    if task["type"] == "handle_time":
        task["query"] = f"{item['query']} Return only the Id of the agent."
        task["metadata"]["required"] = f"""\
## Handle Time Policy
- Definition: The duration taken to close a case. Specifically, it is the time from when a case is opened to when it is closed.
- In the queries that specify 'agents managed/queries x cases' -- this filter applies to the first agent that the case was first assigned to. This means that if an agent has 2 cases that was initially assigned to itself by admin and 1 case transferred from another agent, a filter like 'handled/managed at least 3 cases' would filter this agent out.
- When computing handle time, we do not compute handle time for cases that have been transferred to other agents.
- For cases that have NOT been transferred to an other agent, there will be only ONE 'Owner Assignment', and for those that have been transferred, there will be MORE THAN ONE 'Owner Assignment'. 

## Today's date: {date}"""

    elif task["type"] == "transfer_time":
        task["type"] = "transfer_count"
        task["query"] = f"{item['query']} Return only the Id of the agent."
        task["metadata"]["required"] = f"""\
## Transfer Count Policy
- Definition: The number of instances a case was reassigned or transferred from one agent to another. Each transfer from agent A to agent B adds to the transfer count for agent A.
- In the queries that specify 'agents managed/queries x cases' -- this filter applies to the first agent that the case was first assigned to. This means that if an agent has 2 cases that was initially assigned to itself by admin and 1 case transferred from another agent, a filter like 'handled/managed at least 3 cases' would filter this agent out.
- For cases that have NOT been transferred to an other agent, there will be only ONE 'Owner Assignment', and for those that have been transferred, there will be MORE THAN ONE 'Owner Assignment'. 

## Today's date: {date}"""
    
    elif task["type"] == "knowledge_qa":
        task["metadata"]["required"] = "- Use the information retrieved from the knowledge articles to answer the question in a concise manner"
        task["reward_metric"] = "fuzzy_match"
    
    elif task["type"] == "case_routing":
        task["query"] = f"""Use the case routing policy to determine the most suitable agent for the given case. Return only the Id of the agent.
## Given Case
- Case Subject: {item['metadata']['case_subject']}
- Case Description: {item['metadata']['case_description']}"""
        task["metadata"]["required"] = f"""\
## Case Routing Policy
The case routing policy determines the best agent to assign the given new case based on the following criteria
- Issue Expertise: The agent who has closed the most cases associated with the issue most similar to the given case.
- Product Expertise: If there is a tie in issue expertise, the best agent is the one who has solved the most cases associated with the product most relevant to the given case.
- Workload: If there is still a tie, the best agent is the one that has least cases with Status not 'Closed'.
"""

    
    elif task["type"] == "named_entity_disambiguation":
        task["metadata"]["required"] = f"""\
- Contact Id interacting: {item['metadata']['customer_id']}
- Today's date: {date}"""
        task["query"] = f"{item['query']} Return only the Id of the product from the contact's relevant past transaction."

    elif task["type"] == "policy_violation_identification":
        task["metadata"]["required"] = f"- Case Id to be considered is: {item['metadata']['case_id']}"
        task["query"] = f"{item['query']} Return only the Id of the knowledge article or None if no violation is found."
    
    elif task["type"] == "top_issue_identification":
        task["query"] = f"{item['query']} The associated product Id is {item['metadata']['product_id']}. Return only the issue Id of the most reported issue for this product."
        task["metadata"]["required"] = f"- Today's date: {date}"
        
    
    elif task["type"] == "best_region_identification":
        task["query"] = f"{item['query']} Return only the two-letter abbreviation of the most matching state (eg. CA)."
        task["metadata"]["required"] = f"- Today's date: {date}"
        
    
    elif task["type"] == "seasonality_identification":
        task["type"] = "monthly_trend_analysis"
        task["query"] = f"{item['query']} The associated product Id is {item['metadata']['product_id']}. Return only the month name."
        task["metadata"]["required"] = f"- Today's date: {date}"
        
    
    tasks.append(task)

with open("tasks_natural.json", "w") as f:
    json.dump(tasks, f, indent=2)
