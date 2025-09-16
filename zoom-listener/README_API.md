# Zoom Meeting Recorder API

This FastAPI application provides REST endpoints to start Zoom meeting recordings and retrieve recorded audio files.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Make sure you have the required environment variables set in a `.env` file:
```
MEETING_ID=your_meeting_id
MEETING_PWD=your_meeting_password
ZOOM_APP_CLIENT_ID=your_zoom_app_client_id
ZOOM_APP_CLIENT_SECRET=your_zoom_app_client_secret
```

## Running the API

Start the FastAPI server:
```bash
python api.py
```

Or using uvicorn directly:
```bash
uvicorn api:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at `http://localhost:8000`

## API Endpoints

### 1. Start Meeting Recording

**POST** `/start`

Start a Zoom meeting recording session.

**Request Body:**
```json
{
  "meeting_id": "83300774340",
  "meeting_password": "your_password"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Meeting 83300774340 recording started successfully",
  "meeting_id": "83300774340"
}
```

### 2. Get Recording File

**GET** `/record/{meeting_id}`

Get the absolute path to the recorded WAV file for a specific meeting.

**Response:**
```json
{
  "status": "success",
  "file_path": "/absolute/path/to/meeting_recording_20250916_131103.wav",
  "message": "Recording found for meeting 83300774340"
}
```

### 3. Get Meeting Status

**GET** `/status/{meeting_id}`

Get the current status of a meeting recording session.

**Response:**
```json
{
  "meeting_id": "83300774340",
  "is_running": true,
  "has_recording": true,
  "latest_recording": "sample_program/out/audio/meeting_recording_20250916_131103.wav"
}
```

### 4. API Information

**GET** `/`

Get basic API information and available endpoints.

## Testing

Run the test script to verify the API functionality:
```bash
python test_api.py
```

## Example Usage with curl

### Start a meeting:
```bash
curl -X POST "http://localhost:8000/start" \
     -H "Content-Type: application/json" \
     -d '{
       "meeting_id": "83300774340",
       "meeting_password": "your_password"
     }'
```

### Get recording file:
```bash
curl -X GET "http://localhost:8000/record/83300774340"
```

### Check meeting status:
```bash
curl -X GET "http://localhost:8000/status/83300774340"
```

## Notes

- The meeting bot runs in a separate thread and will continue recording until manually stopped
- Recording files are saved in the `sample_program/out/audio/` directory
- Files are named with timestamps: `meeting_recording_YYYYMMDD_HHMMSS.wav`
- The API returns the most recent recording file for a given meeting ID
- Make sure the Zoom SDK is properly configured and the meeting credentials are valid

## Error Handling

The API includes comprehensive error handling:
- Invalid meeting credentials
- Missing environment variables
- File system errors
- Network connectivity issues

All errors are returned with appropriate HTTP status codes and descriptive error messages.
