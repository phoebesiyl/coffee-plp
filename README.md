An interactive Retrieval-Augmented Generation (RAG) learning portal that teaches coffee science and brewing methods through curated professional and academic sources.
Built with Streamlit, LangChain, and OpenAI, the portal retrieves grounded coffee knowledge and generates educational, citation-based answers.

🚀 Quick Start
1. Clone the repo
git clone https://github.com/phoebeli/coffee-plp.git
cd coffee-plp

2. Create a virtual environment
python -m venv .venv
source .venv/bin/activate   # macOS / Linux

3. Install dependencies

4. Add your OpenAI API key

Create a .env file in the project root:

OPENAI_API_KEY=your_api_key_here

5. Build vector database (first time only)
python data/process_sources.py

6. Launch the Streamlit app
streamlit run app.py


Your browser will open at http://localhost:8501
 showing the Coffee Learning Portal interface.
