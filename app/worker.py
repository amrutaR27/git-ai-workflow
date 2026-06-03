import os
import requests
import json
from openai import OpenAI
from .prompt import SYSTEM_PROMPT, PR_ANALYSIS_PROMPT

def run_agentic_workflow(data):
    try:
        print("🚀 [AGENT] Workflow started processing...")
        repo = data["repository"]["full_name"]
        pr_num = data["pull_request"]["number"]
        token = os.getenv("GITHUB_TOKEN")
        
        headers = {"Authorization": f"token {token}"}

        # 1. Fetch the Git Diff
        diff_headers = {**headers, "Accept": "application/vnd.github.v3.diff"}
        diff_res = requests.get(f"https://api.github.com/repos/{repo}/pulls/{pr_num}", headers=diff_headers)
        diff = diff_res.text
        print(f"📦 [AGENT] Successfully fetched git diff ({len(diff)} chars)")

        # 2. Fetch the PR Template from the repository
        template_url = f"https://api.github.com/repos/{repo}/contents/.github/PULL_REQUEST_TEMPLATE.md"
        template_res = requests.get(template_url, headers=headers).json()
        
        # GitHub returns base64 for file content, let's decode it
        import base64
        template_content = base64.b64decode(template_res['content']).decode('utf-8')
        print("📄 [AGENT] Successfully fetched and decoded PR template")

        # 3. Setup Client for LM Studio (OpenAI Compatible)
        # Pointing to the host machine through Docker bridge
        client = OpenAI(
            base_url="http://host.docker.internal:1234/v1",
            api_key="lm-studio"  # Required string but ignored by LM Studio
        )

        # Get whatever model is currently loaded in your LM Studio UI
        models = client.models.list()
        model_id = models.data[0].id
        print(f"🧠 [AGENT] Talking to LM Studio model: {model_id}")

        # Format our structural user prompt
        user_content = PR_ANALYSIS_PROMPT.format(template=template_content, diff=diff)

        # 4. Call LM Studio
        response = client.chat.completions.create(
            model=model_id,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_content}
            ],
            temperature=0.2
        )
        ai_output = response.choices[0].message.content
        print("✍️ [AGENT] AI response generated successfully")

        # 5. Post Comment back to GitHub PR
        comment_url = f"https://api.github.com/repos/{repo}/issues/{pr_num}/comments"
        post_res = requests.post(
            comment_url,
            headers=headers,
            json={"body": ai_output}
        )
        
        if post_res.status_code == 201:
            print("✅ [AGENT] Comment successfully added to PR!")
        else:
            print(f"❌ [AGENT] Failed to post comment. GitHub response: {post_res.text}")

    except Exception as e:
        # Crucial: This will force errors to display in your docker logs
        print(f"💥 [AGENT ERROR] Critical failure in background task: {str(e)}")