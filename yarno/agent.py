balance = 10000
import time

class Agent:
    def __init__(self, name, description):
        self.name = name
        self.description = description
    
    def excute(self, requirement, context):
        print(f"Executing requirement: {requirement['name']}")
        time.sleep(2)
        result = f"Uploaded your context as a agent in yarns"
        return result
    

def get_context():
    with open('context.md', 'r') as file:
        raw_context = file.read()
    return raw_context

def get_balance():
    return balance

def analyze_requirements(context):
    # 分析上下文，提取用户需求
    requirements = [
        {
            "name": "利用 context 提供咨询",
            "description": "用户可以把经历发布到平台以提供咨询",
        }
    ]
    return requirements

def request_authorization(hint):
    # 请求用户授权
    authorization = input(hint)
    return authorization == "y"

def find_agent(requirement):
    # 查找能够执行需求的智能体
    agent = Agent("Consultant", "yarns agent")
    return agent

def main():
    print("Loading user context...")
    context = get_context()
    print("Context loaded.")

    # 每天分析获得需求
    print("Analyzing user requirements based on context...")
    requirements = analyze_requirements(context)

    # 由于需要用户授权信息，所以需要用户授权
    print("Requesting user authorization...")
    hint = "Do you authorize the use of your context? (y/n) "
    authorization = request_authorization(hint)

    # 如果用户授权，则执行需求
    if authorization:
        print("Authorization granted.")
        for requirement in requirements:
            print(f"Executing requirement: {requirement['name']}")
            print("Searching for agents that could help me finish that...")
            agent = find_agent(requirement)
            if agent:
                print("Found agent:")
                print(f"- {agent.name}: {agent.description}")
            else:
                print("No agent found.")
                continue
            print("Executing requirement...")
            result = agent.excute(requirement, context)
            print("Requirement executed.")
            print(result)


    else:
        print("Authorization denied.")

if __name__ == "__main__":
    main()
