# Agent-Based Code Documentation Generator

## 📌 Overview
This project is an AI-powered system that automatically generates structured documentation from source code. It combines code parsing, agent-based processing, and a state machine-driven workflow to produce human-readable explanations of functions, classes, and parameters.

The system also provides real-time visualization of execution through an interactive Streamlit interface, making the entire pipeline transparent and easy to understand.

---

## ⚙️ Features
- Automated code documentation generation  
- Agent-based modular architecture  
- State machine-driven workflow control  
- AI-powered semantic code understanding  
- Real-time visualization of execution (states, logs, tool calls)  
- Structured output for functions, classes, and parameters  

---

## 🧠 System Architecture
Input Code
↓
State Machine
↓
Code Parsing (Tree-sitter)
↓
AI Description Generation (LLM)
↓
Documentation Generation
↓
Streamlit UI Display


---

## 🔄 Workflow
1. User provides source code  
2. Code is parsed to extract structure  
3. AI agent generates explanations  
4. Documentation is formatted  
5. Results are displayed with logs and state transitions  

---

## 🛠️ Tech Stack
- Python  
- Streamlit  
- Tree-sitter (Code Parsing)  
- Large Language Model (LLM)  
- State Machine Architecture  
- Git & GitHub  

---

## 📊 Core Components
- **Streamlit UI** → User interaction and visualization  
- **State Machine** → Controls execution flow  
- **Parser (`parse_code`)** → Extracts code structure  
- **AI Agent (`generate_descriptions`)** → Generates explanations  
- **Documentation Tool (`generate_docs`)** → Formats output  
- **Logging & Metrics** → Tracks execution  

---

## ▶️ How to Run
```bash
# Install dependencies
pip install -r requirements.txt

#requirements.txt
streamlit
groq
tree-sitter
tree-sitter-languages
python-dotenv
pydantic

# Run application
streamlit run ui/app.py