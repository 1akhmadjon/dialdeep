
# DialDeep: Audio and JSON Data Processing API

## Overview

DialDeep is a FastAPI-based project that processes incoming audio files and JSON data, filters and formats the information, and stores the relevant data in a PostgreSQL database. Key features include:

- Splitting audio files into 30-second chunks for transcription using a Speech-to-Text (STT) model.
- Handling complex JSON data structures and interacting with external APIs.

## Features

### Audio Processing:
- Accepts `.wav` audio files.
- Splits audio into 30-second segments.
- Converts audio segments into text using an STT model.

### JSON Handling:
- Accepts two types of incoming JSON data:
  - JSON accompanying audio files.
  - Standalone JSON data.
- Parses incoming JSON, extracts the required fields, and formats them for forwarding to an external API.

### Database Integration:
- Stores audio transcriptions and JSON data in a PostgreSQL database for auditing and future use.

## Installation

### Prerequisites
- Python 3.x
- PostgreSQL database
- Required libraries (listed in `requirements.txt`)

### Steps
1. Clone the repository:
    ```bash
    git clone https://github.com/1akhmadjon/dialdeep.git
    cd dialdeep
    ```

2. Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

3. Configure environment variables:
    - Create a `.env` file in the root directory with the following variables:
        ```dotenv
        DB_NAME=your_database_name
        DB_USER=your_database_user
        DB_PASSWORD=your_database_password
        DB_HOST=your_database_host
        DB_PORT=your_database_port
        ```

4. Apply database migrations:
    ```bash
    alembic upgrade head
    ```

5. Run the application:
    ```bash
    python run.py
    python example.py
    python main.py
    ```

## Usage

### Running the API
To run the application, use the following command:
```bash
python run.py
python example.py
python main.py
```

### Upload Audio Files
- **Endpoint**: `/upload-audio`
- **Supported format**: `.wav`

### Send JSON Data
- **Endpoint**: `/process-json`

### API Documentation
The FastAPI auto-generates interactive API documentation:
- [Swagger UI](http://127.0.0.1:8082/docs)
- [ReDoc](http://127.0.0.1:8082/redoc)

## How It Works

### Audio Processing:
- `.wav` audio files are uploaded via the API.
- Each file is segmented into 30-second chunks.
- The chunks are processed by an STT model, and the transcribed text is stored in the database.

### JSON Handling:
- Incoming JSON data is parsed for required fields.
- Relevant data is forwarded to an external API and stored in the database for auditing.

### Note:
In the `utils/send_result_to_api` function, customize the `api_url` to match your external API endpoint.

## Database Configuration
- Ensure the PostgreSQL database is running and accessible using the credentials defined in the `.env` file.

## STT Model Configuration
- Verify the required model files or API keys are configured correctly.

## Dependencies
Install all required libraries:
```bash
pip install -r requirements.txt
```

## Contributions
Contributions are welcome! Feel free to open issues, submit pull requests, or provide feedback.

## License
This project is licensed under the MIT License.

## Contact
For questions or support, contact Akhmadjon.
