import re

file_path = r'c:\Users\neels\OneDrive\Desktop\farmxpert\AIfarmxpert\farmxpert\core\super_agent.py'

with open(file_path, 'rb') as f:
    content = f.read()

# Use regex to find and replace
pattern = rb'answer = "Here\'s the recommended action plan based on your inputs\." if agents_used else "Please provide crop and location details for a precise recommendation\."'

new_code = b'''# Generate a more natural answer using agent data
        answer_parts = []
        for r in agent_responses:
            if r.success and isinstance(r.data, dict):
                agent_resp = r.data.get("response") or r.data.get("answer") or r.data.get("message", "")
                if agent_resp and isinstance(agent_resp, str) and len(agent_resp) > 20:
                    answer_parts.append(agent_resp)
        
        if answer_parts:
            answer = " ".join(answer_parts[:2])  # Combine top 2 agent responses
        elif agents_used:
            answer = f"Based on analysis from {', '.join(agents_used)}, here are my recommendations for your farm."
        else:
            answer = "I'd be happy to help with your farming needs. Please provide more details about your crop, location, and situation for specific recommendations."'''

if re.search(pattern, content):
    content = re.sub(pattern, new_code, content)
    with open(file_path, 'wb') as f:
        f.write(content)
    print("Successfully replaced hardcoded text!")
else:
    # Check if already replaced
    if b"answer_parts" in content:
        print("Already replaced!")
    else:
        # Try to find the line
        if b"Here's the recommended action plan" in content:
            print("Found the text, trying simpler replacement...")
            content = content.replace(
                b'answer = "Here\'s the recommended action plan based on your inputs." if agents_used else "Please provide crop and location details for a precise recommendation."',
                new_code
            )
            with open(file_path, 'wb') as f:
                f.write(content)
            print("Replacement done!")
        else:
            print("Could not find the target line")
