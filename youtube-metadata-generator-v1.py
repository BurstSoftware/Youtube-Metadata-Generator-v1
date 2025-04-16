import streamlit as st
import google.generativeai as genai
import re

# Streamlit page configuration
st.set_page_config(page_title="YouTube Metadata Generator", page_icon="📺")
st.title("📺 YouTube Video Metadata Generator")
st.markdown("Enter your Gemini API key and a video title to generate an optimized YouTube title, description, and tags using the Google Gemini API.")

# Input fields
api_key = st.text_input("Enter your Gemini API Key", type="password", placeholder="e.g., AIzaSyD...your-api-key")
video_title = st.text_input("Enter YouTube Video Title", placeholder="e.g., Best Python Tutorial 2025")
generate_button = st.button("Generate Metadata")

def generate_metadata(api_key, title):
    """Generate optimized title, description, and tags using Gemini API."""
    try:
        # Configure Gemini API with user-provided key
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.0-flash")

        # Construct prompt
        prompt = f"""
You are an expert YouTube SEO strategist. Given the video title '{title}', generate:
1. An SEO-optimized YouTube video title (max 100 characters, aim for 60-70).
2. A compelling video description (min 250, max 5000 characters, include keywords, timestamps, and CTA).
3. A list of 5-10 relevant tags (max 500 characters total, each tag max 30 characters).

Ensure the title is engaging and keyword-rich, the description is scannable with bullet points and emojis, and tags are specific and relevant to the topic. Format the output clearly with 'Title:', 'Description:', and 'Tags:' labels.
"""

        # Generate content
        response = model.generate_content(prompt)
        text = response.text.strip()

        # Parse the response
        title_match = re.search(r"Title:\s*(.+)", text)
        description_match = re.search(r"Description:\s*([\s\S]+?)Tags:", text, re.DOTALL)
        tags_match = re.search(r"Tags:\s*([\s\S]+)", text)

        generated_title = title_match.group(1).strip() if title_match else title
        generated_description = description_match.group(1).strip() if description_match else "No description generated."
        generated_tags = tags_match.group(1).strip().split("\n") if tags_match else []

        return {
            "title": generated_title[:100],
            "description": generated_description[:5000],
            "tags": [tag.strip() for tag in generated_tags if tag.strip()][:10]  # Limit to 10 tags
        }
    except Exception as e:
        st.error(f"Error generating metadata: {e}")
        return None

# Main logic
if generate_button:
    if not api_key:
        st.error("Please enter a valid Gemini API key.")
    elif not video_title:
        st.error("Please enter a video title.")
    else:
        st.subheader("Generated Metadata")
        metadata = generate_metadata(api_key, video_title)
        if metadata:
            st.write(f"**Optimized Title**: {metadata['title']} ({len(metadata['title'])} characters)")
            st.write(f"**Optimized Description**: ({len(metadata['description'])} characters)")
            st.markdown(metadata['description'])
            st.write(f"**Optimized Tags**: {', '.join(metadata['tags'])} ({len(','.join(metadata['tags']))} characters)")
        else:
            st.error("Failed to generate metadata. Please check your API key or try again.")
else:
    st.info("Enter your Gemini API key and a video title, then click 'Generate Metadata' to start.")

# Footer
st.markdown("---")
st.markdown("Built with Streamlit and Google Gemini API (gemini-2.0-flash).")
