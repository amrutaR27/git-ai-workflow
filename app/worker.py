# Logic: Fetches diff, calls AI, posts comment
import os, requests, boto3, json

def run_agentic_workflow(data):
    repo = data["repository"]["full_name"]
    pr_num = data["pull_request"]["number"]
    token = os.getenv("GITHUB_TOKEN")
    
    # 1. Get the Diff
    diff = requests.get(
        f"https://api.github.com/repos/{repo}/pulls/{pr_num}",
        headers={"Authorization": f"token {token}", "Accept": "application/vnd.github.v3.diff"}
    ).text

    # 2. Call Bedrock
    bedrock = boto3.client("bedrock-runtime", region_name="us-east-1")
    prompt = f"Use this git diff to fill out a PR template. Diff:\n{diff}"
    
    # (Simplified Bedrock call)
    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 1000,
        "messages": [{"role": "user", "content": prompt}]
    })
    response = bedrock.invoke_model(modelId="anthropic.claude-3-sonnet-20240229-v1:0", body=body)
    ai_output = json.loads(response.get("body").read())['content'][0]['text']

    # 3. Post Comment
    requests.post(
        f"https://api.github.com/repos/{repo}/issues/{pr_num}/comments",
        headers={"Authorization": f"token {token}"},
        json={"body": f"### 🤖 AI Analysis\n{ai_output}"}
    )