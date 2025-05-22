from pydantic import BaseModel
from openai import OpenAI
import json

# Grok-3 evaluation    
client = OpenAI(
  api_key="switch to your grok3 key",
  base_url="https://api.x.ai/v1",
)
model = "grok-3-beta"

# qwen-4b evaluation through lm studio
# client = OpenAI(base_url="http://127.0.0.1:1234/v1", api_key="lm-studio")
# model = "qwen3-4b"

SYSTEM_PROMPT = "You are an expert story reviewer, you are strict and good at judge the quality of a story."

class Benchmark(BaseModel):
    explanation: str
    final_output: list[int]

def generate_prompt(story_text):
    return f"""
Now I will give you a story, please evaluate it based on the following benchmarks:

1. Fluency
2. Creativity
3. Attractiveness
4. Plausibility

##Story:
{story_text}

Give each benchmark a score from 0 to 10. Give me your explanation, and the final_output should be a list of score: [fluency, creativity, attractiveness, plausibility].
"""

ap_fluency = 0
ap_creativity = 0
ap_attractiveness = 0
ap_plausibility = 0
direct_fluency = 0
direct_creativity = 0
direct_attractiveness = 0
direct_plausibility = 0

temp = ['drone_', 'earphone_', 'smartphone_']


# Evaluate 30 examples, 3 times for 1 story.
for i in temp:
    for j in range(10):
        file_name = "samples/" + i + str(j) + '.json'
        with open(file_name, 'r') as f:
            data = json.load(f)
            ap_story = data[0]["story"]
            direct_story = data[1]["story"]
            ap_prompt = generate_prompt(ap_story)
            direct_prompt = generate_prompt(direct_story)
            temp_ap = []
            temp_direct = []
            for k in range(3):
                completion = client.beta.chat.completions.parse(
                    model=model,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": ap_prompt},
                    ],
                    temperature=0,
                    response_format=Benchmark,    
                )
                score = completion.choices[0].message.parsed.final_output
                temp_ap.append(score)
                completion = client.beta.chat.completions.parse(
                    model=model,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": direct_prompt},
                    ],
                    temperature=0,
                    response_format=Benchmark,    
                )
                score = completion.choices[0].message.parsed.final_output
                temp_direct.append(score)
            ap_score = [(x + y + z) / 3 for x, y, z in zip(temp_ap[0], temp_ap[1], temp_ap[2])]
            direct_score = [(x + y + z) / 3 for x, y, z in zip(temp_direct[0], temp_direct[1], temp_direct[2])]
            print(ap_score)
            print(direct_score)
            ap_fluency += ap_score[0]
            ap_creativity += ap_score[1]
            ap_attractiveness += ap_score[2]
            ap_plausibility += ap_score[3]
            direct_fluency += direct_score[0]
            direct_creativity += direct_score[1]
            direct_attractiveness += direct_score[2]
            direct_plausibility += direct_score[3]
            print("finish " + file_name)

print("AP-based fluency: " + str(ap_fluency / 30))
print("AP-based creativity: " + str(ap_creativity / 30))
print("AP-based attractiveness: " + str(ap_attractiveness / 30))
print("AP-based plausibility: " + str(ap_plausibility / 30))
print("Direct fluency: " + str(direct_fluency / 30))
print("Direct creativity: " + str(direct_creativity / 30))
print("Direct attractiveness: " + str(direct_attractiveness / 30))
print("Direct plausibility: " + str(direct_plausibility / 30))