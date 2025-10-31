# Offline bundle preparation and installation

This folder contains two helper scripts to prepare and install an offline bundle for the RAG service when the target machine has no Internet access.

1) On an Internet-connected machine (same platform/architecture as the offline target) run:

```bash
# Optionally set MODEL_NAME to include a SentenceTransformers model (eg: all-MiniLM-L6-v2)
MODEL_NAME=all-MiniLM-L6-v2 scripts/prepare_offline_bundle.sh
```

The script will create `offline_bundle.tar.gz` at the repository root containing:
- wheels/ (Python wheels for required packages)
- requirements.txt
- optional models/<MODEL_NAME> if MODEL_NAME was set and download succeeded

2) Transfer `offline_bundle.tar.gz` to the offline target machine (via USB, scp, etc.) and run on the target:

```bash
scripts/offline_install.sh
```

This will:
- extract the wheels and install them with `pip --no-index --find-links` (installing locally)
- copy any included models into `./models/`

After installation, set the environment variable `LOCAL_ST_MODEL_PATH` to point to your model directory, for example:

```bash
export LOCAL_ST_MODEL_PATH="$(pwd)/models/all-MiniLM-L6-v2"
# then restart the service (example):
python3 -m uvicorn web.app:app --host 127.0.0.1 --port 8000
```

Notes and tips:
- Ensure the wheels were built for the same platform (macOS Intel/Apple Silicon or Linux x86_64). For torch and faiss, downloading the correct wheel is critical.
- If pip fails to install specific wheels, you may need to build them from source on the target or obtain platform-matching wheels.
- If you cannot include the model in the bundle, you can download it separately on a machine with Internet and copy the model folder into `./models/` on the target.

Platform-specific notes for your MacBook Pro (2018, Intel):

- Your machine is macOS (Intel x86_64). When preparing the offline bundle, ensure you either:
	- Run `prepare_offline_bundle.sh` on a macOS Intel machine (preferred), or
	- Provide prebuilt torch and faiss wheels compiled for macOS x86_64 via `TORCH_WHEEL_URL` and `FAISS_WHEEL_URL` environment variables when running the prepare script.

- Example of supplying a wheel URL when preparing the bundle:

```bash
TORCH_WHEEL_URL="https://download-url/torch-<version>-cp311-cp311-macosx_10_9_x86_64.whl" \
FAISS_WHEEL_URL="https://download-url/faiss-<version>-cp311-cp311-macosx_10_9_x86_64.whl" \
MODEL_NAME=all-MiniLM-L6-v2 scripts/prepare_offline_bundle.sh
```

- The `offline_install.sh` script will create a Python virtual environment at `.venv` and install wheels there. Activate it with:

```bash
source .venv/bin/activate
```

