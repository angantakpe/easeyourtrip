# EaseYourTrip Document AI - Streamlit Frontend

This directory contains the Streamlit frontend for the EaseYourTrip Document AI application. It provides a user-friendly interface for uploading and processing documents, viewing extracted information, and testing the various API endpoints.

## Features

- Document upload interface
- Category selection for document processing
- Visualization of extracted document information
- API endpoint testing capabilities
- Real-time feedback on document processing status

## Development Setup

The Streamlit frontend is containerized using Docker and configured to support live code reloading during development.

### Running the Frontend

You can run the Streamlit frontend using the following methods:

#### Using Make Commands

```bash
# Start the Streamlit frontend
make frontend

# Stop the Streamlit frontend
make frontend-stop
```

#### Using Docker Compose Directly

```bash
cd streamlit
docker-compose up -d
```

### Development Mode

The Streamlit frontend is configured to run in development mode, which means:

1. Code changes are automatically detected and the application reloads
2. The local code directory is mounted into the container
3. The `watchdog` package is installed to improve file change detection

## Configuration

The Streamlit frontend is configured to connect to the main Document AI API using the following environment variables:

- `NURONAI_API_KEY_LOCAL`: API key for local development
- `API_URL`: URL of the Document AI API (default: `http://app:5321`)

## Testing

You can test the frontend by uploading various document types and verifying that the information is correctly extracted and displayed.

## Troubleshooting

If you encounter issues with the Streamlit frontend:

1. Check that the main Document AI API is running
2. Verify that the Docker network is correctly configured
3. Check the Docker logs for any error messages:

```bash
docker logs streamlit_streamlit_1
```

## Contributing

When adding new features to the Streamlit frontend:

1. Ensure that your code follows the Streamlit best practices
2. Test your changes with various document types
3. Update this README with any new features or configuration options
