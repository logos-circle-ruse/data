import pandas as pd
import logging, base64, requests
from github import Repository
from typing import Optional
from groq import Groq
from html_to_markdown import convert
import os
import json
from bs4 import BeautifulSoup

def get_logger() -> logging.Logger:
    """
    Create the Logger
    """
    instance = logging.getLogger("ruse-circle")
    instance.setLevel(logging.INFO)
    instance.propagate = False

    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        f"[%(asctime)s] [%(levelname)s]\t%(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    handler.setFormatter(formatter)
    instance.addHandler(handler)
    return instance


def create_file(file_path: str, content: str, commit_message: str, repo: Repository.Repository, logger: logging.Logger, branch_name: str = "main"):
    """
    Create a new file in the repository
    """
    repo.create_file(
        path=file_path,
        message=commit_message,
        content=content,
        branch=branch_name,
    )
    logger.info(f"Uploaded {file_path} on branch {branch_name}")

def delete_file(file_path: str, existing_file, commit_message: str, repo: Repository.Repository, logger: logging.Logger, branch_name: str = "main"):
    """
    Delete an existing file from the repository
    """
    repo.delete_file(
        path=file_path,
        message=commit_message,
        sha=existing_file.sha,
        branch=branch_name,
    )
    logger.info(f"Deleted {file_path} on branch {branch_name}")

def delete_old_posts(directory: str, keep_path: str, repo: Repository.Repository, logger: logging.Logger, branch_name: str = "main") -> None:
    """
    Remove any existing .md files in the repo's posts directory other than keep_path.
    Used to clear out the previous announcement once a new event is detected.
    """
    try:
        contents = repo.get_contents(directory, ref=branch_name)
    except Exception:
        return
    for item in contents:
        if not item.name.endswith(".md"):
            continue
        if item.path == keep_path:
            continue
        logger.info(f"Deleting old post: {item.path}")
        repo.delete_file(
            path=item.path,
            message=f"luma-info: Delete {item.name}",
            sha=item.sha,
            branch=branch_name,
        )


def commit_data(file_path: str, content: str, commit_message: str, repo: Repository.Repository, logger: logging.Logger, branch_name: str = "main"):
    """
    Commit the data to the repository
    """
    try:
        existing_file = repo.get_contents(file_path, ref=branch_name)
        existing_content = base64.b64decode(existing_file.content).decode("utf-8")

        if existing_content == content:
            logger.info(f"Skipped {file_path} update on branch {branch_name}. No content change.")
            return
        
        repo.update_file(
            path=file_path,
            message=commit_message,
            content=content,
            sha=existing_file.sha,
            branch=branch_name,
        )

        logger.info(f"Updated {file_path} on branch {branch_name}")

    except Exception:
        repo.create_file(
            path=file_path,
            message=commit_message,
            content=content,
            branch=branch_name,
        )
        logger.info(f"Uploaded {file_path} on branch {branch_name}")



def get_circle_data(logger: Optional[logging.Logger] = None) -> pd.DataFrame:
    """
    Extract global circle data
    """
    url = "https://hasura.bi.status.im/api/rest/circle/events"
    if logger:
        logger.info(f"Fetching Luma Events data from {url}")

    data = requests.get(url).json().get("stg_external_circle_circle_event", [])
    data = pd.DataFrame(data)
    if logger:
        logger.info(f"GET: {len(data)} rows")

    return data.copy()

def get_events() -> dict:
    """
    Get current website events
    """
    file_path = os.path.join(os.path.dirname(__file__), "website", "events.json")

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return data

def scrape_event_text(url: str) -> str:
    """
    Scrape event page content and convert it to Markdown
    """
    response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    post = soup.find(id="post_1")
    return convert(str(post)).content

def get_llm_response(client: Groq,model_name: str,prompt: str) -> str:
    """
    Get the LLM's response
    """
    completion = client.chat.completions.create(
        model=model_name,
        messages=[
            {
                "role": "user",
                "content": prompt
            },
        ],
        temperature=0,
        max_completion_tokens=4096,
        top_p=1,
    )
    output = completion.choices[0].message.content
    output = output.replace("—", "-")
    return output