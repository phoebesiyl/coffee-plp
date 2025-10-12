An interactive Retrieval-Augmented Generation (RAG) learning portal that teaches coffee science and brewing methods through curated professional and academic sources.
Built with Streamlit, LangChain, and OpenAI, the portal retrieves grounded coffee knowledge and generates educational, citation-based answers.

🚀 Quick Start
1. Clone the repo
git clone https://github.com/phoebeli/coffee-plp.git
cd coffee-plp

2. Create a virtual environment
python -m venv .venv
source .venv/bin/activate   # macOS / Linux
.venv\Scripts\activate      # Windows

3. Install dependencies
pip install -r requirements.txt

4. Add your OpenAI API key

Create a .env file in the project root:

OPENAI_API_KEY=your_api_key_here

5. Build vector database (first time only)
python data/process_sources.py

6. Launch the Streamlit app
streamlit run app.py


Your browser will open at http://localhost:8501
 showing the Coffee Learning Portal interface.

🧩 Project Structure
coffee-plp/
├── app.py                      # Streamlit interface
├── langchain_rag.py            # RAG pipeline (retrieval + generation)
├── agents.py                   # Multi-agent orchestration (researcher/synthesizer/critic)
├── data/
│   ├── process_sources.py      # Source ingestion and embedding builder
│   ├── sources.csv             # 15 curated learning sources
│   └── chroma_db/              # Persisted Chroma index (auto-created)
├── config.yaml                 # Model and retriever settings
└── README.md                   # Documentation

🧠 Learning Modules

The portal is organized into three modules:

Pillar	Focus	Example Queries
👅 Sensory & Flavor Science	Cupping, flavor lexicons, sensory analysis	“How are coffee flavors categorized across aroma, taste, and aftertaste?”
☕ Espresso & Milk Mastery	Extraction science, milk chemistry	“How does milk steaming temperature influence foam texture?”
🫖 Hand Brewing Methods	Pour-over and immersion techniques	“Compare V60 and French Press extraction.”
📊 Evaluation Summary

System performance was evaluated using a manual RAGAs-style framework (factuality, groundedness, context recall, relevance).
Average scores across five benchmark queries:

Metric	Avg Score
Factuality	0.92
Groundedness	0.88
Context Recall	0.85
Relevance	0.90
🖼️ Interface Preview
Streamlit View	Description

	The main interface includes a “Brew Answer ☕” button, sidebar for source citations, and retrieval confidence display.
💡 Author

Siying (Phoebe) Li
MISM-BIDA ’25, Carnegie Mellon University
📧 siyingl4@andrew.cmu.edu
