# Arabic PDF Processing and LLM Training Platform

A comprehensive end-to-end AI model training platform designed to allow users and organizations to train language models on their own Arabic-language PDF datasets.

## Project Overview

This platform enables users to:
- Upload and manage PDF documents (both scanned and searchable)
- Process Arabic text using OCR and text extraction
- Preprocess and clean the extracted text
- Prepare datasets for training
- Train models using RAG or fine-tuning approaches
- Evaluate and validate trained models
- Deploy models as APIs
- Manage the entire process through intuitive user interfaces

## Architecture

The platform is built with a modular architecture, divided into the following phases:

1. **Data Upload and Management**
2. **OCR and Text Extraction**
3. **Data Preprocessing and Cleaning**
4. **Dataset Preparation for Training**
5. **Model Training and Optimization**
6. **Model Evaluation and Validation**
7. **Deployment and Model Serving**
8. **Administrative and User Interfaces**

Each phase is implemented as a separate module with well-defined interfaces, allowing for independent development, testing, and deployment.
After uploading a document, send `POST /api/ocr/{document_id}` to extract text from each page.

## Technology Stack

- **Frontend**: React with TypeScript, Tailwind CSS
- **Backend**: FastAPI (Python)
- **Database**: PostgreSQL for structured data, Vector database for embeddings
- **Storage**: Cloud storage (configurable) for PDF files and models
- **OCR**: Tesseract with Arabic language support
- **NLP**: Hugging Face Transformers, PyTorch
- **Deployment**: Docker, RESTful APIs

## Getting Started

[Installation and setup instructions will be added]

## License

[License information will be added]

## Staging Deployment

A helper script is provided to deploy the current commit to a temporary staging environment. The script builds Docker images, provisions a docker-compose stack and runs health checks.

```bash
scripts/deploy_staging.sh
```

Deployment logs and summaries are stored under `deployments/<commit-sha>/`.

The script expects Docker and docker-compose to be available and uses `.env.staging` for environment variables.
