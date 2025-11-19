# Educational Video QA System

An intelligent question-answering system for educational videos using a Retrieval-Augmented Generation (RAG) pipeline.

## Features

-   Upload and manage educational videos
-   Intelligent question answering based on video content
-   Workspace management and video organization
-   Semantic search using vector embeddings
-   BM25-based reranking
-   User authentication with JWT

## Tech Stack

### Backend

-   FastAPI
-   MongoDB (Motor)
-   LangChain + ChromaDB
-   Google Gemini
-   Sentence Transformers
-   PyTorch + OpenCV

### Frontend

-   React + TypeScript
-   Vite
-   Ant Design
-   TanStack Query
-   Axios

## System Requirements

-   Python 3.9+
-   Node.js 18+
-   MongoDB
-   FFmpeg

## Installation and Setup

### 1. Clone the repository

```bash
git clone <repository-url>
cd educational_video_qa
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate     # macOS/Linux
# or: venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Create environment file
cp .env.example .env

# Start backend
fastapi run app/main.py
```

Backend URL:

```
http://localhost:8000
```

API documentation:

```
http://localhost:8000/docs
```

### 3. Frontend Setup

```bash
cd frontend

npm install
cp .env.example .env

npm run dev
```

Frontend URL:

```
http://localhost:5173
```

## Usage

1. Access the frontend interface
2. Register or log in
3. Create a workspace
4. Upload an educational video
5. Ask questions based on the video content

## Project Structure

```
educational_video_qa/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   └── utils/
│   └── storage/
├── frontend/
│   └── src/
│       ├── components/
│       ├── pages/
│       ├── apiServices/
│       └── types/
└── README.md
```

## Environment Variables

### Backend `.env`

```
MONGODB_URL=mongodb://localhost:27017
MONGODB_DATABASE=educational_video_qa
SECRET_KEY=your-secret-key-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=43200
UPLOAD_DIR=./storage/videos
CHROMA_PERSIST_DIR=./storage/chroma_db
GEMINI_API_KEYS=your-gemini-api-key,...
```

### Frontend `.env`

```
VITE_API_BASE_URL=http://localhost:8000
```

## Scripts

### Backend

```bash
fastapi run app/main.py
```

### Frontend

```bash
npm run dev
npm run build
npm run preview
```

## Contributing

This project is built as part of the CS431 course on Deep Learning Techniques and Applications.

## License

MIT License
