# Weather Data Backend Service

A Flask-based backend service that fetches historical weather data from the Open-Meteo API and stores it in Google Cloud Storage (GCS). The service provides RESTful endpoints to store, list, and retrieve weather data files.

## Features

- 🌤️ Fetch historical weather data from Open-Meteo API
- ☁️ Store data as JSON files in Google Cloud Storage
- 📊 Retrieve and list stored weather data files
- 🔒 Input validation and error handling
- 🚀 Containerized deployment on Google Cloud Run
- 📝 Comprehensive logging and monitoring

## Weather Data Variables

The service fetches the following daily weather variables:
- Maximum Temperature (2m)
- Minimum Temperature (2m)
- Mean Temperature (2m)
- Maximum Apparent Temperature (2m)
- Minimum Apparent Temperature (2m)
- Mean Apparent Temperature (2m)

## API Endpoints

### 1. Store Weather Data
**POST** `/store-weather-data`

Fetches historical weather data and stores it in GCS.

**Request Body:**
```json
{
  "latitude": 52.5200,
  "longitude": 13.4050,
  "start_date": "2023-01-01",
  "end_date": "2023-01-31"
}
```

**Response:**
```json
{
  "message": "Weather data stored successfully",
  "filename": "weather_data_lat52.52_lon13.405_2023-01-01_to_2023-01-31_20241123_143022.json",
  "location": {
    "latitude": 52.52,
    "longitude": 13.405
  },
  "date_range": {
    "start_date": "2023-01-01",
    "end_date": "2023-01-31"
  }
}
```

### 2. List Weather Files
**GET** `/list-weather-files`

Lists all stored weather data files in the GCS bucket.

**Response:**
```json
{
  "files": [
    {
      "filename": "weather_data_lat52.52_lon13.405_2023-01-01_to_2023-01-31_20241123_143022.json",
      "size": 1024,
      "created": "2024-11-23T14:30:22.123456Z",
      "updated": "2024-11-23T14:30:22.123456Z"
    }
  ],
  "count": 1
}
```

### 3. Get Weather File Content
**GET** `/weather-file-content/<filename>`

Retrieves the content of a specific weather data file.

**Response:**
```json
{
  "filename": "weather_data_lat52.52_lon13.405_2023-01-01_to_2023-01-31_20241123_143022.json",
  "data": {
    "latitude": 52.52,
    "longitude": 13.405,
    "daily": {
      "time": ["2023-01-01", "2023-01-02"],
      "temperature_2m_max": [5.2, 7.1],
      "temperature_2m_min": [0.1, 2.3]
    }
  }
}
```

### 4. Health Check
**GET** `/health`

Returns the health status of the service.

## Prerequisites

- Google Cloud Platform account
- Google Cloud SDK (gcloud) installed
- Docker installed
- Python 3.11+ (for local development)

## Local Development Setup

1. **Clone the repository:**
```bash
git clone <your-repo-url>
cd weather-data-backend
```

2. **Set up virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Set up Google Cloud credentials:**
```bash
# Authenticate with Google Cloud
gcloud auth application-default login

# Set your project ID
export GOOGLE_CLOUD_PROJECT=your-project-id
export GCS_BUCKET_NAME=your-bucket-name
```

5. **Run the application:**
```bash
python app.py
```

The service will be available at `http://localhost:8080`

## Deployment to Google Cloud Run

### Option 1: Using the deployment script (Recommended)

1. **Make the script executable:**
```bash
chmod +x deploy.sh
```

2. **Edit the script variables:**
```bash
# Open deploy.sh and update these variables:
PROJECT_ID="your-actual-project-id"
SERVICE_NAME="weather-data-backend"
REGION="us-central1"
```

3. **Run the deployment script:**
```bash
./deploy.sh
```

### Option 2: Manual deployment

1. **Set up Google Cloud project:**
```bash
gcloud config set project YOUR_PROJECT_ID
```

2. **Enable required APIs:**
```bash
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable storage.googleapis.com
```

3. **Create GCS bucket:**
```bash
gsutil mb gs://your-unique-bucket-name
```

4. **Deploy to Cloud Run:**
```bash
gcloud run deploy weather-data-backend \
    --source . \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --set-env-vars GCS_BUCKET_NAME=your-unique-bucket-name
```

5. **Get the service URL:**
```bash
gcloud run services describe weather-data-backend \
    --platform managed \
    --region us-central1 \
    --format 'value(status.url)'
```

## Testing the API

### Using curl

1. **Test health endpoint:**
```bash
curl https://your-service-url.run.app/health
```

2. **Store weather data:**
```bash
curl -X POST https://your-service-url.run.app/store-weather-data \
  -H "Content-Type: application/json" \
  -d '{
    "latitude": 52.5200,
    "longitude": 13.4050,
    "start_date": "2023-01-01",
    "end_date": "2023-01-31"
  }'
```

3. **List files:**
```bash
curl https://your-service-url.run.app/list-weather-files
```

4. **Get file content:**
```bash
curl https://your-service-url.run.app/weather-file-content/filename.json
```

### Using Python requests

```python
import requests
import json

base_url = "https://your-service-url.run.app"

# Store weather data
response = requests.post(f"{base_url}/store-weather-data", json={
    "latitude": 52.5200,
    "longitude": 13.4050,
    "start_date": "2023-01-01",
    "end_date": "2023-01-31"
})
print(response.json())

# List files
response = requests.get(f"{base_url}/list-weather-files")
print(response.json())
```

## File Naming Convention

Weather data files are stored with the following naming pattern:
```
weather_data_lat{latitude}_lon{longitude}_{start_date}_to_{end_date}_{timestamp}.json
```

Example: `weather_data_lat52.52_lon13.405_2023-01-01_to_2023-01-31_20241123_143022.json`

## Error Handling

The API includes comprehensive error handling for:
- Invalid input validation
- API rate limiting
- Network timeouts
- GCS access errors
- File not found errors
- JSON parsing errors

All errors return appropriate HTTP status codes with descriptive error messages.

## Environment Variables

- `GCS_BUCKET_NAME`: Name of the Google Cloud Storage bucket
- `PORT`: Port number for the service (default: 8080)
- `GOOGLE_CLOUD_PROJECT`: Google Cloud project ID (auto-detected when deployed)

## Monitoring and Logging

The service includes:
- Structured logging using Python's logging module
- Health check endpoint for monitoring
- Request/response logging
- Error tracking and reporting

## Security Considerations

- Input validation for all endpoints
- Coordinate range validation
- Date format validation
- Request size limits
- CORS headers (configure as needed)

## Performance Optimization

- Efficient GCS operations
- Request timeout handling
- Connection pooling
- Minimal memory footprint
- Scalable to handle concurrent requests

## Troubleshooting

### Common Issues

1. **Authentication errors:**
   - Ensure you're authenticated with Google Cloud: `gcloud auth application-default login`
   - Check that the service account has necessary permissions

2. **Bucket access errors:**
   - Verify bucket exists and is accessible
   - Check GCS permissions

3. **API timeout errors:**
   - Check Open-Meteo API status
   - Verify network connectivity

4. **Memory errors:**
   - Increase Cloud Run memory allocation
   - Optimize data processing for large date ranges

### Logs and Debugging

View logs in Google Cloud Console:
```bash
gcloud logs read --service weather-data-backend --limit 50
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For support and questions, please open an issue in the GitHub repository.