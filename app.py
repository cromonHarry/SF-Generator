import streamlit as st
import base64
from openai import OpenAI
from PIL import Image
import json
import io
import os
import time

client = OpenAI(api_key=st.secrets["openai"]["api_key"])

# Title and description
st.title("🚀 Near Future SF Generator")
st.markdown("""
This application generates a 3-stage evolutionary timeline and science fiction story based on the technology product you're interested in.
Please upload a product image and fill in the relevant information.
""")

# Initialize session state to store generated data
if 'generated' not in st.session_state:
    st.session_state.generated = False
if 'bg_history' not in st.session_state:
    st.session_state.bg_history = []
if 'description_history' not in st.session_state:
    st.session_state.description_history = []
if 'story' not in st.session_state:
    st.session_state.story = ""
if 'image_data' not in st.session_state:
    st.session_state.image_data = []
if 'cover_image_data' not in st.session_state:
    st.session_state.cover_image_data = None
if 'demo_clicked' not in st.session_state:
    st.session_state.demo_clicked = False

# Sidebar for inputs
with st.sidebar:
    st.header("Input Information")
    
    # Add demo button at the top of sidebar
    st.info("Limited API usage available. Try the demo first!")
    demo_button = st.button("🎮 Generate Demo", help="Click this to show the example story about smartphone", type="primary")
    
    if demo_button:
        st.session_state.demo_clicked = True
    
    # Product input
    product = st.text_input("Tell me your interest product.", 
                           value="Smartphone" if st.session_state.demo_clicked else "",
                           placeholder="e.g., Smartphone")
    
    # User experience input
    user_experience = st.text_area("Why do you think this product is good?", 
                                  value="It allows me talk with my parents from anywhere in the world." if st.session_state.demo_clicked else "",
                                  placeholder="e.g., It allows me talk with my parents from anywhere in the world.",
                                  height=100)
    
    # Avant-garde issue input
    avant_garde_issue = st.text_area("Is there any problem that you think is not good enough?", 
                                    value="People spend too much time on it." if st.session_state.demo_clicked else "",
                                    placeholder="e.g., People spend too much time on it.",
                                    height=100)
    
    # Image upload
    uploaded_file = st.file_uploader("Upload Product Image", type=['png', 'jpg', 'jpeg'])
    
    # Load demo image when demo button is clicked
    if st.session_state.demo_clicked and not uploaded_file:
        try:
            # Try to open the demo image from the root directory
            demo_image = open("smartphone_demo.png", "rb")
            uploaded_file = demo_image
        except FileNotFoundError:
            st.error("Demo image not found. Please upload an image manually.")
    
    # Generate button
    generate_button = st.button("🔮 Generate Story", type="primary")
    
    # Auto-click generate button if demo mode is active and all fields are filled
    if st.session_state.demo_clicked and product and user_experience and avant_garde_issue and uploaded_file and not st.session_state.generated:
        generate_button = True

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

def save_temp_image(img):
    """Save a PIL Image to a temporary file and return the file path"""
    temp_file = "temp_image.png"
    img.save(temp_file, format="PNG")
    return temp_file

def get_image_bytes(pil_img):
    """Convert PIL image to bytes for download button"""
    buffered = io.BytesIO()
    pil_img.save(buffered, format="PNG")
    return buffered.getvalue()

# Prompts from your code
SYSTEM_PROMPT = """You are an expert of science fictionist. You analyze the society based on the Archaeological Prototyping(AP) model. Here is the introduction about this model:
AP is a sociocultural model composed of 18 items (6 objects and 12 paths). In essence, it's a model that divides society and culture into these 18 elements and logically depicts their connections.
##The 6 objects are:
1. Avant-garde social issues: Social issues caused by paradigms of technology and resources, and the everyday spaces and user experiences shaped by them, are made visible through art (social critisim).
2. Human's value: The desired state of people who empathize with avant-garde social issues disseminated through cultural and artistic promotion, as well as with social issues that cannot be addressed by existing systems and are spread through everyday communication. These issues are not recognized by everyone, but only by a certain group of progressive or minority individuals. Specifically, they include macro-level environmental issues (such as climate and ecology) and human-centered environmental issues (such as ethics, economics, and public health).
3. Social Issue: Social issues that are brought to public awareness by progressive communities tackling avant-garde problems, as well as systemic issues exposed through the media. These issues become visible as targets that society must address.
4. Technology and resource: Technologies and resources that have been standardized and constrained by the past, created to ensure the smooth functioning of everyday routines. These include those held by organizations—whether for-profit, non-profit, incorporated, or unincorporated, new or existing—that are structured to solve social issues.
5. User experiences: A physical space composed of products and services developed through the mobilization of technologies and resources. Within this space, users assign meaning to these products and services based on certain values, and engage in experiences through their use. The relationship between values and user experience can be illustrated, for example, by people who hold the value of "wanting to become an AI engineer" interpreting a PC as "a tool for learning programming" and thereby engaging in the experience of "programming."
6. System: Systems created to facilitate the routines practiced by people who hold certain values, as well as systems established to enable stakeholders involved in businesses that shape everyday spaces and user experiences (i.e., the business ecosystem) to operate more smoothly. Specifically, these include laws, guidelines, industry standards, administrative guidance, and moral codes.

##The 12 paths are:
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
12. Art (Social Critique): A person's belief that views problems that people are unaware of from a subjective/intrinsic perspective. It has the role of feeling discomfort with everyday spaces and user experiences and presenting problems. Converting everyday spaces and user experiences into avant-garde issues.
"""

def generate_description(product, user_experience, avant_garde_issue):
    return f"""
Here are some information about the {product}:
##Positive feedback: {user_experience}
##Negative feedback: {avant_garde_issue}
Here is an related example image. Please generate a description of this product, such as appearance or function. Less than 100 words.
"""


def build_background(product, user_experience, avant_garde_issue):
    return f"""
Here are some information about the {product}:
##Positive feedback: {user_experience}
##Negative feedback: {avant_garde_issue}
Please analyze and generate the all objects and paths in AP model based on the given information. Only output the objects and paths. Let's think step by step.
"""

def update_description(product, description_history, bg_history, initial_description, step):
    introduction = f"""
This is {product}. The development of this technology follows these 3 steps:
##Step 1: Ferment period: In this step, technological development progresses steadily, focusing mainly on solving existing problems and improving current functionalities. At the end of this period, current problem will be solved and new problem will happen.
##Step 2: Take-off period: In this step, technology enters a period of rapid development. People propose various innovative ideas, which are eventually combined to form entirely new forms of technology. At the end of this period, this technology will have a huge development, but also lead to new problem.
##Step 3: Maturity period: In this step, technological development slows down again. While solving the problems in last stage. At the end of this period, the technology develops to a more stable and mature state.

"""
    if step == 0:
        introduction += f"""
## Initial description before step 1:
{initial_description}
"""
    else:
        for i in range(step):
            introduction += f"""
    ##Description after Step {i+1}: 
    {description_history[i]['description']}

    ##Background that related to AP model after Step {i+1}:
    {bg_history[i]['background']}
    """
    introduction += f"""
Now analyze and imagine what the product will look like at the end of step {step+1}, such as appearance or function. Only output the description for step {step+1} in less than 100 words.
"""
    
    return introduction

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

def generate_image_edit_prompt(product, next_description, step):
    """Generate prompt for image editing based on the evolution stage"""
    stage_names = {
        1: "Ferment Period",
        2: "Take-off Period",
        3: "Maturity Period"
    }
    
    return f"""
You are an expert drawer, who is good at imagine the future.
Here is an image of {product}. Imagine how it will looks like after the {stage_names[step]} based on the following description:
##New evolved description: {next_description}
"""

# Main content area
if generate_button and product and user_experience and avant_garde_issue and uploaded_file and not st.session_state.generated:
    # Initialize containers for each step
    initial_container = st.container()
    step1_container = st.container()
    step2_container = st.container()
    step3_container = st.container()
    final_container = st.container()
    initial_description = ""
    
    with initial_container:
        # Save uploaded image temporarily
        with st.spinner("Processing image..."):
            # Read uploaded file
            image = Image.open(uploaded_file)
            
            # Resize image
            resized_image = resize_image(image)
            
            # Convert to base64
            img_base64 = encode_image(resized_image)
            
            # Save as temp file
            temp_image_path = save_temp_image(resized_image)
            
            # Store images history
            image_history = [resized_image]
            
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
        
        prompt = generate_description(product, user_experience, avant_garde_issue)
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
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

        prompt = update_description(product, bg_history, description_history, initial_description, 0)
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        first_description = completion.choices[0].message.content
        
        # Store first step description
        description_history.append({
            "step": 1,
            "description": first_description
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
        
        progress_bar.progress(0.25)
        
        # Generate evolved image for stage 1 based on initial description
        status_text.text("Generating product image for Ferment period...")
        
        # Create image edit prompt
        image_edit_prompt = generate_image_edit_prompt(product, first_description, 1)
        
        # Edit image using gpt-image-1
        with open(temp_image_path, "rb") as img_file:
            result = client.images.edit(
                model="gpt-image-1",
                image=img_file,
                prompt=image_edit_prompt,
                quality="low"
            )
        
        # Save and process stage 1 image
        stage1_image_bytes = base64.b64decode(result.data[0].b64_json)
        stage1_image = Image.open(io.BytesIO(stage1_image_bytes))
        stage1_image_path = "stage1_image.png"
        stage1_image.save(stage1_image_path)
        
        # Update image history - replace the original uploaded image with the evolved one
        image_history[0] = stage1_image
        
        progress_bar.progress(0.3)
        
        # Display Stage 1
        st.subheader("🌱 Stage 1: Ferment Period")
        with st.expander("View Stage 1 Details", expanded=False):
            st.markdown("**Current Description:**")
            st.markdown(first_description)
            st.markdown("**AP Model Background:**")
            st.markdown(initial_background)
            st.markdown("**Product Image:**")
            st.image(stage1_image, caption=f"{product} - Ferment Period", use_container_width=True)
    
    with step2_container:
        # Step 2: Update description
        status_text.text("Evolving to Take-off period...")
        
        prompt = update_description(product, description_history, bg_history, initial_description, 1)
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
        
        progress_bar.progress(0.40)
        
        # Generate evolved image for stage 2
        status_text.text("Generating evolved product image for Take-off period...")
        
        # Create image edit prompt
        image_edit_prompt = generate_image_edit_prompt(
            product, 
            second_description, 
            2
        )
        
        # Edit image using gpt-image-1
        with open(stage1_image_path, "rb") as img_file:
            result = client.images.edit(
                model="gpt-image-1",
                image=img_file,
                prompt=image_edit_prompt,
                quality="low"
            )
        
        # Save and process stage 2 image
        stage2_image_bytes = base64.b64decode(result.data[0].b64_json)
        stage2_image = Image.open(io.BytesIO(stage2_image_bytes))
        stage2_image_path = "stage2_image.png"
        stage2_image.save(stage2_image_path)
        
        # Add to image history
        image_history.append(stage2_image)
        
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
            st.markdown("**Evolved Product Image:**")
            st.image(stage2_image, caption=f"{product} - Take-off Period", use_container_width=True)
    
    with step3_container:
        # Step 3: Update description
        status_text.text("Evolving to Maturity period...")
        
        prompt = update_description(product, description_history, bg_history, initial_description, 2)
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
        
        progress_bar.progress(0.70)
        
        # Generate evolved image for stage 3
        status_text.text("Generating evolved product image for Maturity period...")
        
        # Create image edit prompt
        image_edit_prompt = generate_image_edit_prompt(
            product, 
            third_description, 
            3
        )
        
        # Edit image using gpt-image-1
        with open(stage2_image_path, "rb") as img_file:
            result = client.images.edit(
                model="gpt-image-1",
                image=img_file,
                prompt=image_edit_prompt,
                quality="low"
            )
        
        # Save and process stage 3 image
        stage3_image_bytes = base64.b64decode(result.data[0].b64_json)
        stage3_image = Image.open(io.BytesIO(stage3_image_bytes))
        stage3_image_path = "stage3_image.png"
        stage3_image.save(stage3_image_path)
        
        # Add to image history
        image_history.append(stage3_image)
        
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
            st.markdown("**Evolved Product Image:**")
            st.image(stage3_image, caption=f"{product} - Maturity Period", use_container_width=True)
    
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
            quality="low"
        )
        cover_image_bytes = base64.b64decode(cover_img.data[0].b64_json)
        cover_image = Image.open(io.BytesIO(cover_image_bytes))
        
        progress_bar.progress(1.0)
        status_text.text("✅ Generation complete!")
        time.sleep(0.5)
        progress_placeholder.empty()
        status_text.empty()
        
        # Store generated data in session state
        st.session_state.bg_history = bg_history
        st.session_state.description_history = description_history
        st.session_state.story = story
        st.session_state.image_data = [get_image_bytes(img) for img in image_history]
        st.session_state.cover_image_data = get_image_bytes(cover_image)
        st.session_state.product = product
        st.session_state.generated = True
        
        # Clean up temporary image files
        for file_path in [temp_image_path, stage1_image_path, stage2_image_path, stage3_image_path]:
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except:
                    pass
                    
        # Force rerun to display results with storage
        st.rerun()

# Display results if already generated
if st.session_state.generated:
    # Display evolution timeline
    st.subheader("🔄 Product Evolution Timeline")
    cols = st.columns(3)
    stages = ["Ferment", "Take-off", "Maturity"]
    
    for i, stage in enumerate(stages):
        with cols[i]:
            st.image(io.BytesIO(st.session_state.image_data[i]), caption=f"Stage {i+1}: {stage} Period", use_container_width=True)
            with st.expander(f"View Stage {i+1} Description"):
                st.markdown(st.session_state.description_history[i]['description'])
    
    # Display story and cover
    st.subheader("📚 Science Fiction Story")
    col1, col2 = st.columns([1, 2])
    with col1:
        st.image(io.BytesIO(st.session_state.cover_image_data), caption="Story Cover", use_container_width=True)
    with col2:
        st.markdown("**Story Text:**")
        st.markdown(st.session_state.story)
    
    # Download buttons
    st.subheader("Download Options")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Download background history JSON
        bg_json = json.dumps(st.session_state.bg_history, ensure_ascii=False, indent=2)
        st.download_button(
            label="📥 Download AP Model JSON",
            data=bg_json,
            file_name="background_history.json",
            mime="application/json",
            key="download_bg_json"
        )
        
        # Download story
        st.download_button(
            label="📥 Download Story",
            data=st.session_state.story,
            file_name="story.txt",
            mime="text/plain",
            key="download_story"
        )
    
    with col2:
        # Download description history JSON
        desc_json = json.dumps(st.session_state.description_history, ensure_ascii=False, indent=2)
        st.download_button(
            label="📥 Download Descriptions JSON",
            data=desc_json,
            file_name="description_history.json",
            mime="application/json",
            key="download_desc_json"
        )
        
        # Download cover image
        st.download_button(
            label="📥 Download Cover Image",
            data=st.session_state.cover_image_data,
            file_name="cover.png",
            mime="image/png",
            key="download_cover"
        )
    
    with col3:
        # Download evolved images
        for i, img_bytes in enumerate(st.session_state.image_data):
            stage_name = ["Ferment", "Take-off", "Maturity"][i]
            st.download_button(
                label=f"📥 Download {stage_name} Image",
                data=img_bytes,
                file_name=f"stage{i+1}_{stage_name.lower()}.png",
                mime="image/png",
                key=f"download_stage{i+1}"
            )
    
    # Reset button
    if st.button("🔄 Generate New Story", type="primary"):
        # Reset session state
        st.session_state.generated = False
        st.session_state.bg_history = []
        st.session_state.description_history = []
        st.session_state.story = ""
        st.session_state.image_data = []
        st.session_state.cover_image_data = None
        st.session_state.demo_clicked = False
        st.rerun()

else:
    # Show instructions when not running
    st.subheader("Instructions")
    st.markdown("""
    1. Fill in the left panel input fields:
       - Product Name
       - User Experience Description
       - Avant-garde Issue (potential problems)
    2. Upload a product image
    3. Click "Generate Story" button
    4. Wait for processing to complete and download results
    
    **Or simply click the "Generate Demo" button in the sidebar to try with the smartphone example!**
    """)
    
    # Show example
    st.subheader("Example")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        **Product Name:** Smartphone
        
        **User Experience:**  
        It allows me talk with my parents from anywhere in the world.
        
        **Avant-garde Issue:**  
        People spend too much time on it.
        """)
        
    with col2:
        # Display the demo smartphone image if available
        try:
            example_img = Image.open("smartphone_demo.jpg")
            st.image(example_img, caption="Example: Smartphone", use_container_width=True)
        except:
            st.info("Demo image will be displayed when the demo is generated.")

# Sidebar footer
st.sidebar.markdown("---")
st.sidebar.markdown("Made with ❤️ using Streamlit")