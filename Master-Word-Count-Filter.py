import feedparser
from bs4 import BeautifulSoup
from xml.etree.ElementTree import Element, SubElement, tostring, ElementTree, parse
import requests
import base64
import json
from datetime import datetime

# Get today's date and time
now = datetime.now()
timestamp = now.strftime('%Y-%m-%d %H:%M:%S')

# Create the commit message
commit_temp = f'Updated ###(insert feed name here)### RSS feed with newest data on {timestamp}'

def count_words(text):
    return len(text.split())


def create_rss_feed(filtered_entries, output_file):
    rss = Element('rss', version='2.0')
    channel = SubElement(rss, 'channel')

    title = SubElement(channel, 'title')
    title.text = "### Insert Source name here###"

    link = SubElement(channel, 'link')
    link.text = "https://www.theplakhovgroup.ca/projects/reading-list"  # Replace with your site URL

    description = SubElement(channel, 'description')
    description.text = "This is a custom ### Insert Source name here ### RSS feed compiled by the Plakhov Group Reading List Team."

    for entry in filtered_entries:
        item = SubElement(channel, 'item')

        title_element = SubElement(item, 'title')
        title_element.text = entry['title']

        link_element = SubElement(item, 'link')
        link_element.text = entry['link']

        description_element = SubElement(item, 'description')
        description_element.text = entry['description']

        pub_date = SubElement(item, 'pubDate')
        pub_date.text = entry['pubDate']

    tree = ElementTree(rss)
    with open(output_file, 'wb') as file:
        tree.write(file)


def filter_articles(feed_url, min_word_count, output_file):
    # Parse the RSS feed
    feed = feedparser.parse(feed_url)
    filtered_entries = []

    # Loop through each item in the feed
    for entry in feed.entries:
        # Extract the description content
        description_html = entry.description

        # Parse the HTML content using BeautifulSoup
        soup = BeautifulSoup(description_html, 'html.parser')
        description_text = soup.get_text()

        # Count words
        word_count = count_words(description_text)

        # Collect articles with word count over the threshold
        if word_count > min_word_count:
            filtered_entries.append({
                'title': entry.title,
                'link': entry.link,
                'description': description_html,
                'pubDate': entry.published
            })

    # Read existing RSS feed
    existing_entries = []
    try:
        tree = parse(output_file)
        root = tree.getroot()
        for item in root.find('channel').findall('item'):
            existing_entries.append({
                'title': item.find('title').text,
                'link': item.find('link').text,
                'description': item.find('description').text,
                'pubDate': item.find('pubDate').text
            })
    except FileNotFoundError:
        pass  # No existing file, start fresh

    # Merge new and existing entries, avoiding duplicates
    all_entries = {entry['link']: entry for entry in existing_entries + filtered_entries}.values()

    # Create and save the new RSS feed
    create_rss_feed(all_entries, output_file)


def push_to_github(file_path, repo, path_in_repo, message, branch, token):
    url = f"https://api.github.com/repos/{repo}/contents/{path_in_repo}"

    # Get the current file SHA if it exists
    try:
        response = requests.get(url, headers={"Authorization": f"token {token}"})
        response.raise_for_status()  # Raise an exception for HTTP errors
        sha = response.json().get('sha', None)
    except requests.RequestException as e:
        print(f"Error fetching file info from GitHub: {e}")
        sha = None

    try:
        with open(file_path, 'rb') as file:
            content = base64.b64encode(file.read()).decode()
    except IOError as e:
        print(f"Error reading file {file_path}: {e}")
        return

    data = {
        "message": message,
        "content": content,
        "branch": branch
    }
    if sha:
        data["sha"] = sha

    try:
        response = requests.put(url, headers={"Authorization": f"token {token}"}, data=json.dumps(data))
        response.raise_for_status()  # Raise an exception for HTTP errors
        return response.json()
    except requests.RequestException as e:
        print(f"Error updating file on GitHub: {e}")
        return


# Example usage
rss_feed_url = '### Input your RSS feed URL here ###'  # Your RSS feed URL
min_word_count = ### Word Count Here ###  # Set your desired minimum word count
output_file = 'filtered_feeder.xml'  # Path to save the new RSS feed

# GitHub details
repo = 'theplakhovgroup/reading'  # Replace with your repo name
path_in_repo = '###source name ###.xml'
commit_message = commit_temp
branch = 'main'  # Branch to commit to
github_token = '### Not for Public Consumption ###'  # Your GitHub token

filter_articles(rss_feed_url, min_word_count, output_file)
push_to_github(output_file, repo, path_in_repo, commit_message, branch, github_token)