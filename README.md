**AIMAAK** is an AI-powered conversational assistant designed for **real-time multilingual customer support** (Darija/French). It leverages **FastAPI**, **LangChain**, **Redis**, and **vector databases** to deliver dynamic, context-aware, and scalable responses. The backend exposes RESTful APIs for chat interactions, document-based Q&A, and relational database integrations.

---

## 🚀 Features
- **AI-Powered Responses**: Uses **LangChain** with Google Generative AI for smart and contextual replies.
- **Multilingual Support**: Understands **Moroccan Darija** and **French**.
- **Real-Time Chat**: Backend optimized with **FastAPI** and **Redis** for fast response handling.
- **Document Q&A**: Extracts knowledge from PDF documents (e.g., `Lara_Fashion_QA.pdf`) using vector stores and embeddings.
- **Relational DB Integration**: Provides SQL-based knowledge querying.
- **Cross-Origin Ready**: CORS enabled for easy frontend integration.
- **Voice & Chat Modes**: Supports both chatbot widget mode and voice-based interaction using Gemini API.

---

## 🛠 Tech Stack
- **Framework**: [FastAPI](https://fastapi.tiangolo.com/)
- **AI/LLM Framework**: [LangChain](https://www.langchain.com/) + OpenAI & Gemini
- **Database**: MySQL + Redis (for session and cache handling)
- **Vector Store**: FAISS
- **Deployment**: Uvicorn workers

---

## 📦 Installation

### Prerequisites
- Python **3.10+**
- SQL Engine
- Redis
- LangChain
- FAISS
- FastAPI
- `virtualenv` (recommended)

### Steps
```bash
# 1. Clone the repository
git clone https://github.com/<your-username>/AIMaak-Backend.git
cd AIMaak-Backend

# 2. Create a virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\\Scripts\\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment variables
cp .env.example .env
# Edit .env and add your REDIS, MySQL, and API keys

# 5. Start the FastAPI server
uvicorn main:app --reload
```

## ⚙️ Environment Variables

Create a `.env` file in the project root with:
```
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=your_password

DB_URI=your_db_url_if_you_are_using_an_oline_db

MYSQL_HOST=localhost
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DB=aimaak

GEN_API_KEY=your_key
OPENAI_API_KEY=sk-your_key
```

## 🔗 API Endpoints

| Method | Endpoint            | Description                     |
| ------ | ------------------- | ------------------------------- |
| POST   | `/chat`             | Send a chat message to AI       |
| POST   | `/documents/query`  | Ask a question on uploaded docs |
| POST   | `/sql/query`        | Converts a natural language question to a safe SQL query, runs it, and returns the results with a natural language answer |

## 📜 License

This project is licensed under the MIT License.

## 👥 Contributors
- **Zakaria EL-AOUFI:** Created all RAG pipelines
- **Wassim Midi:** Deployed and integrated voice into AIMAAK
- **Mohammed Amine El Abiad:** Frontend Developer
