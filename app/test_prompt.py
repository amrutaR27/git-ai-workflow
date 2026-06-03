import os
from openai import OpenAI
# Import your prompts exactly how your worker does
from prompt import SYSTEM_PROMPT, PR_ANALYSIS_PROMPT

# 1. Setup LM Studio local client
client = OpenAI(
    base_url="http://localhost:1234/v1",  # Using localhost since we run this directly on your Mac
    api_key="lm-studio"
)

# 2. Define a fake PR template (Simulating your .github file)
mock_template = """
## Summary
## Changes
## Tech Stack Impact
- [ ] Laravel (Backend)
- [ ] Vue (Frontend)
"""

# 3. Define a fake Git Diff (Simulating a Laravel/Vue change)
mock_diff = """
diff --git a/app/Http/Controllers/UserController.php b/app/Http/Controllers/UserController.php
index e69de29..d0015b6 100644
--- a/app/Http/Controllers/UserController.php
+++ b/app/Http/Controllers/UserController.php
@@ -10,4 +10,8 @@ class UserController extends Controller {
+    public function getActiveUsers() {
+        // FIXED: Added eager loading to prevent N+1 query bug
+        return User::with('profile')->where('active', 1)->get();
+    }
diff --git a/resources/js/components/UserList.vue b/resources/js/components/UserList.vue
+ <template>
+   <div v-for="user in users" :key="user.id">{{ user.name }}</div>
+ </template>
"""

def test_ai_prompt():
    print("🤖 Testing prompt against LM Studio...")
    
    # 1. Grab the active model
    models = client.models.list()
    model_id = models.data[0].id
    print(f"🧠 Using model: {model_id}")
    
    # 2. Format the user prompt data
    user_content = PR_ANALYSIS_PROMPT.format(template=mock_template, diff=mock_diff)
    
    # 3. DEFINE combined_content FIRST (This was missing or misplaced!)
    combined_content = f"{SYSTEM_PROMPT}\n\n{user_content}"
    
    # 4. Pass it into the messages array
    response = client.chat.completions.create(
        model=model_id,
        messages=[
            {"role": "user", "content": combined_content}
        ],
        temperature=0.2
    )
    
    print("\n📝 --- AI OUTPUT START --- \n")
    print(response.choices[0].message.content)
    print("\n📝 --- AI OUTPUT END --- \n")

if __name__ == "__main__":
    test_ai_prompt()