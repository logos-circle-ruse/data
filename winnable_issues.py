from github import Github, Issue, Repository, Milestone
import re, os, json, datetime
import utils

def get_winnable_issues(repo: Repository.Repository) -> list[Issue.Issue]:
    """
    Get the Winnable Issues
    https://circles.logos.co/readme/for-circle-stewards/section-1-organising-circles-around-local-action/what-is-a-winnable-issue
    """
    prefix = "[Winnable Issue]"
    issues = repo.get_issues(state="open", type="Feature")
    winnable_issues: list[Issue.Issue] = [
        issue 
        for issue in issues 
        if issue.title.startswith(prefix)
    ]
    return winnable_issues

def get_milestones(repo: Repository.Repository) -> dict[Issue.Issue, Milestone.Milestone]:
    """
    Get the current milestones of every winnable issue
    """
    winnable_issues = get_winnable_issues(repo)
    return {
        issue: repo.get_milestone(issue.milestone.number)
        for issue in winnable_issues
    }

def create_data(repo: Repository.Repository, info: dict[Issue.Issue, Milestone.Milestone]) -> list[dict]:
    """
    Create website data
    """
    data = []
    for winnable_issue, milestone in info.items():
        issues = repo.get_issues(milestone=milestone)
        issues = list(issues)
        
        members = []
        tags = {}
        for issue in issues:
            members += issue.assignees
            if issue == winnable_issue:
                continue
            issue_tag = re.search(r'\[(.*)\]', issue.title).group(1)
            if issue_tag not in tags:
                tags[issue_tag] = 0
            
            tags[issue_tag] += 1
        
        total_issues = milestone.open_issues + milestone.closed_issues
        point = {
            "name": "]".join(winnable_issue.title.split("]")[1:]).strip(),
            "description": winnable_issue.body,
            "members": len(set(members)),
            "github_issues": total_issues,
            "completed_pct": (milestone.closed_issues / total_issues) * 100,
            "chart_colours": []
        }
        total_count = sum(list(tags.values()))
        gradient_start = 0
        
        for idx, (tag, count) in enumerate(tags.items()):
            gradient_end = int((count / total_count) * 100)
            point["chart_colours"].append({
                "start": gradient_start,
                "end": gradient_end + gradient_start,
                "colour": COLOURS[idx]
            })
            gradient_start += gradient_end

        data.append(point)

    return data

if __name__ == "__main__":

    github_token = os.environ.get("TOKEN")
    pm_repo_name = os.environ.get("PROJECT_MANAGEMENT_REPOSITORY_NAME")
    data_repo_name = os.environ.get("GITHUB_REPOSITORY")

    # Used in plots
    COLOURS = [
        "#4CAF50",  # green (your start)
        "#66BB6A",  # lighter green
        "#2196F3",  # blue
        "#42A5F5",  # lighter blue
        "#FFC107",  # amber
        "#FFD54F",  # lighter amber
        "#FF7043",  # orange / red (adds contrast)
        "#EF5350",  # red
        "#9C27B0",  # purple
        "#7E57C2"   # lighter purple
    ]
    g = Github(github_token)
    repo = g.get_repo(pm_repo_name)
    info = get_milestones(repo)
    data = create_data(repo, info)

    repo = g.get_repo(data_repo_name)
    json_content = json.dumps(data, indent=2)
    utils.commit_data(
        file_path="website/projects.json",
        content=json_content,
        commit_message=f"projects: Winnable Issue update as of {datetime.datetime.now().date()}",
        logger=utils.get_logger(),
        repo=repo
    )