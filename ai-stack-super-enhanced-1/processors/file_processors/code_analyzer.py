   enhanced_rag_kg/
   ├── api/
   │   ├── app.py
   │   ├── routes/
   │   │   ├── ingest.py
   │   │   ├── search.py
   │   │   ├── kg.py
   │   │   └── metrics.py
   │   ├── models/
   │   │   ├── requests.py
   │   │   └── responses.py
   │   └── utils/
   │       ├── logging.py
   │       └── validation.py
   ├── pipelines/
   │   ├── hybrid_search.py
   │   └── ingestion_pipeline.py
   ├── preprocessors/
   │   └── kg_writer.py
   ├── tests/
   │   ├── test_ingest.py
   │   ├── test_search.py
   │   └── test_kg.py
   ├── requirements.txt
   └── README.md