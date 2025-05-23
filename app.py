from flask import Flask, request, jsonify
import requests
from google.cloud import storage
import json
import os
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuration
BUCKET_NAME = os.environ.get('GCS_BUCKET_NAME', 'weather-data-bucket')
OPEN_METEO_BASE_URL = 'https://archive-api.open-meteo.com/v1/archive'

# Global variable for storage client
storage_client = None


def get_storage_client():
    """Get or create the GCS client with lazy initialization"""
    global storage_client
    if storage_client is None:
        # Check if running in local development mode
        if os.environ.get('DEVELOPMENT_MODE') == 'true':
            logger.warning("Running in development mode - GCS operations will be mocked")
            return None
        try:
            storage_client = storage.Client()
        except Exception as e:
            logger.error(f"Failed to initialize GCS client: {str(e)}")
            if os.environ.get('MOCK_GCS') == 'true':
                logger.info("Using mock GCS client")
                return None
            raise
    return storage_client


def get_bucket():
    """Get or create the GCS bucket"""
    client = get_storage_client()
    if client is None:
        logger.info("Mock mode: Skipping bucket operations")
        return None
    
    try:
        bucket = client.bucket(BUCKET_NAME)
        if not bucket.exists():
            bucket = client.create_bucket(BUCKET_NAME)
            logger.info(f"Created bucket: {BUCKET_NAME}")
        return bucket
    except Exception as e:
        logger.error(f"Error accessing bucket: {str(e)}")
        raise


def generate_filename(latitude, longitude, start_date, end_date):
    """Generate a unique filename for the weather data"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"weather_data_lat{latitude}_lon{longitude}_{start_date}_to_{end_date}_{timestamp}.json"


def fetch_weather_data(latitude, longitude, start_date, end_date):
    """Fetch weather data from Open-Meteo API"""
    params = {
        'latitude': latitude,
        'longitude': longitude,
        'start_date': start_date,
        'end_date': end_date,
        'daily': [
            'temperature_2m_max',
            'temperature_2m_min',
            'temperature_2m_mean',
            'apparent_temperature_max',
            'apparent_temperature_min',
            'apparent_temperature_mean'
        ]
    }
    
    try:
        response = requests.get(OPEN_METEO_BASE_URL, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching weather data: {str(e)}")
        raise


def validate_date_format(date_string):
    """Validate date format YYYY-MM-DD"""
    try:
        datetime.strptime(date_string, '%Y-%m-%d')
        return True
    except ValueError:
        return False


def validate_coordinates(latitude, longitude):
    """Validate latitude and longitude values"""
    if not isinstance(latitude, (int, float)) or not isinstance(longitude, (int, float)):
        return False
    if not (-90 <= latitude <= 90) or not (-180 <= longitude <= 180):
        return False
    return True


@app.route('/store-weather-data', methods=['POST'])
def store_weather_data():
    """Store weather data from Open-Meteo API to GCS"""
    try:
        # Validate request body
        if not request.is_json:
            return jsonify({'error': 'Request must be JSON'}), 400
        
        data = request.get_json()
        required_fields = ['latitude', 'longitude', 'start_date', 'end_date']
        
        # Check for required fields
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        latitude = data['latitude']
        longitude = data['longitude']
        start_date = data['start_date']
        end_date = data['end_date']
        
        # Validate coordinates
        if not validate_coordinates(latitude, longitude):
            return jsonify({'error': 'Invalid latitude or longitude values'}), 400
        
        # Validate date formats
        if not validate_date_format(start_date) or not validate_date_format(end_date):
            return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
        
        # Validate date range
        if start_date > end_date:
            return jsonify({'error': 'start_date must be before or equal to end_date'}), 400
        
        # Fetch weather data
        weather_data = fetch_weather_data(latitude, longitude, start_date, end_date)
        
        # Generate filename
        filename = generate_filename(latitude, longitude, start_date, end_date)
        
        # Store in GCS
        bucket = get_bucket()
        if bucket is None:
            # Mock mode - just log the data
            logger.info(f"Mock mode: Would store weather data with filename: {filename}")
            logger.info(f"Mock mode: Weather data size: {len(json.dumps(weather_data))} bytes")
        else:
            blob = bucket.blob(filename)
            blob.upload_from_string(
                json.dumps(weather_data, indent=2),
                content_type='application/json'
            )
        
        logger.info(f"Successfully stored weather data: {filename}")
        
        return jsonify({
            'message': 'Weather data stored successfully',
            'filename': filename,
            'location': {
                'latitude': latitude,
                'longitude': longitude
            },
            'date_range': {
                'start_date': start_date,
                'end_date': end_date
            }
        }), 201
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Weather API error: {str(e)}")
        return jsonify({'error': 'Failed to fetch weather data from Open-Meteo API'}), 502
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/list-weather-files', methods=['GET'])
def list_weather_files():
    """List all weather data files in GCS bucket"""
    try:
        bucket = get_bucket()
        if bucket is None:
            # Mock mode - return empty list
            logger.info("Mock mode: Returning empty file list")
            return jsonify({
                'files': [],
                'count': 0,
                'message': 'Running in mock mode - no files available'
            }), 200
        
        blobs = bucket.list_blobs()
        
        files = []
        for blob in blobs:
            files.append({
                'filename': blob.name,
                'size': blob.size,
                'created': blob.time_created.isoformat() if blob.time_created else None,
                'updated': blob.updated.isoformat() if blob.updated else None
            })
        
        return jsonify({
            'files': files,
            'count': len(files)
        }), 200
        
    except Exception as e:
        logger.error(f"Error listing files: {str(e)}")
        return jsonify({'error': 'Failed to list files'}), 500


@app.route('/weather-file-content/<filename>', methods=['GET'])
def get_weather_file_content(filename):
    """Get content of a specific weather data file from GCS"""
    try:
        bucket = get_bucket()
        if bucket is None:
            # Mock mode - return sample data
            logger.info(f"Mock mode: Returning sample data for filename: {filename}")
            return jsonify({
                'filename': filename,
                'message': 'Running in mock mode - sample data returned',
                'data': {
                    'latitude': 52.52,
                    'longitude': 13.41,
                    'daily': {
                        'time': ['2023-01-01'],
                        'temperature_2m_max': [5.0],
                        'temperature_2m_min': [-2.0]
                    }
                }
            }), 200
        
        blob = bucket.blob(filename)
        
        if not blob.exists():
            return jsonify({'error': 'File not found'}), 404
        
        # Download and parse JSON content
        content = blob.download_as_text()
        weather_data = json.loads(content)
        
        return jsonify({
            'filename': filename,
            'data': weather_data
        }), 200
        
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON in file: {filename}")
        return jsonify({'error': 'Invalid JSON file'}), 500
    except Exception as e:
        logger.error(f"Error retrieving file content: {str(e)}")
        return jsonify({'error': 'Failed to retrieve file content'}), 500


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'weather-data-backend'
    }), 200


@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404


@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({'error': 'Method not allowed'}), 405


@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    # For local development
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=True)