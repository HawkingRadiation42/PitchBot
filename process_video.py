import cv2
import math
import os
import whisper
import base64
import requests
from dotenv import load_dotenv
import concurrent.futures
import shutil

load_dotenv()

def encode_image(image_data):
    # Encode the in-memory image data (NumPy array)
    success, buffer = cv2.imencode('.jpg', image_data)
    if not success:
        raise ValueError("Could not encode image to JPEG format.")
    return base64.b64encode(buffer).decode('utf-8')

def call_llama_api(prompt, images=None, max_tokens=5000):
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

def process_video(video_path: str, evaluation_prompt: str):
    """
    Processes a video by analyzing it in chunks and then performing a final evaluation.
    """
    output_dir = "output"
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir)
        
    # 1. Extract frames from the video
    print("Extracting frames...")
    video = cv2.VideoCapture(video_path)
    fps = video.get(cv2.CAP_PROP_FPS)
    target_fps = 15
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

    # 2. Extract audio from the video
    print("Extracting audio...")
    audio_path = os.path.join(output_dir, "audio.mp3")
    command = f"ffmpeg -i {video_path} -q:a 0 -map a {audio_path} -y"
    os.system(command)
    print(f"Audio extracted and saved to {audio_path}")
    
    # 3. Transcribe audio using Whisper
    print("Transcribing audio...")
    model = whisper.load_model("base")
    result = model.transcribe(audio_path, fp16=False) # fp16=False if not using a GPU
    transcript = result["text"]
    print("Transcription complete.")
    print(f"Transcript: {transcript if transcript else 'No speech detected.'}")

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
        print("\n[DEBUG] First Segment Summary:\n", segment_summaries[0])
        print("\n[DEBUG] Last Segment Summary:\n", segment_summaries[-1])
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
        
        print("\n[DEBUG] Raw API Response from Stage 2:\n", final_response)

        completion_message = final_response.get('completion_message', {})
        content = completion_message.get('content', {})
        final_evaluation = content.get('text', '') if isinstance(content, dict) else content

        print("\n--- Final Evaluation ---")
        print(final_evaluation)
    except requests.exceptions.HTTPError as e:
        print(f"Final synthesis API call failed: {e}")
        if e.response is not None:
            print(f"[DEBUG] Response Body: {e.response.text}")
    except Exception as e:
        print(f"An unexpected error occurred during final synthesis: {e}")

    print("\nVideo processing complete.")
    return final_evaluation

# Example usage:
if __name__ == '__main__':
    # You would replace 'path/to/your/video.mp4' with the actual video file path
    # and provide your own prompt.
    # For now, let's create a dummy file to test.
    
    # Create a dummy video file for testing purposes
    # In a real scenario, you would have your own video file.
    data_dir = "data"
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)

    video_file = os.path.join(data_dir, "test.mp4")

    if not os.path.exists(video_file):
        print("Creating a dummy video file for testing...")
        # This requires ffmpeg to be installed
        os.system(f"ffmpeg -f lavfi -i sine=frequency=440:duration=5 -f lavfi -i testsrc=size=1920x1080:rate=30 -t 5 -pix_fmt yuv420p {video_file} -y")

    # This prompt is now used within the final, more detailed system prompt.
    user_prompt = "evaluate the demo of a idea, confidence presentation skills and how well was the idea pitched."
    
    if os.path.exists(video_file):
        process_video(video_file, user_prompt)
    else:
        print(f"Test video file '{video_file}' not found. Please provide a valid video file.") 