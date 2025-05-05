import streamlit as st
import base64
from openai import OpenAI
import pathlib
from pydantic import BaseModel
from PIL import Image
import json
import io
import os
import time

# Initialize OpenAI client with your API key
client = OpenAI()

# Title and description
st.title("🚀 Near Future SF Generator")
st.markdown("""
This application generates a 3-stage evolutionary timeline and science fiction story based on the technology product you're interested in.
Please upload a product image and fill in the relevant information.
""")

# Sidebar for inputs
with st.sidebar:
    st.header("Input Information")
    
    # Product input
    product = st.text_input("Tell me your interest product.", placeholder="e.g., Smartphone")
    
    # User experience input
    user_experience = st.text_area("Why do you think this product is good?", 
                                   placeholder="e.g., It allows me talk with my parents from anywhere in the world.",
                                   height=100)
    
    # Avant-garde issue input
    avant_garde_issue = st.text_area("Is there any problem that you think is not good enough?", 
                                     placeholder="e.g., People spend too much time on it.",
                                     height=100)
    
    # Image upload
    uploaded_file = st.file_uploader("Upload Product Image", type=['png', 'jpg', 'jpeg'])
    
    # Generate button
    generate_button = st.button("🔮 Generate Story", type="primary")

# Helper functions
def resize_image(img):
    max_size = 500
    width, height = img.size
    
    if width > max_size or height > max_size:
        scale = min(max_size / width, max_size / height)
        new_size = (int(width * scale), int(height * scale))
        img = img.resize(new_size, Image.Resampling.LANCZOS)
    return img

def encode_image(img):
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode("utf-8")

# Prompts from your code
SYSTEM_PROMPT = """You are an expert of science fictionist. You analyze the society based on the Archaeological Prototyping(AP) model. Here is the introduction about this model:
AP is a sociocultural model composed of 18 items (6 objects and 12 paths). In essence, it's a model that divides society and culture into these 18 elements and logically depicts their connections.
The 6 objects are:
1. Avant-garde social issues: Social issues caused by paradigms of technology and resources, and the everyday spaces and user experiences shaped by them, are made visible through art (social critisim).
2. Human's value: The desired state of people who empathize with avant-garde social issues disseminated through cultural and artistic promotion, as well as with social issues that cannot be addressed by existing systems and are spread through everyday communication. These issues are not recognized by everyone, but only by a certain group of progressive or minority individuals. Specifically, they include macro-level environmental issues (such as climate and ecology) and human-centered environmental issues (such as ethics, economics, and public health).
3. Social Issue: Social issues that are brought to public awareness by progressive communities tackling avant-garde problems, as well as systemic issues exposed through the media. These issues become visible as targets that society must address.
4. Technology and resource: Technologies and resources that have been standardized and constrained by the past, created to ensure the smooth functioning of everyday routines. These include those held by organizations—whether for-profit, non-profit, incorporated, or unincorporated, new or existing—that are structured to solve social issues.
5. User experiences: A physical space composed of products and services developed through the mobilization of technologies and resources. Within this space, users assign meaning to these products and services based on certain values, and engage in experiences through their use. The relationship between values and user experience can be illustrated, for example, by people who hold the value of "wanting to become an AI engineer" interpreting a PC as "a tool for learning programming" and thereby engaging in the experience of "programming."
6. System: Systems created to facilitate the routines practiced by people who hold certain values, as well as systems established to enable stakeholders involved in businesses that shape everyday spaces and user experiences (i.e., the business ecosystem) to operate more smoothly. Specifically, these include laws, guidelines, industry standards, administrative guidance, and moral codes.

The 12 paths are:
1. Media: Media that reveal the institutional shortcomings of modern society. This includes not only mainstream media such as mass media and online media, but also individuals who disseminate information. These actors play a role in transforming institutional issues into social issues.
2. Communization: Communities formed by individuals who recognize avant-garde issues, regardless of whether they are formal or informal. These communities play a role in transforming underlying issues into social issues.
3. Culture art revitalization: Activities that present social issues made visible through art (as social critique) in the form of artworks and communicate them to the public. These activities serve to transform avant-garde issues into values held by individuals.
4. Standardization: Standardization of systems that is carried out to influence a wider range of stakeholders within the system. Converting systems into technology and resources.
5. Communication: Communication means for conveying social issues to more people. For example, in recent years this is often done through social media. Converting social issues into people's value systems.
6. Organization: Organizations formed to solve social issues. This includes all organizations tackling newly emerged social problems, regardless of whether they have legal status or are new or established organizations. Converting social issues into technology and resources.
7. Meaning-making: The reason people use products and services based on their values. Converting people's values into everyday spaces and user experiences.
8. Products and Services: Products and services created using the technology and resources possessed by an organization. Converting technology and resources into everyday spaces and user experiences.
9. Habituation: Habits that people perform based on their values. Converting values into systems.
10. Paradigm: Something that serves as a dominant technology or resource of an era and has influence on the next generation. Converting technology and resources into avant-garde issues.
11. Business Ecosystem: A network formed by stakeholders involved in products and services that constitute and maintain everyday spaces and user experiences. Converting everyday spaces and user experiences into systems.
12. Art (Social Critique): A person's belief that views problems that people are unaware of from a subjective/intrinsic perspective. It has the role of feeling discomfort with everyday spaces and user experiences and presenting problems. Converting everyday spaces and user experiences into avant-garde issues."""

def generate_description(product):
    return f"""
Here is the image of {product}. Please generate a description of this product, such as appearance or function. Less than 100 words.
"""

def build_background(product, user_experience, avant_garde_issue):
    return f"""
Here are some known information about the objects and paths that are related to the AP model: the product is {product}, which is also shown in the image, the user experience is {user_experience}, the avant-garde issue is {avant_garde_issue}.
Please analyze and generate the other objects and paths that are related to the AP model. Only output the objects and paths.
"""

def update_description(product, description, background, step):
    return f"""
This is {product}. Analyze the technological evolution path of it.
Please base the analysis on the S-curve model and predict the key developments at the following steps:

Step 1: Ferment period: In this step, technological development progresses steadily, focusing mainly on solving existing problems and improving current functionalities.
Step 2: Take-off period: In this step, technology enters a period of rapid development. People propose various innovative ideas, which are eventually combined to form entirely new forms of technology.
Step 3: Maturity period: In this step, technological development slows down again. The new forms of technology bring new problems, which people continue to address while refining the current technologies.

Now the product is in step {step}. Here is the current description of it: {description}.
Also, here is the background of it based on AP model:
{background}
Now please generate the new description of the product at the next step, such as appearance or function. Less than 100 words.
"""

def update_background(product, background, description):
    return f"""
Here is the evolution step of {product} and the related information based on AP model:
{background}
Now move to next step, and the {product} has evolved. The new description of it is {description}.
Please generate the new background of {product} based on AP model. Imagine if problems are solved? How do them solved? Are there any new problems are realized? Only output the objects and paths.
"""

def generate_story(product, bg_history, description_history):
    backgrounds = "\n".join([f"Step {item['step']}: {item['background']}" for item in bg_history])
    descriptions = "\n".join([f"Step {item['step']}: {item['description']}" for item in description_history])
    
    return f"""
Now you need to generate an interesting short science fiction. The topic is about {product}.
Here is the description of this product in 3 development steps:
{descriptions}
Here is the background settings based on AP model in 3 development steps:
{backgrounds}
Your story should be no more than 500 words.
"""

# Main content area
if generate_button and product and user_experience and avant_garde_issue and uploaded_file:
    # Initialize containers for each step
    initial_container = st.container()
    step1_container = st.container()
    step2_container = st.container()
    step3_container = st.container()
    final_container = st.container()
    
    with initial_container:
        # Save uploaded image temporarily
        with st.spinner("Processing image..."):
            # Read uploaded file
            image = Image.open(uploaded_file)
            
            # Resize image
            resized_image = resize_image(image)
            
            # Convert to base64
            img_base64 = encode_image(resized_image)
            
            # Display input image
            st.subheader("Input Image")
            st.image(resized_image, caption=f"{product} - Current State", use_container_width=True)
    
    # Create placeholder for progress
    progress_placeholder = st.empty()
    progress_bar = progress_placeholder.progress(0)
    status_text = st.empty()
    
    # Storage for history
    bg_history = []
    description_history = []
    
    with step1_container:
        # Step 1: Generate initial description
        status_text.text("Analyzing current product...")
        
        prompt = generate_description(product)
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{img_base64}",
                            }
                        },
                    ],
                }
            ]
        )
        initial_description = completion.choices[0].message.content
        
        # Store initial description
        description_history.append({
            "step": 1,
            "description": initial_description
        })
        
        progress_bar.progress(0.15)
        
        # Generate initial background
        status_text.text("Creating initial societal background based on AP model...")
        
        user_prompt = build_background(product, user_experience, avant_garde_issue)
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{img_base64}",
                            }
                        },
                    ],
                }
            ]
        )
        initial_background = completion.choices[0].message.content
        
        # Store initial background
        bg_history.append({
            "step": 1,
            "background": initial_background
        })
        
        progress_bar.progress(0.3)
        
        # Display Stage 1
        st.subheader("🌱 Stage 1: Ferment Period")
        with st.expander("View Stage 1 Details", expanded=False):
            st.markdown("**Current Description:**")
            st.markdown(initial_description)
            st.markdown("**AP Model Background:**")
            st.markdown(initial_background)
    
    with step2_container:
        # Step 2: Update description
        status_text.text("Evolving to Take-off period...")
        
        prompt = update_description(product, description_history[0]['description'], bg_history[0]['background'], 1)
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ]
        )
        second_description = completion.choices[0].message.content
        
        # Store second description
        description_history.append({
            "step": 2,
            "description": second_description
        })
        
        progress_bar.progress(0.45)
        
        # Update background
        status_text.text("Updating societal background based on AP model...")
        
        prompt = update_background(product, bg_history[0]['background'], second_description)
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ]
        )
        second_background = completion.choices[0].message.content
        
        # Store second background
        bg_history.append({
            "step": 2,
            "background": second_background
        })
        
        progress_bar.progress(0.6)
        
        # Display Stage 2
        st.subheader("🚀 Stage 2: Take-off Period")
        with st.expander("View Stage 2 Details", expanded=False):
            st.markdown("**Updated Description:**")
            st.markdown(second_description)
            st.markdown("**AP Model Background Changes:**")
            st.markdown(second_background)
    
    with step3_container:
        # Step 3: Update description
        status_text.text("Evolving to Maturity period...")
        
        prompt = update_description(product, description_history[1]['description'], bg_history[1]['background'], 2)
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ]
        )
        third_description = completion.choices[0].message.content
        
        # Store third description
        description_history.append({
            "step": 3,
            "description": third_description
        })
        
        progress_bar.progress(0.75)
        
        # Update background
        status_text.text("Finalizing societal background based on AP model...")
        
        prompt = update_background(product, bg_history[1]['background'], third_description)
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ]
        )
        third_background = completion.choices[0].message.content
        
        # Store third background
        bg_history.append({
            "step": 3,
            "background": third_background
        })
        
        progress_bar.progress(0.85)
        
        # Display Stage 3
        st.subheader("🏆 Stage 3: Maturity Period")
        with st.expander("View Stage 3 Details", expanded=False):
            st.markdown("**Final Description:**")
            st.markdown(third_description)
            st.markdown("**AP Model Background Changes:**")
            st.markdown(third_background)
    
    with final_container:
        # Generate science fiction story
        status_text.text("⏳ Creating science fiction story... This may take a moment.")
        
        story_prompt = generate_story(product, bg_history, description_history)
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": story_prompt}
            ]
        )
        story = completion.choices[0].message.content
        
        progress_bar.progress(0.9)
        
        # Generate story cover
        status_text.text("Generating story cover... This may take a moment.")
        
        cover_img = client.images.generate(
            model="gpt-image-1",
            prompt=f"Draw a cover for the short story about the evolution of {product}: {story}",
            size="1024x1024",
            quality="low"
        )
        cover_image_bytes = base64.b64decode(cover_img.data[0].b64_json)
        cover_image = Image.open(io.BytesIO(cover_image_bytes))
        
        progress_bar.progress(1.0)
        status_text.text("✅ Generation complete!")
        time.sleep(0.5)
        progress_placeholder.empty()
        status_text.empty()
        
        # Display story and cover
        st.subheader("📚 Science Fiction Story")
        col1, col2 = st.columns([1, 2])
        with col1:
            st.image(cover_image, caption="Story Cover", use_container_width=True)
        with col2:
            st.markdown("**Story Text:**")
            st.markdown(story)
        
        # Download buttons
        st.subheader("Download Options")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            # Download background history JSON
            bg_json = json.dumps(bg_history, ensure_ascii=False, indent=2)
            st.download_button(
                label="📥 Download AP Model JSON",
                data=bg_json,
                file_name="background_history.json",
                mime="application/json"
            )
        
        with col2:
            # Download description history JSON
            desc_json = json.dumps(description_history, ensure_ascii=False, indent=2)
            st.download_button(
                label="📥 Download Descriptions JSON",
                data=desc_json,
                file_name="description_history.json",
                mime="application/json"
            )
        
        with col3:
            # Download story
            st.download_button(
                label="📥 Download Story",
                data=story,
                file_name="story.txt",
                mime="text/plain"
            )
        
        with col4:
            # Download cover image
            buffered = io.BytesIO()
            cover_image.save(buffered, format="PNG")
            st.download_button(
                label="📥 Download Cover Image",
                data=buffered.getvalue(),
                file_name="cover.png",
                mime="image/png"
            )
        
        st.success("✨ Generation Complete! Your science fiction evolution story is ready.")

else:
    # Show instructions when not running
    st.subheader("Instructions")
    st.markdown("""
    1. Fill in the left panel input fields:
       - Product Name
       - User Experience Description
       - Avant-garde Issue (potential problems)
    2. Upload a product image
    3. Click "Generate Evolution Story" button
    4. Wait for processing to complete and download results
    """)
    
    # Show example
    st.subheader("Example")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        **Product Name:** AR Glasses
        
        **User Experience:**  
        Wearing AR glasses provides me with contextual information about my surroundings, enhancing my daily interactions with real-time translations and navigation.
        
        **Avant-garde Issue:**  
        The glasses raise concerns about continuous surveillance, privacy violations, and creating social divides between users and non-users.
        """)
    with col2:
        st.info("Upload an image of AR glasses, and the AI will generate a 3-stage evolution timeline and science fiction story based on this information.")

# Sidebar footer
st.sidebar.markdown("---")
st.sidebar.markdown("Made with ❤️ using Streamlit")