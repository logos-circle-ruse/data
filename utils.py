import logging, base64
from github import Repository

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