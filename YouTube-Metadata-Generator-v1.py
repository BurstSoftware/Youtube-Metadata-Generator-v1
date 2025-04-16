import streamlit as st
import google.generativeai as genai
from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi
import re
import os

# Streamlit page configuration
st.set_page_config(page_title="YouTube Metadata Generator", page_icon="📺")
st.title("📺 YouTube Video Metadata Generator")
st.markdown("Enter a YouTube video title or URL to generate an optimized title, description, and tags using Google AI Studio and YouTube Data API.")

# Input fields
video_input = st.text_input("Enter YouTube Video Title or URL", placeholder="e.g., 'Best Python Tutorial 2025' or 'https://www.youtube.com/watch?v=VIDEO_ID'")
generate_button = st.button("Generate Metadata")

# Load API keys from Streamlit secrets
try:
    GOOGLE_AI_API_KEY = st.secrets["GOOGLE_AI_API_KEY"]
    YOUTUBE_API_KEY = st.secrets["YOUTUBE_API_KEY"]
except KeyError:
    st.error("API keys not found in secrets. Please add GOOGLE_AI_API_KEY and YOUTUBE_API_KEY to .streamlit/secrets.toml.")
    st.stop()

# Initialize Google AI Studio (Gemini)
genai.configure(api_key=GOOGLE_AI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-pro")

# Initialize YouTube Data API
youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

def extract_video_id(url_or_title):
    """Extract YouTube video ID from URL or return None if input is a title."""
    video_id_pattern = r"(?:v=|\/)([0-9A-Za-z_-]{11}).*"
    match = re.search(video_id_pattern, url_or_title)
    return match.group(1) if match else None

def fetch_youtube_details(video_id):
    """Fetch video details using YouTube Data API."""
    try:
        request = youtube.videos().list(part="snippet", id=video_id)
        response = request.execute()
        if response["items"]:
            snippet = response["items"][0]["snippet"]
            return {
                "title": snippet["title"],
                "description": snippet.get("description", ""),
                "tags": snippet.get("tags", [])
            }
        return None
    except Exception as e:
        st.warning(f"Error fetching YouTube details: {e}")
        return None

def get_transcript(video_id):
    """Fetch video transcript if available."""
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        return " ".join([item["text"] for item in transcript])
    except Exception:
        return ""

def generate_metadata(title, transcript=""):
    """Generate optimized title, description, and tags using Gemini API."""
    prompt = f"""
    You are an expert YouTube SEO strategist. Given the video title '{title}' and optional transcript context, generate:
    1. An SEO-optimized YouTube video title (max 100 characters, aim for 60-70).
    2. A compelling video description (min 250, max 5000 characters, include keywords, timestamps, and CTA).
    3. A list of 5-10 relevant tags (max 500 characters total, each tag max 30 characters).

    Context (if available): {transcript[:1000]}...

    Ensure the title is engaging and keyword-rich, the description is scannable with bullet points and emojis, and tags are specific and relevant to the topic.
    """
    try:
        response = model.generate_content(prompt)
        text = response.text.strip()

        # Parse the response (assuming Gemini returns structured text)
        title_match = re.search(r"Title:\s*(.+)", text)
        description_match = re.search(r"Description:\s*([\s\S]+?)Tags:", text, re.DOTALL)
        tags_match = re.search(r"Tags:\s*([\s\S]+)", text)

        generated_title = title_match.group(1).strip() if title_match else title
        generated_description = description_match.group(1).strip() if description_match else "No description generated."
        generated_tags = tags_match.group(1).strip().split("\n") if tags_match else []

        return {
            "title": generated_title[:100],
            "description": generated_description[:5000],
            "tags": generated_tags[:10]  # Limit to 10 tags
        }
    except Exception as e:
        st.error(f"Error generating metadata: {e}")
        return None

# Main logic
if generate_button and video_input:
    video_id = extract_video_id(video_input)
    transcript = ""
    input_title = video_input

    # If a video ID is extracted, fetch details and transcript
    if video_id:
        st.info("Detected YouTube URL. Fetching video details...")
        details = fetch_youtube_details(video_id)
        if details:
            input_title = details["title"]
            st.subheader("Original Video Details")
            st.write(f"**Title**: {details['title']}")
            st.write(f"**Description**: {details['description'][:200]}...")
            st.write(f"**Tags**: {', '.join(details['tags'])}")
            transcript = get_transcript(video_id)

    # Generate metadata using Gemini
    st.subheader("Generated Metadata")
    metadata = generate_metadata(input_title, transcript)
    if metadata:
        st.write(f"**Optimized Title**: {metadata['title']}")
        st.write(f"**Optimized Description**:")
        st.markdown(metadata['description'])
        st.write(f"**Optimized Tags**: {', '.join(metadata['tags'])}")
    else:
        st.error("Failed to generate metadata. Please try again.")
else:
    st.info("Enter a video title or URL and click 'Generate Metadata' to start.")

# Footer
st.markdown("---")
st.markdown("Built with Streamlit, Google AI Studio, and YouTube Data API. Ensure API keys are set in `.streamlit/secrets.toml`.")
