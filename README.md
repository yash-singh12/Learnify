# Personalized Learning Path Prototype

A minimal prototype that generates personalized course recommendations based on user interests using **FastAPI**, **MongoDB**, and **Sentence Transformers**.

## How It Works

1.  **Data**: Course documents (title, description, tags) are stored in MongoDB.
2.  **Embeddings**: We use a pre-trained model (`all-MiniLM-L6-v2`) to convert course text into vector embeddings (lists of numbers representing semantic meaning). These are stored in the database.
3.  **Search**: When a user enters interests, the backend computes an embedding for the user's query.
4.  **Matching**: It calculates the **Cosine Similarity** between the user's query vector and all course vectors.
5.  **Result**: The top-K most similar courses are returned.

## Prerequisites

- Python 3.9+
- MongoDB (running locally or Atlas URI)

## Setup & Run

### 1. Environment Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Tip: If you don't have a GPU, you can install CPU-only PyTorch to save space:
# pip install torch --index-url https://download.pytorch.org/whl/cpu
```

### 2. Configuration

Create a `.env` file from the example:

```bash
cp .env.example .env
```

Edit `.env` if you need to change the `MONGODB_URI`. Default is `mongodb://localhost:27017`.

### 3. Data Initialization

Insert sample courses and compute embeddings:

```bash
# Insert sample data
python insert_sample_courses.py

# Compute embeddings (idempotent - only computes for new docs)
python embedding.py
```

### 4. Start Backend

```bash
uvicorn main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`.
Health check: `http://localhost:8000/health`

### 5. Run Frontend

You can simply open `index.html` in your browser, or serve it using Python:

```bash
# Run in a separate terminal
python -m http.server 5500
```

Then open [http://localhost:5500](http://localhost:5500).

## Example Usage

**Curl Request:**

```bash
curl -X POST "http://localhost:8000/api/generate" \
     -H "Content-Type: application/json" \
     -d '{"field1": "machine learning", "field2": "python", "top_k": 3}'
```

**Response:**

```json
{
  "query": "machine learning python",
  "results": [
    {
      "id": "...",
      "title": "Intro to Machine Learning",
      "description": "...",
      "score": 0.854
    },
    ...
  ]
}
```

## Notes

- **Model**: We use `all-MiniLM-L6-v2` which is small and fast, perfect for CPU usage.
- **Embeddings**: Stored in MongoDB to avoid recomputing on every startup.
- **Reloading**: If you add new courses and re-run `embedding.py`, you can hit `POST /api/reload_embeddings` to update the running server without restarting.
