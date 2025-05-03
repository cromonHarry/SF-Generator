import streamlit as st
import base64
from openai import OpenAI
import pathlib
from pydantic import BaseModel
from PIL import Image
import json
import io
import os
    
# Initialize OpenAI client with your API key
client = OpenAI()

# Pydantic models
class Timeline(BaseModel):
    year: int
    description: str

class Evolution(BaseModel):
    steps: list[Timeline]

# Title and description
st.title("🚀 Near Future SF Generator")
st.markdown("""
This application generates a science fiction story based on the technology product you're interested in.
Please upload a product image and fill in the relevant information.
""")

# Sidebar for inputs
with st.sidebar:
    st.header("Input Information")
    
    # Product input
    product = st.text_input("Product Name", placeholder="e.g., Smartphone")
    
    # User experience input
    user_experience = st.text_area("Your Experience", 
                                   placeholder="Describe the positive feelings when using this product...",
                                   height=100)
    
    # Avant-garde issue input
    avant_garde_issue = st.text_area("Potential Issue", 
                                     placeholder="Describe potential problems this product might bring...",
                                     height=100)
    
    # Image upload
    uploaded_file = st.file_uploader("Upload Product Image", type=['png', 'jpg', 'jpeg'])
    
    # Generate button
    generate_button = st.button("🔮 Generate Timeline and Story", type="primary")

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

def s_curve_description(product):
    return f"""We all know {product}. Analyze the technological evolution path of it from now, which is 2025 to 2050.
Please base the analysis on the S-curve model and predict the key developments at the following points in step:
1. 2030 (5 years later than current time)
2. 2035
3. 2040
4. 2045
5. 2050
For each step, provide a description of this technology, including the key developments, breakthroughs, and potential challenges."""

def build_background(product, user_experience, avant_garde_issue):
    return f"""
Here are some known information about the objects and paths that are related to the AP model: the product is {product}, which is also shown in the image, the user experience is {user_experience}, the avant-garde issue is {avant_garde_issue}.
Please analyze and generate the other objects and paths that are related to the AP model. Only output the objects and paths.
"""

def update_background(product, background, description):
    return f"""
Here is the evolution step of {product} and the related information based on AP model:
{background}
Now 5 years has passed, and the {product} has evolved. The new description is {description}.
Please generate the new background of {product} based on AP model. Imagine if problems are solved? How do them solved? Are there any new problems are realized? Only output the objects and paths.
"""

def generate_story(background, product):
    return f"""
Now you need to generate an interesting short science fiction. The topic is about {product}.
Here is the background settings based on AP model:
{background}
Your story should be no more than 500 words.
"""

# Main content area
if generate_button and product and user_experience and avant_garde_issue and uploaded_file:
    
    # Save uploaded image temporarily
    with st.spinner("Processing..."):
        # Read uploaded file
        image = Image.open(uploaded_file)
        
        # Resize image
        resized_image = resize_image(image)
        
        # Convert to base64
        img_base64 = encode_image(resized_image)
        
        # Display input image
        st.subheader("Input Image")
        st.image(resized_image, caption=f"{product} - Current State", use_container_width=True)
        
        # Generate evolution timeline using S-curve model
        with st.spinner("Analyzing technology evolution path..."):
            prompt = s_curve_description(product)
            completion = client.beta.chat.completions.parse(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert in technology forecasting and futurism, specializing in analyzing technology evolution paths."},
                    {"role": "user", "content": prompt}
                ],
                response_format=Evolution,
            )
            steps = completion.choices[0].message.parsed.steps
        
        # Generate AP model background for each timeline step
        SYSTEM_PROMPT = f"""You are an expert of science fictionist. You analyze the society based on the Archaeological Prototyping(AP) model. Here is the introduction about this model:
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
        
        history = []
        
        # Initial background generation
        with st.spinner("Generating initial background..."):
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
            
            temp = {
                "year": 2025,
                "background": completion.choices[0].message.content
            }
            history.append(temp)
        
        # Generate backgrounds for each timeline step
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, step in enumerate(steps):
            progress = (i + 1) / len(steps)
            progress_bar.progress(progress)
            status_text.text(f"Generating {step.year} background...")
            
            user_prompt = update_background(product, history[i]['background'], step.description)
            completion = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ]
            )
            
            temp = {
                "year": step.year,
                "background": completion.choices[0].message.content
            }
            history.append(temp)
        
        progress_bar.progress(1.0)
        status_text.text("Background generation complete!")
        
        # Display timeline
        st.subheader("📅 Future Development Timeline")
        for i, step in enumerate(steps):
            with st.expander(f"{step.year}", expanded=i == 0):
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.markdown(f"**Technology Description:**\n{step.description}")
                with col2:
                    st.markdown(f"**Year:** {step.year}")
                    st.markdown(f"**From Now:** {step.year - 2025} years")
                
                if i > 0:
                    st.markdown("**AP Model Background Changes:**")
                    st.markdown(history[i+1]['background'])
        
        # Generate science fiction story
        with st.spinner("Creating science fiction story..."):
            status_text = st.empty()
            status_text.markdown("**⏳ Generating science fiction story... This may take a moment.**")
            
            story_prompt = generate_story(history[-1]['background'], product)
            completion = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": story_prompt}
                ]
            )
            story = completion.choices[0].message.content
            status_text.markdown("**✅ Story generation complete!**")
        
        # Generate story cover
        with st.spinner("Generating story cover... This may take a moment."):
            cover_img = client.images.generate(
                model="gpt-image-1",
                prompt=f"Draw a cover for the short story: {story}",
                size="1024x1024",
                quality="low"
            )
            cover_image_bytes = base64.b64decode(cover_img.data[0].b64_json)
            cover_image = Image.open(io.BytesIO(cover_image_bytes))
        
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
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Download timeline JSON
            timeline_json = json.dumps(history, ensure_ascii=False, indent=2)
            st.download_button(
                label="📥 Download Timeline JSON",
                data=timeline_json,
                file_name="timeline.json",
                mime="application/json"
            )
        
        with col2:
            # Download story
            st.download_button(
                label="📥 Download Story",
                data=story,
                file_name="story.txt",
                mime="text/plain"
            )
        
        with col3:
            # Download cover image
            buffered = io.BytesIO()
            cover_image.save(buffered, format="PNG")
            st.download_button(
                label="📥 Download Cover Image",
                data=buffered.getvalue(),
                file_name="cover.png",
                mime="image/png"
            )
        
        st.success("✨ Generation Complete!")

else:
    # Show instructions when not running
    st.subheader("Instructions")
    st.markdown("""
    1. Fill in the left panel input fields:
       - Product Name
       - User Experience Description
       - Avant-garde Issue (potential problems)
    2. Upload a product image
    3. Click "Generate Timeline and Story" button
    4. Wait for processing to complete and download results
    """)
    
    # Show example
    st.subheader("Example")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        **Product Name:** Smart Glasses
        
        **User Experience:**  
        Wearing smart glasses allows real-time translation of conversations, augmented reality navigation, making my travels more relaxed and comfortable.
        
        **Avant-garde Issue:**  
        May lead to over-dependence on technology, reduced genuine human interaction, and privacy violation risks.
        """)
    with col2:
        st.info("Upload an image of smart glasses. AI will generate a 25-year development timeline and science fiction story based on this information.")

# Sidebar footer
st.sidebar.markdown("---")
st.sidebar.markdown("Made with ❤️ using Streamlit")