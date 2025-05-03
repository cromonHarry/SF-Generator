# 🚀 Near Future SF Generator

This is a **Streamlit-based application** that helps users generate a **25-year science fiction development timeline** and a **short sci-fi story** based on a real-world product and user experience, guided by the **S-Curve model** and **Archaeological Prototyping (AP) model**.

## 🔍 Features

- Upload a **product image**
- Input:
  - Product name
  - User experience description
  - Potential avant-garde issue
- Automatically generate:
  - **Technology evolution timeline** (2025–2050) based on S-Curve model
  - **Sociocultural background changes** based on AP model
  - **Original science fiction story** (with AI-generated cover)
- Downloadable results:
  - Timeline (`timeline.json`)
  - Sci-fi story (`story.txt`)
  - Story cover image (`cover.png`)


## 📦 Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/near-future-sf-generator.git
   cd near-future-sf-generator
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Add your OpenAI API key as an environment variable:
   ```bash
   export OPENAI_API_KEY=your-api-key
   ```

4. Run the app:
   ```bash
   streamlit run app.py
   ```

## 🧠 Models Used

- **OpenAI GPT-4o**
- **OPENAI GPT-Image-1**


## 🧪 Example Use Case

1. **Product**: Smart Glasses  
2. **Experience**: Real-time translation, AR navigation  
3. **Issue**: Over-dependence, privacy risks  
➡️ Generates a timeline from 2025 to 2050 and an original story imagining future impacts.

## 📜 License

MIT License
