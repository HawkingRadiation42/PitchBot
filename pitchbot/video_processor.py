import cv2
import math
import os
import base64
import requests
import whisper
import time
from typing import Optional
from fastapi import UploadFile
import concurrent.futures
import tempfile
import subprocess
import numpy as np

def encode_image(image_data):
    # Encode the in-memory image data (NumPy array)
    success, buffer = cv2.imencode('.jpg', image_data)
    if not success:
        raise ValueError("Could not encode image to JPEG format.")
    return base64.b64encode(buffer).decode('utf-8')

def call_llama_api(prompt, images=None, max_tokens=30000):
    """
    Sends a request to the Llama API with a prompt and optional images.
    """
    api_key = os.getenv("LLAMA_API_KEY")
    if not api_key:
        raise ValueError("API key not found. Please check your .env file.")

    api_endpoint = "https://api.llama.com/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    content = [{"type": "text", "text": prompt}]
    if images:
        for img_data in images:
            base64_image = encode_image(img_data)
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{base64_image}"
                }
            })

    payload = {
        "model": "Llama-4-Maverick-17B-128E-Instruct-FP8",
        "messages": [{"role": "user", "content": content}],
        "max_tokens": max_tokens
    }

    response = requests.post(api_endpoint, headers=headers, json=payload)
    response.raise_for_status()  # Will raise an exception for bad status codes
    return response.json()

def analyze_segment(args):
    """
    Analyzes a single segment of the video. Designed to be run in a parallel thread.
    """
    i, chunk, transcript, total_chunks = args
    print(f"Analyzing segment {i+1}/{total_chunks}...")
    segment_prompt = (
        "You are an AI assistant analyzing a video of a startup pitch. "
        f"The full transcript of the presentation audio is: '{transcript}'.\n\n"
        "Based ONLY on the following 9 images from this segment, list all key observations. "
        "Do not summarize or omit details. Note the presenter's specific actions, emotional state (e.g., confidence, nervousness), "
        "and precisely what is written or shown on any slides or visual aids. Be exhaustive."
    )
    
    try:
        api_response = call_llama_api(segment_prompt, images=chunk, max_tokens=30000)
        content = api_response.get('completion_message', {}).get('content', {})
        summary = content.get('text', '') if isinstance(content, dict) else content
        print(f"Segment {i+1} analysis complete.")
        return summary
    except Exception as e:
        error_message = f"Analysis for segment {i+1} failed due to: {e}"
        print(error_message)
        return error_message

def format_video_analysis(filename: str, transcript: str, total_frames: int, segments_analyzed: int, final_evaluation: str) -> str:
    """
    Format the video analysis into a structured report similar to PDF and company analysis.
    """
    # Basic statistics
    transcript_word_count = len(transcript.split()) if transcript else 0
    transcript_length = len(transcript) if transcript else 0
    
    report_lines = []
    
    # Header
    report_lines.append("=" * 80)
    report_lines.append("🎥 VIDEO PITCH ANALYSIS REPORT")
    report_lines.append("=" * 80)
    
    # Video Information
    report_lines.append("\n📋 VIDEO INFORMATION:")
    report_lines.append("-" * 40)
    report_lines.append(f"Filename: {filename}")
    report_lines.append(f"Total Frames Analyzed: {total_frames}")
    report_lines.append(f"Video Segments: {segments_analyzed}")
    report_lines.append(f"Analysis Method: AI-powered frame and audio analysis")
    
    # Transcript Statistics
    report_lines.append("\n📊 AUDIO TRANSCRIPT STATISTICS:")
    report_lines.append("-" * 40)
    report_lines.append(f"Word Count: {transcript_word_count}")
    report_lines.append(f"Character Count: {transcript_length}")
    report_lines.append(f"Transcript Available: {'Yes' if transcript else 'No audio detected'}")
    
    # Processing Summary
    report_lines.append("\n🔄 PROCESSING SUMMARY:")
    report_lines.append("-" * 40)
    report_lines.append(f"Frame Extraction: ✅ Complete ({total_frames} frames)")
    report_lines.append(f"Audio Extraction: ✅ Complete")
    report_lines.append(f"Transcript Generation: ✅ Complete")
    report_lines.append(f"Segment Analysis: ✅ Complete ({segments_analyzed} segments)")
    report_lines.append(f"Final Synthesis: ✅ Complete")
    
    # Full Analysis
    report_lines.append("\n📝 COMPREHENSIVE PITCH EVALUATION:")
    report_lines.append("-" * 40)
    report_lines.append(final_evaluation)
    
    # Footer
    report_lines.append("\n" + "=" * 80)
    
    return "\n".join(report_lines)

async def process_video(video_file: UploadFile):
    """
    Processes a video file from memory by extracting its own audio, transcribing it,
    analyzing video frames, and performing final evaluation. Completely independent from MP3 processing.
    """
    if not video_file or not video_file.filename:
        return "No video file provided."

    print(f"🎥 Video processing started for: {video_file.filename}")

    # Use temporary files for video processing
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_video, \
         tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_audio:
        
        try:
            # Write video content to temp file
            content = await video_file.read()
            temp_video.write(content)
            temp_video.flush()
            video_path = temp_video.name
            audio_path = temp_audio.name

            # 1. Extract frames from the video
            print("Extracting frames...")
            video = cv2.VideoCapture(video_path)
            fps = video.get(cv2.CAP_PROP_FPS)
            target_fps = 5
            frame_interval = math.ceil(fps / target_fps)
            
            frames = []
            frame_count = 0
            while True:
                ret, frame = video.read()
                if not ret:
                    break
                
                if frame_count % frame_interval == 0:
                    frames.append(frame)
                    
                frame_count += 1
                
            video.release()
            print(f"Extracted {len(frames)} frames.")

            # 2. Extract audio from the video using ffmpeg
            print("Extracting audio from video...")
            command = ["ffmpeg", "-i", video_path, "-q:a", "0", "-map", "a", audio_path, "-y"]
            result = subprocess.run(command, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"FFmpeg error: {result.stderr}")
                raise Exception(f"Failed to extract audio: {result.stderr}")
            print(f"Audio extracted from video")
            
            # 3. Transcribe audio using Whisper
            print("Transcribing video audio...")
            model = whisper.load_model("base")
            result = model.transcribe(audio_path, fp16=False)
            transcript = result["text"]
            print("Video transcription complete.")
            print(f"Video transcript: {transcript if transcript else 'No speech detected.'}")

            # STAGE 1: Segment Analysis (Parallelized)
            print("\n--- Starting Stage 1: Segment Analysis ---")
            frame_chunks = [frames[i:i + 9] for i in range(0, len(frames), 9)]
            
            total_chunks = len(frame_chunks)
            tasks = [(i, chunk, transcript, total_chunks) for i, chunk in enumerate(frame_chunks)]
            
            segment_summaries = []
            with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
                print(f"Submitting {total_chunks} segments for parallel analysis (up to 20 at a time)...")
                results = executor.map(analyze_segment, tasks)
                segment_summaries = list(results)
            
            print("--- All segments have been analyzed. ---")

            # Verify Stage 1 output
            print("\n--- Verifying Stage 1 Output ---")
            if segment_summaries:
                # print("\n[DEBUG] First Segment Summary:\n", segment_summaries[0])
                # print("\n[DEBUG] Last Segment Summary:\n", segment_summaries[-1])
                pass
            else:
                print("[DEBUG] No segment summaries were generated.")

            # STAGE 2: Final Synthesis
            print("\n--- Starting Stage 2: Final Synthesis ---")
            
            all_summaries = "\n".join(f"Segment {i+1}: {s}" for i, s in enumerate(segment_summaries) if s)
            
            final_prompt = (
                "You are a senior analyst at a top-tier venture capital firm. Your task is to process the following data "
                "from a startup pitch and compile a comprehensive dossier for the investment committee. Your analysis must be "
                "exhaustive and grounded in the provided facts.\n\n"
                "--- DATA ---\n"
                f"Full Audio Transcript:\n'{transcript}'\n\n"
                f"Sequential Visual Observations:\n{all_summaries}\n\n"
                "--- DOSSIER ---\n"
                "Based on ALL available data (audio and visual), compile the following report.\n\n"
                "**Part 1: Raw Data Extraction & Factual Observations**\n\n"
                "1.  **Core Message:**\n"
                "    - **Problem Identified:** (Summarize the exact problem as stated in the transcript).\n"
                "    - **Proposed Solution (The 'What'):** (Describe the product/service based on the transcript and visuals).\n"
                "    - **Value Proposition (The 'Why'):** (Explain why this solution is better/different, citing transcript and visuals).\n\n"
                "2.  **Presenter Analysis (Objective Observations):**\n"
                "    - **Audible Cues:** (From the transcript, analyze the speaker's pace, clarity, use of filler words, and any noticeable changes in tone).\n"
                "    - **Visual Cues:** (From the visual observations, describe the presenter's attire, background, apparent body language, and use of gestures).\n\n"
                "3.  **Visual Aids Analysis (Objective Observations):**\n"
                "    - **Slide Quality:** (Comment on the design, clarity, and professionalism of the slides shown in the visual observations).\n"
                "    - **Demo Walkthrough:** (Describe the steps and outcomes of the product demo as seen in the visuals and described in the audio).\n"
                "    - **Key Data Presented:** (List any specific numbers, charts, graphs, or key metrics that were visually presented or mentioned in the transcript).\n\n"
                "**Part 2: Investment Committee Evaluation**\n\n"
                "Synthesize the raw data from Part 1 to provide the following evaluation.\n\n"
                "1.  **Idea & Market:**\n"
                "    - **Assessment:** (Analyze the clarity, innovation, and market potential of the idea, referencing facts from Part 1).\n\n"
                "2.  **Presentation & Communication:**\n"
                "    - **Assessment:** (Analyze the presenter's confidence, professionalism, and the clarity of their narrative, combining visual and audible cues from Part 1).\n\n"
                "3.  **Overall Pitch & Execution:**\n"
                "    - **Assessment:** (Evaluate the pitch structure, the effectiveness of the visual aids, and how well the demo supported the core claims, using data from Part 1).\n\n"
                "**Final Recommendation:** (Provide a concluding summary and a final recommendation: 'Strongly Recommend,' 'Recommend,' 'Consider,' or 'Pass')."
            )
            
            try:
                print("Sending final request for comprehensive evaluation...")
                final_response = call_llama_api(final_prompt, max_tokens=100000)
                
                # print("\n[DEBUG] Raw API Response from Stage 2:\n", final_response)

                completion_message = final_response.get('completion_message', {})
                content = completion_message.get('content', {})
                final_evaluation = content.get('text', '') if isinstance(content, dict) else content

                print("\n--- Final Evaluation ---")
                print(final_evaluation)
                
                # Structure the video analysis response
                structured_response = format_video_analysis(
                    video_file.filename,
                    transcript,
                    len(frames),
                    len(segment_summaries),
                    final_evaluation
                )
                
                print("\nVideo processing complete.")
                return structured_response
            except requests.exceptions.HTTPError as e:
                print(f"Final synthesis API call failed: {e}")
                if e.response is not None:
                    print(f"[DEBUG] Response Body: {e.response.text}")
                return f"Final synthesis failed: {e}"
            except Exception as e:
                print(f"An unexpected error occurred during final synthesis: {e}")
                return f"Video processing failed: {e}"
                
        finally:
            # Clean up temporary files
            try:
                os.unlink(video_path)
                os.unlink(audio_path)
            except:
                pass 