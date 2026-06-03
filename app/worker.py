# app/worker.py
# Logic: Fetches diff & template, calls local LM Studio, posts comment back to GitHub

import os
import requests
import json
import base64
from openai import OpenAI
from .prompt import SYSTEM_PROMPT, PR_ANALYSIS_PROMPT

def run_agentic_workflow(data):
    try:
        print("🚀 [AGENT] Workflow processing started...")
        repo = data["repository"]["full_name"]
        pr_num = data["pull_request"]["number"]
        token = os.getenv("GITHUB_TOKEN")
        
        headers = {"Authorization": f"token {token}"}

        # 1. Get the Diff from GitHub
        diff_headers = {**headers, "Accept": "application/vnd.github.v3.diff"}
        diff_res = requests.get(
            f"https://api.github.com/repos/{repo}/pulls/{pr_num}", 
            headers=diff_headers
        )
        diff = diff_res.text
        print(f"📦 [AGENT] Successfully fetched git diff ({len(diff)} characters)")

        # 2. Get the PR Template from the repository
        template_url = f"https://api.github.com/repos/{repo}/contents/.github/PULL_REQUEST_TEMPLATE.md"
        template_res = requests.get(template_url, headers=headers).json()
        
        # GitHub API returns file contents as base64 strings; we must decode it
        if "content" in template_res:
            template_content = base64.b64decode(template_res['content']).decode('utf-8')
            print("📄 [AGENT] Successfully fetched and decoded repository PR template")
        else:
            # Fallback string if template file doesn't exist in the repo
            template_content = "## Summary\n## Changes\n## Testing Plan"
            print("⚠️ [AGENT] PR Template not found in repo, using fallback headers.")

        # 3. Connect to LM Studio via Docker network bridge
        client = OpenAI(
            base_url="http://host.docker.internal:1234/v1",
            api_key="not-needed"  # Standard placeholder string
        )

        # Automatically detect whichever model you have loaded in the LM Studio UI
        models = client.models.list()
        model_id = models.data[0].id
        print(f"🧠 [AGENT] Communicating with LM Studio model: {model_id}")

        # Format our structural prompting framework with the fresh Git data
        user_content = PR_ANALYSIS_PROMPT.format(template=template_content, diff=diff)
        
        # Flatten the payload into a single string to prevent Mistral "Role" crashes
        combined_content = f"{SYSTEM_PROMPT}\n\n{user_content}"

        # 4. Request completion from LM Studio
        response = client.chat.completions.create(
            model=model_id,
            messages=[
                {"role": "user", "content": combined_content}
            ],
            temperature=0.2
        )
        ai_output = response.choices[0].message.content
        print("✍️ [AGENT] AI analysis generated perfectly")

        # 5. Post filled template back to GitHub PR as a comment
        comment_url = f"https://api.github.com/repos/{repo}/issues/{pr_num}/comments"
        post_res = requests.post(
            comment_url,
            headers=headers,
            json={"body": ai_output}
        )
        
        if post_res.status_code == 201:
            print(f"✅ [AGENT] Comment successfully posted to PR #{pr_num}!")
        else:
            print(f"❌ [AGENT] Failed to post comment. GitHub Response: {post_res.text}")

    except Exception as e:
        # Crucial for catching silent errors inside background worker threads
        print(f"💥 [AGENT ERROR] Critical runtime failure: {str(e)}")