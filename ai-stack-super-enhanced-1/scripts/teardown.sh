   enhanced_rag_kg/
   ├── api/
   │   ├── app.py
   │   ├── routes/
   │   │   ├── ingest.py
   │   │   ├── search.py
   │   │   ├── kg.py
   │   │   └── metrics.py
   │   └── models/
   │       ├── requests.py
   │       └── responses.py
   ├── pipelines/
   │   ├── hybrid_search.py
   │   └── ingestion_pipeline.py
   ├── preprocessors/
   │   └── kg_writer.py
   ├── core/
   │   ├── semantic_grouping.py
   │   └── utils.py
   ├── tests/
   │   ├── test_ingest.py
   │   ├── test_search.py
   │   └── test_kg.py
   ├── data/
   │   ├── index.json
   │   └── kg_snapshot.json
   ├── requirements.txt
   └── README.md