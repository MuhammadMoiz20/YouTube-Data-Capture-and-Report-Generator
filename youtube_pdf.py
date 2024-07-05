# Import necessary libraries
from googleapiclient.discovery import build
import pandas as pd
import re
import requests
from PIL import Image
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet

# Replace with API key
api_key = 'Insert API Key here'

# Create a YouTube API client
youtube = build('youtube', 'v3', developerKey=api_key)

def get_channel_and_video_id_from_url(youtube, url):
    if 'youtube.com/watch' in url:
        video_id = re.search(r"v=([^&]+)", url).group(1)
        request = youtube.videos().list(part="snippet", id=video_id)
        response = request.execute()
        channel_id = response['items'][0]['snippet']['channelId']
        return channel_id, video_id
    else:
        raise ValueError("Invalid YouTube video URL")

# get channel details
def get_channel_details(youtube, channel_id):
    request = youtube.channels().list(
        part="snippet,contentDetails,statistics",
        id=channel_id
    )
    response = request.execute()
    return response

# get video details
def get_video_details(youtube, video_id):
    request = youtube.videos().list(
        part="snippet,contentDetails,statistics",
        id=video_id
    )
    response = request.execute()
    return response

# Function to get comments for a video
def get_video_comments(youtube, video_id):
    comments = []
    request = youtube.commentThreads().list(
        part="snippet",
        videoId=video_id,
        maxResults=100
    )
    response = request.execute()
    
    while request is not None:
        for item in response['items']:
            comment = item['snippet']['topLevelComment']['snippet']
            comments.append({
                'author': comment['authorDisplayName'],
                'text': comment['textDisplay'],
                'likeCount': comment['likeCount'],
                'publishedAt': comment['publishedAt']
            })
        request = youtube.commentThreads().list_next(request, response)
        if request:
            response = request.execute()
        else:
            break
    return comments

# Capture thumbnail image
def get_thumbnail_image(youtube, video_id):
    video_details = get_video_details(youtube, video_id)
    thumbnail_url = video_details['items'][0]['snippet']['thumbnails']['high']['url']
    response = requests.get(thumbnail_url)
    img = Image.open(BytesIO(response.content))
    return img

# generate PDF
def generate_pdf(channel_info, video_info, comments, thumbnail_image, output_path):
    c = canvas.Canvas(output_path, pagesize=letter)
    width, height = letter
    styles = getSampleStyleSheet()

    # Add channel information
    c.setFont("Helvetica-Bold", 16)
    c.drawString(72, height - 72, "YouTube Channel Information")
    c.setFont("Helvetica", 12)
    y_position = height - 100

    for key, value in channel_info.items():
        c.drawString(72, y_position, f"{key.capitalize()}: {value}")
        y_position -= 20

    # Add video information
    c.setFont("Helvetica-Bold", 16)
    y_position -= 40
    c.drawString(72, y_position, "Video Information")
    c.setFont("Helvetica", 12)
    y_position -= 20

    for key, value in video_info.items():
        c.drawString(72, y_position, f"{key.capitalize()}: {value}")
        y_position -= 20

    # Add thumbnail image
    if thumbnail_image:
        y_position -= 200  # Space for the image
        thumbnail_path = "/tmp/thumbnail.jpg"
        thumbnail_image.save(thumbnail_path)
        c.drawImage(thumbnail_path, 72, y_position, width=200, height=150)
        y_position -= 160  # Adjust space after the image

    # Add comments
    c.setFont("Helvetica-Bold", 16)
    y_position -= 40
    c.drawString(72, y_position, "Comments")
    c.setFont("Helvetica", 12)
    y_position -= 20

    for comment in comments:
        for key, value in comment.items():
            c.drawString(72, y_position, f"{key.capitalize()}: {value}")
            y_position -= 20
        y_position -= 10
        c.drawString(72, y_position, "-" * 80)
        y_position -= 20
        if y_position < 100:
            c.showPage()
            c.setFont("Helvetica", 12)
            y_position = height - 100

    c.save()


def capture_youtube_data(video_url):
    # Get channel ID and video ID from URL
    channel_id, video_id = get_channel_and_video_id_from_url(youtube, video_url)
    
    # Get channel details
    channel_details = get_channel_details(youtube, channel_id)
    channel_info = {
        'channelId': channel_details['items'][0]['id'],
        'title': channel_details['items'][0]['snippet']['title'],
        'description': channel_details['items'][0]['snippet']['description'],
        'published At': channel_details['items'][0]['snippet']['publishedAt'],
        'subscriber Count': channel_details['items'][0]['statistics']['subscriberCount'],
        'video Count': channel_details['items'][0]['statistics']['videoCount'],
        'view Count': channel_details['items'][0]['statistics']['viewCount']
    }

    # Get video details
    video_details = get_video_details(youtube, video_id)
    video_info = {
        'videoId': video_details['items'][0]['id'],
        'title': video_details['items'][0]['snippet']['title'],
        'description': video_details['items'][0]['snippet']['description'],
        'published At': video_details['items'][0]['snippet']['publishedAt'],
        'view Count': video_details['items'][0]['statistics'].get('viewCount', 0),
        'like Count': video_details['items'][0]['statistics'].get('likeCount', 0),
        'dislike Count': video_details['items'][0]['statistics'].get('dislikeCount', 0),
        'comment Count': video_details['items'][0]['statistics'].get('commentCount', 0)
    }

    # Get comments for the video
    comments = get_video_comments(youtube, video_id)

    # Get thumbnail image for the video
    thumbnail_image = get_thumbnail_image(youtube, video_id)
    
    # Save data to DataFrame
    output_directory = '/Users/moiz/Desktop/Youtube/Hannah Likes'
    channel_df = pd.DataFrame([channel_info])
    video_df = pd.DataFrame([video_info])
    comments_df = pd.DataFrame(comments)
    
    channel_df.to_csv(f'{output_directory}channel_info.csv', index=False)
    video_df.to_csv(f'{output_directory}video_info.csv', index=False)
    comments_df.to_csv(f'{output_directory}comments.csv', index=False)
    
    # Generate PDF
    pdf_name = input("Enter output pdf name: ")
    pdf_path = f'{output_directory}/{pdf_name}youtube_data.pdf'
    generate_pdf(channel_info, video_info, comments, thumbnail_image, pdf_path)
    
    print(f"Channel information, video details, comments, and PDF report have been saved to {output_directory}")


if __name__ == "__main__":
    video_url = input("Enter the YouTube video URL: ")
    capture_youtube_data(video_url)

# This code is written by Moiz
