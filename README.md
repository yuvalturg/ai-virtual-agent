# ai-virtual-assistant

## Clone the repository

1. Clone the ai-virtual-assistant repository

    ```bash
    git clone https://github.com/RHEcosystemAppEng/ai-virtual-assistant
    cd ai-virtual-assistant
    ```

## Start PostgreSQL database

1. Run the following command to start the PostgreSQL

    ```bash
    podman compose --file compose.yaml up --detach
    ```

## Start the backend server

1. Install dependencies:

    ```bash
    python3.10 -m venv venv
    source venv/bin/activate
    pip3 install -r backend/requirements.txt
    ```

2. Start Server

    ```bash
    ./venv/bin/uvicorn backend.main:app
   ```

## Start the ui server

In another terminal:

1. Install dependencies

   ```bash
    cd frontend
    npm install
   ```

2. Start server

    ```bash
    npm run start
   ```
