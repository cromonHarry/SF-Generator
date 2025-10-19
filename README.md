# 🚀 Near-Future SF Generator

**Streamlit-based application** that generates **3-stage development timelines** and **SF short stories** based on real-world products and user experiences, using the **S-curve model** and **Archaeological Prototyping (AP) model**.
Related paper already accepted in ICCE GCCE 2025: **AP-Based LLM Story Generation: Envision Technology Development Through Science Fiction**

## ✨ New Features (Enhanced Version)

- **Multi-stage interactive interface** for intuitive input experience
- **Tavily automatic search** for realistic data foundation
- **Future-oriented** AP model evolution
- **Interactive visualization** for AP model display
- **Full English support**

## 🔍 Main Features

### 📝 Step-by-Step Input Process
1. **Topic of Interest** input
2. **Theme selection** from Tavily search results
3. **Future development direction** selection (technological innovation, experience enhancement, environmental protection)
4. **Future vision** description
5. **Personal scenario** description

### 🎯 Auto-Generated Content
- **3-stage technology evolution timeline** (S-curve model based)
  - Stage 1: Embryonic Period (based on real Wikipedia data)
  - Stage 2: Growth Period (based on user's future vision)
  - Stage 3: Maturity Period (completion of development process)
- **Sociocultural background changes** (AP model based)
- **SF short story** (approximately 1000 words)

### 📊 Visualization Features
- **AP model interactive visualization**
- **6 objects** and **12 arrows** relationship display
- **Inter-stage evolution** visualization

### 💾 Download Features
- AP model data (`ap_model.json`)
- Stage-by-stage descriptions (`description.json`)
- SF short story (`sf_story.txt`)

## 📦 Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/sf-generator-en.git
   cd sf-generator-en
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Add OpenAI API key as environment variable:
   ```bash
   export OPENAI_API_KEY=your-api-key
   ```

4. Run the application:
   ```bash
   streamlit run app.py
   ```

## 🌐 Using with Streamlit Cloud

The app is also available on Streamlit Cloud:
[https://sf-generator-en.streamlit.app/](https://sf-generator-en.streamlit.app/)

### Secrets Configuration
Add the following in Streamlit Cloud project settings:
```toml
[openai]
api_key = "your-openai-api-key-here"

[tavily]
api_key = "your-tavily-api-key-here"
```

## 🧠 Models Used

- **OpenAI GPT-4o** - Text generation and analysis
- **Tavily API** - Real-world data acquisition

## 📊 About the AP Model

**Archaeological Prototyping (AP) model** is a model that analyzes sociocultural aspects using 18 elements:

[Design Resilience Model in Archaeology: Possibilities of Archaeological Prototyping](https://www.ritsumei.ac.jp/research/rcds/file/2023/7_rcds_2_nakamura_goto.pdf)

### 6 Objects
- **Avant-garde Social Issues** - Issues caused by technology paradigms
- **People's Values** - Values recognized by progressive people
- **Social Issues** - Issues recognized and to be solved in society
- **Technology and Resources** - Technology organized for problem solving
- **Daily Spaces and User Experience** - Physical spaces and experiences through products/services
- **Institutions** - Systems that facilitate habits and business

### 12 Arrows (Transformation Relationships)
- **Media** - Exposing institutional defects
- **Community Formation** - Communities addressing avant-garde issues
- **Cultural Arts Promotion** - Art-based issue transmission
- **Standardization** - Institutionalization into technology/resources
- **Communication** - Issue transmission via SNS etc.
- **Organization** - Formation of problem-solving organizations
- **Meaning Attribution** - Reasons for using products/services based on values
- **Products/Services** - Creation using technology
- **Habituation** - Institutionalization of value-based habits
- **Paradigm** - New social issues from dominant technology
- **Business Ecosystem** - Networks of business stakeholders
- **Art (Social Criticism)** - Presenting issues from discomfort with daily life

## 📈 S-Curve Model

### 3 Stages of Technology Evolution
1. **Stage 1: Embryonic Period** - Solving existing problems and improvements
2. **Stage 2: Growth Period** - Rapid technological development
3. **Stage 3: Maturity Period** - Stable and mature state

## 🧪 Usage Example

1. **Interest**: Smartphone
2. **Development Direction**: Technological innovation
3. **Future Vision**: More intuitive and environmentally friendly communication devices
4. **Personal Scenario**: I want to use new technology to deepen communication with my family
➡️ Generate an original novel imagining future impacts

## 💻 Technical Features

### Frontend
- **Streamlit** - Interactive web application
- **HTML/CSS/JavaScript** - Custom visualization

### Backend
- **Python** - Main programming language
- **OpenAI API** - AI generation
- **Tavily API** - Data acquisition

### Data Processing
- **JSON** - Data storage and exchange
- **Session State** - Application state management

## 🔧 Technical Requirements

- Python 3.12
- streamlit==1.45.0
- openai==1.77.0
- pillow==10.2.0
- networkx==3.2.1
- matplotlib==3.9.2
- pandas==2.2.2
- wikipedia==1.4.0
- tavily-python==0.7.7

## 🎮 How to Use

1. **Enter Theme**: Input the topic you want to explore
2. **Describe Setting**: Provide details about the story setting
3. **AI Generation**: Let the AI automatically generate:
   - Stage 1: Current analysis using Tavily web search
   - Stage 2: Future development using multi-agent collaboration
   - Stage 3: Maturity prediction with expert AI agents
   - SF Story: Complete short story based on the 3-stage timeline
4. **Visualization**: View interactive AP model diagrams
5. **Download**: Save generated content as files

## 🤖 Multi-Agent System

The application features an innovative **multi-agent collaboration system**:

- **3 Expert AI Agents** with different specializations
- **3 Iteration Rounds** for each future element
- **Competitive Proposal Generation** with quality evaluation
- **Diversity Assurance** to avoid repetitive ideas
- **Creative Innovation** focus for breakthrough thinking

## 🌟 Key Innovations

- **Real-world Grounding**: Stage 1 uses actual web data via Tavily
- **Future Speculation**: Stages 2-3 use creative AI collaboration
- **Visual Storytelling**: Interactive diagrams show societal evolution
- **Narrative Integration**: Technical analysis becomes compelling fiction
- **Systematic Approach**: AP model ensures comprehensive coverage

## 🤝 Contributing

Pull requests and issue reports are welcome!

## 📄 Acknowledgments

- [Streamlit](https://streamlit.io/) - Web application framework
- [OpenAI](https://openai.com/) - AI generation engine
- [Tavily](https://tavily.com/) - Web search API
- [S-Curve Model](https://www.the-waves.org/2022/03/13/innovation-s-curve-episodic-innovation-evolution/) - Technology evolution theory

## 📜 License

MIT License

## 🔗 Related Links

- [Live Demo](https://sf-generator-en.streamlit.app/)
- [Project Repository](https://github.com/cromonharry/sf-generator-en)
- [Issue Reports](https://github.com/cromonharry/sf-generator-en/issues)

---

**Made with ❤️ using Streamlit and AI**
