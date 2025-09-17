# =======================================================
# Enhanced SF Generator - Modified for OpenAI Realtime API (Text Mode)
# =======================================================
import streamlit as st
import json
import re
import time
import asyncio
import websockets
import ssl
import threading
from openai import OpenAI
from tavily import TavilyClient
import concurrent.futures

# ========== Page Setup ==========
st.set_page_config(page_title="Near-Future SF Generator", layout="wide")

# ========== Realtime API Client Class ==========
class RealtimeTextClient:
    """
    Modified Realtime API client for text-only interactions
    """
    def __init__(self, api_key):
        self.api_key = api_key
        self.url = "wss://api.openai.com/v1/realtime"
        self.model = "gpt-4o-realtime-preview-2024-10-01"
        self.ws = None
        self.response_queue = asyncio.Queue()
        self.is_connected = False
        
        # SSL Configuration
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE
        
    async def connect(self):
        """Connect to the Realtime API via WebSocket"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "OpenAI-Beta": "realtime=v1"
        }
        
        try:
            self.ws = await websockets.connect(
                f"{self.url}?model={self.model}",
                additional_headers=headers,
                ssl=self.ssl_context
            )
            self.is_connected = True
            
            # Configure session for text-only mode
            session_config = {
                "type": "session.update",
                "session": {
                    "modalities": ["text"],
                    "instructions": "You are a helpful assistant that responds to text inputs with text outputs.",
                    "voice": "alloy",
                    "input_audio_format": "pcm16",
                    "output_audio_format": "pcm16",
                    "turn_detection": None,
                    "temperature": 0.7,
                    "max_response_output_tokens": 4096
                }
            }
            
            await self.ws.send(json.dumps(session_config))
            
            # Start listening for responses
            asyncio.create_task(self._listen_for_responses())
            
        except Exception as e:
            st.error(f"Failed to connect to Realtime API: {e}")
            self.is_connected = False
            
    async def _listen_for_responses(self):
        """Listen for responses from the WebSocket"""
        try:
            async for message in self.ws:
                data = json.loads(message)
                await self.response_queue.put(data)
        except Exception as e:
            st.error(f"Error listening to WebSocket: {e}")
            self.is_connected = False
    
    async def send_text_message(self, content, system_prompt=None):
        """Send a text message and get response"""
        if not self.is_connected:
            raise Exception("Not connected to Realtime API")
        
        # Create conversation item
        conversation_item = {
            "type": "conversation.item.create",
            "item": {
                "type": "message",
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": content
                    }
                ]
            }
        }
        
        # Add system message if provided
        if system_prompt:
            system_item = {
                "type": "conversation.item.create",
                "item": {
                    "type": "message",
                    "role": "system",
                    "content": [
                        {
                            "type": "input_text",
                            "text": system_prompt
                        }
                    ]
                }
            }
            await self.ws.send(json.dumps(system_item))
        
        # Send user message
        await self.ws.send(json.dumps(conversation_item))
        
        # Request response
        response_request = {
            "type": "response.create",
            "response": {
                "modalities": ["text"],
                "instructions": "Respond with text only."
            }
        }
        await self.ws.send(json.dumps(response_request))
        
        # Wait for and collect response
        response_text = ""
        while True:
            try:
                response_data = await asyncio.wait_for(self.response_queue.get(), timeout=30.0)
                
                if response_data.get("type") == "response.text.delta":
                    response_text += response_data.get("delta", "")
                elif response_data.get("type") == "response.text.done":
                    response_text += response_data.get("text", "")
                    break
                elif response_data.get("type") == "response.done":
                    break
                elif response_data.get("type") == "error":
                    raise Exception(f"API Error: {response_data.get('error', {}).get('message', 'Unknown error')}")
                    
            except asyncio.TimeoutError:
                raise Exception("Timeout waiting for response")
        
        return response_text.strip()
    
    async def close(self):
        """Close the WebSocket connection"""
        if self.ws:
            await self.ws.close()
            self.is_connected = False

# ========== Modified OpenAI Client Wrapper ==========
class RealtimeOpenAIWrapper:
    """Wrapper to make Realtime API work like the standard OpenAI client"""
    
    def __init__(self, api_key):
        self.api_key = api_key
        self.realtime_client = None
        
    async def _ensure_connected(self):
        """Ensure we have an active connection"""
        if not self.realtime_client or not self.realtime_client.is_connected:
            self.realtime_client = RealtimeTextClient(self.api_key)
            await self.realtime_client.connect()
    
    async def create_completion(self, messages, system_prompt=None, **kwargs):
        """Create a completion using the Realtime API"""
        await self._ensure_connected()
        
        # Extract the user message (simplified for this demo)
        user_message = ""
        if isinstance(messages, list) and len(messages) > 0:
            if messages[-1].get("role") == "user":
                user_message = messages[-1].get("content", "")
        elif isinstance(messages, str):
            user_message = messages
        
        # Send message and get response
        response_text = await self.realtime_client.send_text_message(
            user_message, 
            system_prompt=system_prompt
        )
        
        # Return in the same format as OpenAI client
        return MockResponse(response_text)
    
    async def close(self):
        """Close connections"""
        if self.realtime_client:
            await self.realtime_client.close()

class MockResponse:
    """Mock response object to mimic OpenAI response structure"""
    def __init__(self, content):
        self.choices = [MockChoice(content)]

class MockChoice:
    def __init__(self, content):
        self.message = MockMessage(content)

class MockMessage:
    def __init__(self, content):
        self.content = content

# ========== Async Function Wrappers ==========
async def async_generate_question_for_object(realtime_client, product, object_name, object_description):
    """Async version of generate_question_for_object"""
    prompt = f"""
Generate one natural and complete question about the AP model object "{object_name}" ({object_description}) regarding {product}.
The question should meet the following conditions:
- Natural English as a complete sentence
- A question that investigates specific content related to {product}
- A question that would likely yield good results in a search engine
Output only the question:
"""
    response = await realtime_client.create_completion(prompt, system_prompt=SYSTEM_PROMPT)
    return response.choices[0].message.content.strip()

async def async_generate_question_for_arrow(realtime_client, product, arrow_name, arrow_info):
    """Async version of generate_question_for_arrow"""
    prompt = f"""
Generate a natural and complete question about the AP model arrow "{arrow_name}" regarding {product}.
Arrow details:
- Source: {arrow_info['from']}
- Target: {arrow_info['to']}
- Description: {arrow_info['description']}
The question should meet the following conditions:
- Natural English as a complete sentence
- A question that specifically investigates the transformation relationship from {arrow_info['from']} to {arrow_info['to']}
- A question that can discover specific cases or relationships in {product}
Output only the question:
"""
    response = await realtime_client.create_completion(prompt, system_prompt=SYSTEM_PROMPT)
    return response.choices[0].message.content.strip()

async def async_build_ap_element(realtime_client, product, element_type, element_name, answer):
    """Async version of build_ap_element"""
    if element_type == "object":
        prompt = f"""
Build an AP element for {element_name} of {product} based on the following information:
Information: {answer}
Output in the following JSON format:
{{"type": "{element_name}", "definition": "Specific and concise definition (within 30 words)", "example": "Specific example related to this object"}}
"""
    else:
        arrow_info = AP_MODEL_STRUCTURE["arrows"][element_name]
        prompt = f"""
Build an AP element for {element_name} ({arrow_info['from']} → {arrow_info['to']}) of {product} based on the following information:
Information: {answer}
Output in the following JSON format:
{{"source": "{arrow_info['from']}", "target": "{arrow_info['to']}", "type": "{element_name}", "definition": "Specific explanation of transformation relationship (within 30 words)", "example": "Specific example related to this arrow"}}
"""
    try:
        response = await realtime_client.create_completion(prompt, system_prompt=SYSTEM_PROMPT)
        return json.loads(response.choices[0].message.content.strip())
    except Exception:
        return None

# ========== Fallback to Standard OpenAI Client ==========
try:
    # Try to use Realtime API first, fall back to standard client
    OPENAI_API_KEY = st.secrets["openai"]["api_key"]
    
    # For now, use standard client as primary (since Realtime API is complex to implement in Streamlit)
    client = OpenAI(api_key=OPENAI_API_KEY)
    
    # Initialize Realtime wrapper (will be used in async functions)
    realtime_wrapper = RealtimeOpenAIWrapper(OPENAI_API_KEY)
    
    # Initialize Tavily client
    tavily_client = TavilyClient(api_key=st.secrets["tavily"]["api_key"])
    
except KeyError as e:
    st.error(f"⚠ API key not configured. Please check `{e.args[0]}` in Streamlit settings.")
    st.stop()
except Exception as e:
    st.error(f"⚠ API connection error: {str(e)}")
    st.stop()

# ========== Original Constants (kept the same) ==========
SYSTEM_PROMPT = """You are a science fiction expert who analyzes society based on the "Archaeological Prototyping (AP)" model. Here is an introduction to this model:

AP is a sociocultural model consisting of 18 items (6 objects and 12 arrows). In essence, it is a model that divides society and culture into 18 elements around a specific theme and logically describes their connections.

This model can also be considered as a directed graph. It consists of 6 objects (Avant-garde Social Issues, People's Values, Social Issues, Technology and Resources, Daily Spaces and User Experience, Institutions) and 12 arrows (Media, Community Formation, Cultural Arts Promotion, Standardization, Communication, Organization, Meaning Attribution, Products/Services, Habituation, Paradigm, Business Ecosystem, Art (Social Criticism)) that constitute a generational sociocultural model. The connections between these objects and arrows are defined as follows:

##Objects
1. Avant-garde Social Issues: Social issues caused by paradigms of technology and resources, or social issues that emerge through Art (Social Criticism) regarding daily living spaces and user experiences within them.
2. People's Values: The desired state of people who empathize with avant-garde social issues spread through cultural arts promotion or social issues that cannot be addressed by institutions spread through daily communication. These issues are not recognized by everyone, but only by certain progressive/minority people. Specifically, this includes macro environmental issues (climate, ecology, etc.) and human environmental issues (ethics, economics, hygiene, etc.).
3. Social Issues: Social issues recognized by society through progressive communities addressing avant-garde issues, or social issues constrained by institutions exposed through media. These emerge as targets that should be solved in society.
4. Technology and Resources: Among the institutions created to smoothly function daily routines, these are technologies and resources that are standardized and constrained by the past, and technologies and resources possessed by organizations (for-profit and non-profit corporations, including groups without legal status, regardless of new or existing) organized to solve social issues.
5. Daily Spaces and User Experience: Physical spaces composed of products and services developed by mobilizing technology and resources, and user experiences of using those products and services with meaning attribution based on certain values in those spaces. The relationship between values and user experience is, for example, people with the value "want to become an AI engineer" give meaning to PCs as "tools for learning programming" and have the experience of "programming."
6. Institutions: Institutions created to more smoothly carry out habits that people with certain values perform daily, or institutions created by stakeholders (business ecosystem) who conduct business composing daily spaces and user experiences to conduct business more smoothly. Specifically, this includes laws, guidelines, industry standards, administrative guidance, and morals.

##Arrows
1. Media: Media that reveals contemporary institutional defects. Includes major media such as mass media and internet media, as well as individuals who disseminate information. Converts institutions to social issues. (Institutions -> Social Issues)
2. Community Formation: Communities formed by people who recognize avant-garde issues. Whether official or unofficial does not matter. Converts avant-garde social issues to social issues. (Avant-garde Social Issues -> Social Issues)
3. Cultural Arts Promotion: Activities that exhibit and convey social issues revealed by Art (Social Criticism) as works to people. Converts avant-garde social issues to people's values. (Avant-garde Social Issues -> People's Values)
4. Standardization: Among institutions, standardization of institutions conducted to affect a broader range of stakeholders. Converts institutions to new technology and resources. (Institutions -> Technology and Resources)
5. Communication: Communication means to convey social issues to more people. For example, this is often done through SNS in recent years. Converts social issues to people's values. (Social Issues -> People's Values)
6. Organization: Organizations formed to solve social issues. Regardless of whether they have legal status or are new or old organizations, all organizations that address newly emerged social issues. Converts social issues to new technology and resources. (Social Issues -> Technology and Resources)
7. Meaning Attribution: Reasons why people use products and services based on their values. Converts people's values to new daily spaces and user experiences. (People's Values -> Daily Spaces and User Experience)
8. Products/Services: Products and services created using technology and resources possessed by organizations. Converts technology and resources to daily spaces and user experiences. (Technology and Resources -> Daily Spaces and User Experience)
9. Habituation: Habits that people perform based on their values. Converts people's values to institutions. (People's Values -> Institutions)
10. Paradigm: As dominant technology and resources of an era, these bring influence to the next generation. Converts technology and resources to avant-garde social issues. (Technology and Resources -> Avant-garde Social Issues)
11. Business Ecosystem: Networks formed by stakeholders related to products and services that compose daily spaces and user experiences to maintain them. Converts daily spaces and user experiences to institutions. (Daily Spaces and User Experience -> Institutions)
12. Art (Social Criticism): Beliefs of people who view issues that people don't notice from subjective/intrinsic perspectives. Has the role of feeling discomfort with daily spaces and user experiences and presenting issues. Converts daily spaces and user experiences to avant-garde social issues. (Daily Spaces and User Experience -> Avant-garde Social Issues)

###The S-curve is a model representing the evolution of technology over time. It consists of the following two stages:
##Stage 1: Ferment Period: In this stage, technological development progresses steadily, but its progress is gradual. Focus is mainly on solving existing problems and improving current functions. At the end of this period, current problems are solved while new problems emerge.
##Stage 2: Take-off Period: In this stage, technology enters a rapid growth period. Various innovative ideas are proposed, and they eventually combine to create completely new forms of technology. At the end of this period, technology achieves great development while also causing new problems.
"""

AP_MODEL_STRUCTURE = {
    "objects": {
        "Avant-garde Social Issues": "Social issues caused by paradigms of technology and resources",
        "People's Values": "Values and ideals recognized by progressive people",
        "Social Issues": "Issues recognized and to be solved in society",
        "Technology and Resources": "Technology and resources organized for problem solving",
        "Daily Spaces and User Experience": "Physical spaces and user experiences through products/services",
        "Institutions": "Systems and rules that facilitate habits and business"
    },
    "arrows": {
        "Media": {"from": "Institutions", "to": "Social Issues", "description": "Media exposing institutional defects"},
        "Community Formation": {"from": "Avant-garde Social Issues", "to": "Social Issues", "description": "Communities addressing avant-garde issues"},
        "Cultural Arts Promotion": {"from": "Avant-garde Social Issues", "to": "People's Values", "description": "Exhibition and transmission of issues through art"},
        "Standardization": {"from": "Institutions", "to": "Technology and Resources", "description": "Standardization of institutions into technology/resources"},
        "Communication": {"from": "Social Issues", "to": "People's Values", "description": "Issue transmission via SNS etc."},
        "Organization": {"from": "Social Issues", "to": "Technology and Resources", "description": "Formation of organizations for problem solving"},
        "Meaning Attribution": {"from": "People's Values", "to": "Daily Spaces and User Experience", "description": "Reasons for using products/services based on values"},
        "Products/Services": {"from": "Technology and Resources", "to": "Daily Spaces and User Experience", "description": "Creation of products/services using technology"},
        "Habituation": {"from": "People's Values", "to": "Institutions", "description": "Institutionalization of habits based on values"},
        "Paradigm": {"from": "Technology and Resources", "to": "Avant-garde Social Issues", "description": "New social issues from dominant technology"},
        "Business Ecosystem": {"from": "Daily Spaces and User Experience", "to": "Institutions", "description": "Networks of business stakeholders"},
        "Art (Social Criticism)": {"from": "Daily Spaces and User Experience", "to": "Avant-garde Social Issues", "description": "Presenting issues from discomfort with daily life"}
    }
}

# ========== Helper Functions (kept the same) ==========
def parse_json_response(gpt_output: str) -> dict:
    result_str = gpt_output.strip()
    if result_str.startswith("```") and result_str.endswith("```"):
        result_str = re.sub(r'^```[^\n]*\n', '', result_str)
        result_str = re.sub(r'\n```$', '', result_str)
        result_str = result_str.strip()
    try:
        return json.loads(result_str)
    except Exception as e:
        st.error(f"JSON parsing error: {e}")
        st.error(f"String attempted to parse: {result_str}")
        raise e

# ========== Modified Functions to Support Both APIs ==========
def generate_question_for_object(product: str, object_name: str, object_description: str, use_realtime=False) -> str:
    prompt = f"""
Generate one natural and complete question about the AP model object "{object_name}" ({object_description}) regarding {product}.
The question should meet the following conditions:
- Natural English as a complete sentence
- A question that investigates specific content related to {product}
- A question that would likely yield good results in a search engine
Output only the question:
"""
    
    if use_realtime:
        # This would need to be called from an async context
        # For now, fall back to standard client
        pass
    
    response = client.chat.completions.create(
        model="gpt-4o", 
        messages=[{"role": "user", "content": prompt}], 
        temperature=0
    )
    return response.choices[0].message.content.strip()

def generate_question_for_arrow(product: str, arrow_name: str, arrow_info: dict, use_realtime=False) -> str:
    prompt = f"""
Generate a natural and complete question about the AP model arrow "{arrow_name}" regarding {product}.
Arrow details:
- Source: {arrow_info['from']}
- Target: {arrow_info['to']}
- Description: {arrow_info['description']}
The question should meet the following conditions:
- Natural English as a complete sentence
- A question that specifically investigates the transformation relationship from {arrow_info['from']} to {arrow_info['to']}
- A question that can discover specific cases or relationships in {product}
Output only the question:
"""
    
    if use_realtime:
        # This would need to be called from an async context
        # For now, fall back to standard client
        pass
    
    response = client.chat.completions.create(
        model="gpt-4o", 
        messages=[{"role": "user", "content": prompt}], 
        temperature=0
    )
    return response.choices[0].message.content.strip()

# ========== Async Functions for Realtime API (when available) ==========
async def async_process_element_realtime(product: str, element_type: str, name: str, info: dict):
    """Async version using Realtime API"""
    try:
        if element_type == "object":
            question = await async_generate_question_for_object(realtime_wrapper, product, name, info)
        else:
            question = await async_generate_question_for_arrow(realtime_wrapper, product, name, info)
        
        # Still use Tavily for search
        answer = search_and_get_answer(question)
        if "Search error" in answer or not answer:
            return None, None
        
        element_data = await async_build_ap_element(realtime_wrapper, product, element_type, name, answer)
        if not element_data:
            return None, None
        
        return {"type": element_type, "name": name, "data": element_data}, f"## {name}\n{answer}"
    except Exception as e:
        st.warning(f"Error occurred while processing element '{name}': {e}")
        return None, None

# ========== Search Functions (kept the same) ==========
def search_and_get_answer(question: str) -> str:
    try:
        response = tavily_client.search(query=question, include_answer=True)
        answer = response.get('answer', '')
        if answer: return answer
        results = response.get('results', [])
        return results[0].get('content', "No information found") if results else "No information found"
    except Exception as e: return f"Search error: {str(e)}"

def build_ap_element(product: str, element_type: str, element_name: str, answer: str, use_realtime=False) -> dict:
    if element_type == "object":
        prompt = f"""
Build an AP element for {element_name} of {product} based on the following information:
Information: {answer}
Output in the following JSON format:
{{"type": "{element_name}", "definition": "Specific and concise definition (within 30 words)", "example": "Specific example related to this object"}}
"""
    else:
        arrow_info = AP_MODEL_STRUCTURE["arrows"][element_name]
        prompt = f"""
Build an AP element for {element_name} ({arrow_info['from']} → {arrow_info['to']}) of {product} based on the following information:
Information: {answer}
Output in the following JSON format:
{{"source": "{arrow_info['from']}", "target": "{arrow_info['to']}", "type": "{element_name}", "definition": "Specific explanation of transformation relationship (within 30 words)", "example": "Specific example related to this arrow"}}
"""
    try:
        if use_realtime:
            # Would need async context
            pass
        
        response = client.chat.completions.create(
            model="gpt-4o", 
            messages=[{"role": "user", "content": prompt}], 
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content.strip())
    except Exception: 
        return None

def process_element(product: str, element_type: str, name: str, info: dict, use_realtime=False):
    try:
        if element_type == "object":
            question = generate_question_for_object(product, name, info, use_realtime)
        else:
            question = generate_question_for_arrow(product, name, info, use_realtime)
        answer = search_and_get_answer(question)
        if "Search error" in answer or not answer:
            return None, None
        element_data = build_ap_element(product, element_type, name, answer, use_realtime)
        if not element_data:
            return None, None
        return {"type": element_type, "name": name, "data": element_data}, f"## {name}\n{answer}"
    except Exception as e:
        st.warning(f"Error occurred while processing element '{name}': {e}")
        return None, None

# ========== Rest of the functions remain the same ==========
def build_stage1_ap_with_tavily(product: str, status_container, use_realtime=False):
    ap_model = {"nodes": [], "arrows": []}
    all_answers = []
    MAX_WORKERS = 5
    tasks = []
    for name, desc in AP_MODEL_STRUCTURE["objects"].items():
        tasks.append((product, "object", name, desc, use_realtime))
    for name, info in AP_MODEL_STRUCTURE["arrows"].items():
        tasks.append((product, "arrow", name, info, use_realtime))
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_task = {executor.submit(process_element, *task): task for task in tasks}
        for future in concurrent.futures.as_completed(future_to_task):
            task_name = future_to_task[future][2]
            status_container.write(f"  - Searching element '{task_name}'...")
            result, answer_text = future.result()
            if result:
                if result["type"] == "object": ap_model["nodes"].append(result["data"])
                else: ap_model["arrows"].append(result["data"])
            if answer_text: all_answers.append(answer_text)
    
    status_container.write("Generating introduction...")
    intro_prompt = f"Based on the following information about {product} from various perspectives, create a concise introduction within 50 words in English about what {product} is.\n### Collected Information:\n{''.join(all_answers)}"
    
    if use_realtime:
        # Would need async context
        pass
    
    response = client.chat.completions.create(
        model="gpt-4o", 
        messages=[{"role": "user", "content": intro_prompt}], 
        temperature=0
    )
    introduction = response.choices[0].message.content
    return introduction, ap_model

# ========== Continue with the rest of your original functions ==========
# (I'll keep the remaining functions the same to maintain functionality)

def generate_agents(topic: str, use_realtime=False) -> list:
    prompt = f"""
Generate 2 completely different expert agents for generating AP model elements about the theme "{topic}".
Each agent must have different perspectives and expertise, and be able to provide creative and innovative future predictions.
Output in the following JSON format:
{{ "agents": [ {{ "name": "Agent name", "expertise": "Field of expertise", "personality": "Personality/characteristics", "perspective": "Unique perspective" }} ] }}
"""
    response = client.chat.completions.create(
        model="gpt-4o", 
        messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": prompt}], 
        temperature=1.2, 
        response_format={"type": "json_object"}
    )
    result = parse_json_response(response.choices[0].message.content)
    return result["agents"]

# ========== Continue with remaining functions... ==========
# (Keep all other functions the same for brevity)

# ========== Main UI (add Realtime API option) ==========
st.title("🚀 Near-Future SF Generator (Realtime API Enhanced)")

# Add API selection option
with st.sidebar:
    st.header("API Configuration")
    use_realtime_api = st.checkbox(
        "Use Realtime API (Experimental)", 
        value=False,
        help="Enable this to use OpenAI's new Realtime API. Note: This is experimental and may have limitations."
    )
    
    if use_realtime_api:
        st.warning("⚠️ Realtime API mode is experimental. Some features may not work as expected.")

# ========== Continue with remaining functions ==========
def agent_generate_element(agent: dict, topic: str, element_type: str, previous_stage_ap: dict, user_vision: str, context: dict, use_realtime=False) -> str:
    context_info = ""
    if element_type == "Daily Spaces and User Experience": 
        context_info = f"##New Technology and Resources:\n{context.get('Technology and Resources', '')}"
    elif element_type == "Avant-garde Social Issues": 
        context_info = f"##New Technology and Resources:\n{context.get('Technology and Resources', '')}\n##New Daily Spaces and User Experience:\n{context.get('Daily Spaces and User Experience', '')}"
    
    prompt = f"""
As {agent['name']}, with expertise in {agent['expertise']} and characteristics of {agent['personality']}, analyze from the unique perspective of {agent['perspective']}.
##Theme: {topic}
##Previous stage AP model:
{json.dumps(previous_stage_ap, ensure_ascii=False, indent=2)}
##User's future vision:
{user_vision}
{context_info}
From your expertise and perspective, creatively and innovatively generate content for "{element_type}" in the next stage. Based on S-curve theory, consider development from the previous stage and new possibilities, and provide your unique, outstanding, and imaginative ideas **in text content only, within 50 words. No JSON format or extra explanations needed.**
"""
    response = client.chat.completions.create(
        model="gpt-4o", 
        messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": prompt}], 
        temperature=1.2
    )
    return response.choices[0].message.content.strip()

def judge_element_proposals(proposals: list[dict], element_type: str, topic: str, use_realtime=False) -> dict:
    proposals_text = "".join([f"##Proposal {i+1} (Agent: {p['agent_name']}):\n{p['proposal']}\n\n" for i, p in enumerate(proposals)])
    prompt = f"""
The following are {len(proposals)} proposals for "{element_type}" regarding "{topic}". Evaluate each proposal from the perspectives of creativity and future vision, and select the most imaginative proposal.
{proposals_text}
Output in the following JSON format:
{{ "selected_proposal": "Agent name of selected proposal", "selected_content": "Content of selected {element_type} proposal", "selection_reason": "Selection reason (within 150 words)", "creativity_score": "Creativity evaluation (1-10)", "future_vision_score": "Future vision evaluation (1-10)" }}
"""
    response = client.chat.completions.create(
        model="gpt-4o", 
        messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": prompt}], 
        temperature=1.2, 
        response_format={"type": "json_object"}
    )
    return parse_json_response(response.choices[0].message.content)

def generate_single_element_with_iterations(status_container, topic: str, element_type: str, previous_stage_ap: dict, agents: list, user_vision: str, context: dict, use_realtime=False) -> dict:
    status_container.write(f"    - Generating {len(agents)} agent proposals...")
    proposals = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(agents)) as executor:
        future_to_agent = {executor.submit(agent_generate_element, agent, topic, element_type, previous_stage_ap, user_vision, context, use_realtime): agent for agent in agents}
        for future in concurrent.futures.as_completed(future_to_agent):
            agent = future_to_agent[future]
            try:
                proposal_content = future.result()
                proposals.append({"agent_name": agent['name'], "proposal": proposal_content})
            except Exception as exc: 
                st.warning(f"Error in proposal generation by {agent['name']}: {exc}")
    
    if not proposals:
        return {"element_type": element_type, "error": "No proposals were generated."}
    
    status_container.write(f"    - Evaluating proposals...")
    judgment = judge_element_proposals(proposals, element_type, topic, use_realtime)
    
    return {
        "element_type": element_type, 
        "iteration": {"iteration_number": 1, "all_agent_proposals": proposals, "judgment": judgment},
        "final_decision": {"final_selected_content": judgment["selected_content"], "final_selection_reason": judgment["selection_reason"]}
    }

def build_complete_ap_model(topic: str, previous_ap: dict, new_elements: dict, stage: int, user_vision: str, use_realtime=False) -> dict:
    prompt = f"""
Build the complete AP model for Stage {stage}.
##Previous stage information:
{json.dumps(previous_ap, ensure_ascii=False, indent=2)}
##Newly generated core elements:
Technology and Resources: {new_elements["Technology and Resources"]}
Daily Spaces and User Experience: {new_elements["Daily Spaces and User Experience"]}
Avant-garde Social Issues: {new_elements["Avant-garde Social Issues"]}
##User's future vision:
{user_vision}
**Important**: Stage {stage} must include all of the following 6 objects and 12 arrows:
Objects: Avant-garde Social Issues, People's Values, Social Issues, Technology and Resources, Daily Spaces and User Experience, Institutions
Arrows: Media, Community Formation, Cultural Arts Promotion, Standardization, Communication, Organization, Meaning Attribution, Products/Services, Habituation, Paradigm, Business Ecosystem, Art (Social Criticism)
Center on the newly generated 3 elements, update other elements with content appropriate for Stage {stage}, and build all arrow relationships.
Output in the following JSON format:
{{"nodes": [{{"type": "Object name", "definition": "Description of this object", "example": "Specific example of this object"}}], "arrows": [{{"source": "Source object", "target": "Target object", "type": "Arrow name", "definition": "Description of this arrow", "example": "Specific example of this arrow"}}]}}
"""
    response = client.chat.completions.create(
        model="gpt-4o", 
        messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": prompt}], 
        response_format={"type": "json_object"}
    )
    return parse_json_response(response.choices[0].message.content)

def generate_stage_introduction(topic: str, stage: int, new_elements: dict, user_vision: str, use_realtime=False) -> str:
    prompt = f"""
Create an introduction for Stage {stage} of {topic} based on the following newly generated elements.
##Generated elements:
Technology and Resources: {new_elements["Technology and Resources"]}
Daily Spaces and User Experience: {new_elements["Daily Spaces and User Experience"]}
Avant-garde Social Issues: {new_elements["Avant-garde Social Issues"]}
##User's future vision:
{user_vision}
Create a concise introduction within 50 words in English about what the situation of {topic} in Stage {stage} would be like.
"""
    response = client.chat.completions.create(
        model="gpt-4o", 
        messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": prompt}], 
        temperature=0
    )
    return response.choices[0].message.content.strip()

def generate_outline(theme: str, scene: str, ap_model_history: list, use_realtime=False) -> str:
    prompt = f"""
You are a professional SF writer. Based on the following information, create a synopsis for a short SF novel with the theme "{theme}".
## Story Setting:
{scene}
## Story Background (S-curve Stage 1):
{json.dumps(ap_model_history[0]['ap_model'], ensure_ascii=False, indent=2)}
## Story Development (S-curve Stage 2):
{json.dumps(ap_model_history[1]['ap_model'], ensure_ascii=False, indent=2)}
Based on the above information, create a story synopsis that includes the main plot, characters, and central conflicts unfolding in the specified setting. The synopsis should be innovative and compelling, following the style of SF novels. The story should focus on the transition from Stage 1 to Stage 2.
"""
    response = client.chat.completions.create(
        model="gpt-4o", 
        messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

def generate_story(theme: str, outline: str, use_realtime=False) -> str:
    prompt = f"""
You are a professional SF writer. Based on the following synopsis, write a short SF novel with the theme "{theme}".
## Story Synopsis:
{outline}
Write a coherent story following this synopsis. The story should be innovative, compelling, and follow the SF style. Please write approximately 500 words in English.
"""
    response = client.chat.completions.create(
        model="gpt-4o", 
        messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

# ========== UI Functions for Visualization ==========
def show_visualization(ap_history, height=750):
    """Generate and display visualization HTML based on AP model history"""
    if not ap_history:
        st.warning("No data to visualize.")
        return
    
    html_content = f'''
    <!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><title>AP Model Visualization</title><style>
    body{{font-family:sans-serif;background-color:#f0f2f6;margin:0;padding:20px;}}
    .vis-wrapper{{overflow-x:auto;border:1px solid #ddd;border-radius:10px;background:white;padding-top:20px;}}
    .visualization{{position:relative;width:{len(ap_history)*720}px;height:680px;background:#fafafa;}}
    .node{{position:absolute;width:140px;height:140px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:13px;font-weight:bold;text-align:center;cursor:pointer;transition:all .3s;box-shadow:0 4px 12px rgba(0,0,0,.15);border:3px solid white;line-height:1.2;padding:15px;box-sizing:border-box;}}
    .node:hover{{transform:scale(1.1);z-index:100;}}.node-avant-garde{{background:#ff9999;}}.node-values{{background:#ecba13;}}.node-social{{background:#ffff99;}}.node-technology{{background:#99cc99;}}.node-daily{{background:#99cccc;}}.node-institutions{{background:#9999ff;}}
    .arrow{{position:absolute;height:2px;background:#333;transform-origin:left center;z-index:1;}}
    .arrow::after{{content:'';position:absolute;right:-8px;top:-4px;width:0;height:0;border-left:8px solid #333;border-top:4px solid transparent;border-bottom:4px solid transparent;}}
    .arrow-label{{position:absolute;background:white;padding:2px 8px;border:1px solid #ddd;border-radius:15px;font-size:10px;white-space:nowrap;transform:translate(-50%,-50%);z-index:10;}}
    .dotted-arrow{{border-top:2px dotted #333;background:transparent;}}.dotted-arrow::after{{border-left-color:#333;}}
    .tooltip{{position:absolute;background:rgba(0,0,0,.9);color:white;padding:12px;border-radius:8px;font-size:12px;max-width:300px;z-index:1000;pointer-events:none;opacity:0;transition:opacity .3s;line-height:1.4;}}
    .tooltip.show{{opacity:1;}}
    </style></head><body><div class="vis-wrapper"><div class="visualization" id="visualization"></div></div><div class="tooltip" id="tooltip"></div><script>
    const viz=document.getElementById('visualization'),tooltip=document.getElementById('tooltip');let allNodes={{}};const apData={json.dumps(ap_history,ensure_ascii=False)};
    function getNodeClass(type){{
        const mapping = {{
            'Avant-garde Social Issues': 'avant-garde',
            'People\\'s Values': 'values', 
            'Social Issues': 'social',
            'Technology and Resources': 'technology',
            'Daily Spaces and User Experience': 'daily',
            'Institutions': 'institutions'
        }};
        return mapping[type] || 'default';
    }}
    function getPos(s,t){{const w=700,o=s*w;if(s%2===0){{switch(t){{case'Institutions':return{{x:o+355,y:50}};case'Daily Spaces and User Experience':return{{x:o+180,y:270}};case'Social Issues':return{{x:o+530,y:270}};case'Technology and Resources':return{{x:o+50,y:500}};case'Avant-garde Social Issues':return{{x:o+355,y:500}};case'People\\'s Values':return{{x:o+660,y:500}};default:return null}}}}else{{switch(t){{case'Technology and Resources':return{{x:o+50,y:50}};case'Avant-garde Social Issues':return{{x:o+355,y:50}};case'People\\'s Values':return{{x:o+660,y:50}};case'Daily Spaces and User Experience':return{{x:o+180,y:270}};case'Social Issues':return{{x:o+530,y:270}};case'Institutions':return{{x:o+355,y:500}};default:return null}}}}}}
    function render(){{viz.innerHTML='';allNodes={{}};apData.forEach((s,i)=>{{if(!s.ap_model||!s.ap_model.nodes)return;s.ap_model.nodes.forEach(d=>{{const p=getPos(i,d.type);if(!p)return;const n=document.createElement('div');n.className=`node node-${{getNodeClass(d.type)}}`;n.style.left=p.x+'px';n.style.top=p.y+'px';n.textContent=d.type;const e=d.definition+(d.example?`\\n\\n[Example] `+d.example:"");n.dataset.definition=e.replace(/\\n/g,'<br>');n.dataset.id=`s${{s.stage}}-${{d.type}}`;n.addEventListener('mouseenter',showTip);n.addEventListener('mouseleave',hideTip);viz.appendChild(n);allNodes[n.dataset.id]=n}})}});apData.forEach((s,i)=>{{if(!s.ap_model||!s.ap_model.arrows)return;const next=apData[i+1];s.ap_model.arrows.forEach(a=>{{const isLast=!next,type=a.type,hide=isLast&&['Standardization','Organization','Meaning Attribution','Habituation'].includes(type);if(hide)return;let src=allNodes[`s${{s.stage}}-${{a.source}}`],tgt,isInter=false;if(next&&(type==='Organization'||type==='Standardization')){{tgt=allNodes[`s${{next.stage}}-Technology and Resources`];isInter=!!tgt}}else if(next&&type==='Meaning Attribution'){{tgt=allNodes[`s${{next.stage}}-Daily Spaces and User Experience`];isInter=!!tgt}}else if(next&&type==='Habituation'){{tgt=allNodes[`s${{next.stage}}-Institutions`];isInter=!!tgt}}if(!isInter){{tgt=allNodes[`s${{s.stage}}-${{a.target}}`];}}if(src&&tgt){{const d=type==='Art (Social Criticism)'||type==='Media';createArrow(src,tgt,a,d)}}}})}})}}
    function createArrow(s,t,a,d){{const r=70,p1={{x:parseFloat(s.style.left),y:parseFloat(s.style.top)}},p2={{x:parseFloat(t.style.left),y:parseFloat(t.style.top)}},dx=p2.x+r-(p1.x+r),dy=p2.y+r-(p1.y+r),dist=Math.sqrt(dx*dx+dy*dy),ang=Math.atan2(dy,dx)*180/Math.PI,sx=p1.x+r+dx/dist*r,sy=p1.y+r+dy/dist*r,adjDist=dist-r*2,ar=document.createElement('div');ar.className=d?'arrow dotted-arrow':'arrow';ar.style.left=sx+'px';ar.style.top=sy+'px';ar.style.width=adjDist+'px';ar.style.transform=`rotate(${{ang}}deg)`;const l=document.createElement('div');l.className='arrow-label';l.textContent=a.type;const lx=sx+dx/dist*adjDist/2,ly=sy+dy/dist*adjDist/2;l.style.left=lx+'px';l.style.top=ly+'px';const e=a.definition+(a.example?`\\n\\n[Example] `+a.example:"");l.dataset.definition=e.replace(/\\n/g,'<br>');l.addEventListener('mouseenter',showTip);l.addEventListener('mouseleave',hideTip);viz.appendChild(ar);viz.appendChild(l)}}
    function showTip(e){{const d=e.target.dataset.definition;if(d){{tooltip.innerHTML=d;tooltip.style.left=e.pageX+15+'px';tooltip.style.top=e.pageY-10+'px';tooltip.classList.add('show')}}}}
    function hideTip(){{tooltip.classList.remove('show')}}
    render();
    </script></body></html>'''
    st.components.v1.html(html_content, height=height, scrolling=True)

def show_agent_proposals(element_result):
    """Display multi-agent proposal results nicely"""
    st.markdown(f"#### 🧠 Generation Process for '{element_result['element_type']}'")
    
    iteration = element_result['iteration']
    st.markdown(f"##### Agent Proposals")
    
    st.markdown("###### 🤖 Proposals from Each Agent")
    cols = st.columns(len(iteration['all_agent_proposals']))
    for i, proposal in enumerate(iteration['all_agent_proposals']):
        with cols[i]:
            st.markdown(f"**{proposal['agent_name']}**")
            st.info(proposal['proposal'])
    
    st.markdown("###### 🎯 Judgment Result")
    judgment = iteration['judgment']
    st.success(f"**Selected Proposal:** {judgment['selected_proposal']}")
    st.write(f"**Selected Content:** {judgment['selected_content']}")
    st.write(f"**Selection Reason:** {judgment['selection_reason']}")

# ========== Main UI & State Management ==========
st.title("🚀 Near-Future SF Generator (Realtime API Enhanced)")

# Add API selection option
with st.sidebar:
    st.header("API Configuration")
    use_realtime_api = st.checkbox(
        "Use Realtime API (Experimental)", 
        value=False,
        key="realtime_api_toggle",
        help="Enable this to use OpenAI's new Realtime API. Note: This is experimental and may have limitations."
    )
    
    if use_realtime_api:
        st.warning("⚠️ Realtime API mode is experimental. Some features may not work as expected.")
        st.info("💡 The Realtime API is optimized for voice interactions. For text-based generation like this app, the standard API may be more reliable.")

# Session State Initialization
if 'process_started' not in st.session_state:
    st.session_state.process_started = False
    st.session_state.topic = ""
    st.session_state.scene = ""
    st.session_state.ap_history = []
    st.session_state.descriptions = []
    st.session_state.story = ""
    st.session_state.agents = []
    st.session_state.stage_elements_results = {'stage2': []}

# STEP 0: Initial Input Screen
if not st.session_state.process_started:
    st.markdown("Enter the **theme** you want to explore and the **setting** for the story. AI will predict the future in 2 stages and automatically generate an SF novel to completion.")
    
    st.markdown("### 📝 Content Configuration")
    topic_input = st.text_input("Enter the theme you want to explore", placeholder="e.g., AI, autonomous driving, quantum computing")
    scene_input = st.text_area("Describe the story scenario in detail", placeholder="e.g., A futuristic city at sunset, a quantum research lab")

    if st.button("Start AP & Story Generation →", type="primary", disabled=not topic_input or not scene_input):
        st.session_state.topic = topic_input
        st.session_state.scene = scene_input
        st.session_state.process_started = True
        st.rerun()

# Fully Automated Execution Process
else:
    st.header(f"Theme: {st.session_state.topic}")
    user_vision = f"Imagine the future development of '{st.session_state.topic}' through technological evolution."

    # Display Areas: Always show existing data
    # Stage 1 Display
    if len(st.session_state.ap_history) >= 1:
        st.markdown("---")
        st.header("Stage 1: Ferment Period (Current Analysis)")
        st.info(st.session_state.descriptions[0])
        show_visualization(st.session_state.ap_history[0:1])

    # Stage 2 Display
    if st.session_state.agents:
        st.markdown("---")
        st.header("Stage 2: Take-off Period (Development Prediction)")
        st.subheader("🤖 Expert AI Agent Team")
        with st.expander("View Generated Agents", expanded=True):
            cols = st.columns(len(st.session_state.agents))
            for i, agent in enumerate(st.session_state.agents):
                with cols[i]:
                    st.markdown(f"**{agent['name']}**")
                    st.write(f"**Expertise:** {agent['expertise']}")
                    st.write(f"**Personality:** {agent['personality']}")
                    st.write(f"**Perspective:** {agent['perspective']}")
    
    if st.session_state.stage_elements_results['stage2']:
        for result in st.session_state.stage_elements_results['stage2']:
            show_agent_proposals(result)

    if len(st.session_state.ap_history) >= 2:
        st.info(st.session_state.descriptions[1])
        show_visualization(st.session_state.ap_history)

    # Story Display
    if st.session_state.story:
        st.markdown("---")
        st.header("🎉 Generation Results")
        st.markdown(f"**Scene Setting:** {st.session_state.scene}")
        st.markdown("### 📚 Generated SF Short Story")
        st.text_area("SF Story", st.session_state.story, height=400)
        
        with st.expander("📈 View Summary of 2-Stage Future Predictions"):
            stages_info = ["Stage 1: Ferment Period", "Stage 2: Take-off Period"]
            for i, stage_name in enumerate(stages_info):
                st.markdown(f"**{stage_name}**")
                st.info(st.session_state.descriptions[i])
    
    # Generation Logic: Check data existence and generate if missing
    # Stage 1 Generation
    if len(st.session_state.ap_history) == 0:
        with st.status("Stage 1: Building AP model with web information collection via Tavily...", expanded=True) as status:
            intro1, model1 = build_stage1_ap_with_tavily(st.session_state.topic, status, use_realtime_api)
            st.session_state.descriptions.append(intro1)
            st.session_state.ap_history.append({"stage": 1, "ap_model": model1})
        st.rerun()
        
    # Stage 2 Generation (Step by Step)
    elif len(st.session_state.ap_history) == 1:
        # Agent Generation
        if not st.session_state.agents:
            with st.spinner("Generating expert AI agents for analysis..."):
                st.session_state.agents = generate_agents(st.session_state.topic, use_realtime_api)
            st.rerun()
        
        # Element Generation
        s2_results = st.session_state.stage_elements_results['stage2']
        element_sequence = ["Technology and Resources", "Daily Spaces and User Experience", "Avant-garde Social Issues"]
        if len(s2_results) < len(element_sequence):
            elem_type = element_sequence[len(s2_results)]
            with st.status(f"Stage 2: Generating '{elem_type}'...", expanded=True) as status:
                context = {r['element_type']: r['final_decision']['final_selected_content'] for r in s2_results}
                result = generate_single_element_with_iterations(status, st.session_state.topic, elem_type, st.session_state.ap_history[0]['ap_model'], st.session_state.agents, user_vision, context, use_realtime_api)
                s2_results.append(result)
            st.rerun()

        # Build Complete AP Model
        else:
            with st.status("Stage 2: Building complete AP model...", expanded=True) as status:
                context = {r['element_type']: r['final_decision']['final_selected_content'] for r in s2_results}
                status.update(label="Stage 2: Building complete AP model...")
                model2 = build_complete_ap_model(st.session_state.topic, st.session_state.ap_history[0]['ap_model'], context, 2, user_vision, use_realtime_api)
                status.update(label="Stage 2: Generating introduction...")
                intro2 = generate_stage_introduction(st.session_state.topic, 2, context, user_vision, use_realtime_api)
                st.session_state.descriptions.append(intro2)
                st.session_state.ap_history.append({"stage": 2, "ap_model": model2})
            st.rerun()

    # Story Generation
    elif len(st.session_state.ap_history) == 2 and not st.session_state.story:
        with st.spinner("Final stage: Generating SF story synopsis..."):
            outline = generate_outline(st.session_state.topic, st.session_state.scene, st.session_state.ap_history, use_realtime_api)
        with st.spinner("Final stage: Generating SF short story from synopsis..."):
            story = generate_story(st.session_state.topic, outline, use_realtime_api)
            st.session_state.story = story
        st.success("✅ All generation processes completed!")
        time.sleep(1)
        st.rerun()
        
    # Final Page Action Buttons
    if st.session_state.story:
        st.markdown("---")
        st.subheader("Actions")
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                label="📥 Download SF Story (.txt)",
                data=st.session_state.story,
                file_name=f"sf_story_{st.session_state.topic}.txt",
                mime="text/plain"
            )
        with col2:
            ap_json = json.dumps(st.session_state.ap_history, ensure_ascii=False, indent=2)
            st.download_button(
                label="📥 Download AP Model (JSON)",
                data=ap_json,
                file_name=f"ap_model_{st.session_state.topic}.json",
                mime="application/json"
            )

    # Reset Button
    st.markdown("---")
    if st.button("🔄 Generate with New Theme"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()