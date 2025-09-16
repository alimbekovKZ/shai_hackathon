from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os
import glob
import subprocess
import threading
import time
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI(title="Zoom Meeting Recorder API", version="1.0.0")

# Global storage for active processes
active_processes = {}
recording_files = {}

class StartMeetingResponse(BaseModel):
    status: str
    message: str
    meeting_id: str


def run_meeting_bot_cli(meeting_id: str, meeting_password: str):
    """Run the meeting bot using CLI command in a separate process"""
    try:
        # Get the current directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        cli_script = os.path.join(current_dir, "cli.py")
        
        # Run the CLI command
        cmd = [
            "python3", cli_script,
            "--meeting_id", meeting_id,
            "--meeting_password", meeting_password
        ]
        
        # Start the process
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=current_dir
        )
        
        # Store the process reference
        active_processes[meeting_id] = process
        
        print(f"Started meeting bot process for {meeting_id} with PID {process.pid}")
        
    except Exception as e:
        print(f"Error starting meeting bot for {meeting_id}: {e}")
        if meeting_id in active_processes:
            del active_processes[meeting_id]

@app.get("/start", response_model=StartMeetingResponse)
async def start_meeting(meeting_id: str, meeting_password: str):
    """
    Start a Zoom meeting recording session.
    
    Args:
        meeting_id: The meeting ID to start recording for
        meeting_password: The meeting password
        
    Returns:
        StartMeetingResponse with status and message
    """
    
    # Check if meeting is already running
    if meeting_id in active_processes:
        # Check if process is still running
        process = active_processes[meeting_id]
        if process.poll() is None:  # Process is still running
            return StartMeetingResponse(
                status="error",
                message=f"Meeting {meeting_id} is already running",
                meeting_id=meeting_id
            )
        else:
            # Process has ended, remove it
            del active_processes[meeting_id]
    
    try:
        # Start the meeting bot using CLI in a separate thread
        bot_thread = threading.Thread(
            target=run_meeting_bot_cli,
            args=(meeting_id, meeting_password),
            daemon=True
        )
        bot_thread.start()
        
        # Give the process a moment to start
        time.sleep(2)
        
        # Check if process started successfully
        if meeting_id in active_processes:
            process = active_processes[meeting_id]
            if process.poll() is None:  # Process is running
                return StartMeetingResponse(
                    status="success",
                    message=f"Meeting {meeting_id} recording started successfully",
                    meeting_id=meeting_id
                )
            else:
                # Process failed to start
                stdout, stderr = process.communicate()
                error_msg = stderr.decode() if stderr else "Unknown error"
                del active_processes[meeting_id]
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to start meeting: {error_msg}"
                )
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to start meeting process"
            )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start meeting recording: {str(e)}"
        )

@app.get("/record/{meeting_id}")
async def get_recording(meeting_id: str):
    """
    Get the recording file for a specific meeting.
    
    Args:
        meeting_id: The meeting ID to get recording for
        
    Returns:
        FileResponse with the wav file or HTTPException if not found
    """
    try:
        # Look for the recording file for this meeting
        # The recording files are stored in the out/audio directory
        audio_dir = "/workspace/py-zoom-meeting-sdk/sample_program/sample_program/out/audio"
        
        if not os.path.exists(audio_dir):
            raise HTTPException(
                status_code=404,
                detail="Audio directory not found"
            )
        
        # Look for the specific meeting recording file
        wav_file = os.path.join(audio_dir, f"meeting_recording_{meeting_id}.wav")
        print(wav_file, os.path.exists(wav_file))
        if not os.path.exists(wav_file):
            raise HTTPException(
                status_code=404,
                detail=f"No recording files found for meeting {meeting_id}"
            )
        
        absolute_path = os.path.abspath(wav_file)
        
        # Check if the file exists and has content
        if os.path.exists(absolute_path) and os.path.getsize(absolute_path) > 0:
            return FileResponse(
                path=absolute_path,
                media_type="audio/wav",
                filename=f"meeting_recording_{meeting_id}.wav"
            )
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Recording file exists but is empty or corrupted"
            )
            
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving recording: {str(e)}"
        )

@app.get("/status/{meeting_id}")
async def get_meeting_status(meeting_id: str):
    """
    Get the status of a meeting recording session.
    
    Args:
        meeting_id: The meeting ID to check status for
        
    Returns:
        Dictionary with meeting status information
    """
    is_running = False
    process_info = None
    
    if meeting_id in active_processes:
        process = active_processes[meeting_id]
        if process.poll() is None:  # Process is running
            is_running = True
            process_info = {
                "pid": process.pid,
                "status": "running"
            }
        else:
            # Process has ended
            process_info = {
                "pid": process.pid,
                "status": "ended",
                "return_code": process.returncode
            }
            # Clean up the ended process
            del active_processes[meeting_id]
    
    # Check for recording files
    audio_dir = "sample_program/out/audio"
    has_recording = False
    latest_recording = None
    
    if os.path.exists(audio_dir):
        wav_file = os.path.join(audio_dir, f"meeting_recording_{meeting_id}.wav")
        if os.path.exists(wav_file):
            has_recording = True
            latest_recording = wav_file
    
    return {
        "meeting_id": meeting_id,
        "is_running": is_running,
        "process_info": process_info,
        "has_recording": has_recording,
        "latest_recording": latest_recording
    }

@app.post("/stop/{meeting_id}")
async def stop_meeting(meeting_id: str):
    """
    Stop a running meeting recording session.
    
    Args:
        meeting_id: The meeting ID to stop
        
    Returns:
        Dictionary with stop status
    """
    if meeting_id not in active_processes:
        raise HTTPException(
            status_code=404,
            detail=f"No active meeting found for {meeting_id}"
        )
    
    process = active_processes[meeting_id]
    
    try:
        # Terminate the process
        process.terminate()
        
        # Wait for graceful termination
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            # Force kill if it doesn't terminate gracefully
            process.kill()
            process.wait()
        
        del active_processes[meeting_id]
        
        return {
            "status": "success",
            "message": f"Meeting {meeting_id} stopped successfully"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error stopping meeting: {str(e)}"
        )

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Zoom Meeting Recorder API",
        "version": "1.0.0",
        "endpoints": {
            "start": "GET /start?meeting_id={id}&meeting_password={password} - Start meeting recording",
            "record": "GET /record/{meeting_id} - Download recording wav file",
            "status": "GET /status/{meeting_id} - Get meeting status",
            "stop": "POST /stop/{meeting_id} - Stop meeting recording"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
