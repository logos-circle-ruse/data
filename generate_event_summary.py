import os
import pandas as pd
import utils
from groq import Groq
from github import Github
 
LLM_PROMPT = """
You will receive a structured meeting recap/report in English about a "Logos Circle Ruse" event.
 
Your task is to generate a Bulgarian-language promotional announcement (in Markdown) for the NEXT meeting, based on the input report.
 
Rules:
- Output must be only in Bulgarian (Cyrillic script only, no Latin letters), except for URLs which may remain in Latin.
- Start with: "Добре дошли на Кръг Logos Русе."
- Follow with: "На миналата среща обсъдихме:"
- For each of the 2-4 most important topics from the "Topics" and "Discussed issues" sections of the input:
  - Add a short Markdown heading (## ) with the topic name in Bulgarian (e.g. "Платформа за анонимни сигнали", "Уебсайт на Logos Circle Русе").
  - Follow it with 1-2 short sentences in Bulgarian, in past tense (минало свършено време), summarizing what was discussed or done, written for a general non-technical audience.
  - If the topic has one clearly relevant link from the input (e.g. a website or forum link), include it on its own line directly after the description, as a bare URL.
- Add the line: "Вашето мнение е важно за нас!"
- Do not invent topics, facts, or links not present in the input.
- Do not include usernames, statistics (attendance numbers, registrations), or steward names.
- Do not include explanations, notes, or comments outside the final Markdown.
 
Input text:
```
{text}
```
 
Return only the final Markdown.
"""
 
LOGOS_SECTION = """## За Logos
 
Logos е напълно децентрализирана, спазваща поверителност и политически неутрална технологична платформа. Стека включва три модулни децентрализирани протокола: Блокчейн, Съобщения, и Съхранение. В комбинация, те осигуряват техническата основа за кибер държави, паралелни общества, мрежови държави или всякакви публични институции без граници, основани на доброволно съгласие.
 
Logos е и колекция от учебни общности, които ще управляват и поддържат мрежата в духа на оригиналните [cypherpunks](https://en.wikipedia.org/wiki/Cypherpunk?utm_source=luma). Заедно, те формират гражданското движение необходимо за изграждането на социалните, икономическите и управленските институции които ще съществуват в технологичния стек.
 
В крайна сметка, тези институции ще се включат в конкурентен пазар, който може да запълни празнините в управлението в реалния свят, предоставяйки публични услуги с минимално участие на външни посредници и устойчиви на корупция, навсякъде където има достъп до интернет.
 
Прочетете нашия [манифест](https://logos.co/manifesto?utm_source=luma), за да се запознаете по-подробно с нашите идеали и технология."""
 
def get_latest_event(events_data: dict) -> dict:
    """
    Events are stored in descending order, so the first entry is the latest.
    """
    updates = events_data.get("updates", [])
    if not updates:
        raise ValueError("No updates found in events.json")
    return updates[0]
 
 
def build_markdown(event: dict) -> str:
    """
    Combine the LLM-generated description with the 'За Logos' section.
    """
    description = event.get("description", "").strip()
    return f"{description}\n\n{LOGOS_SECTION}\n"
 
 
def output_file_path(event: dict) -> str:
    """
    Build the output markdown file's repo-relative path using a %b %Y date format,
    e.g. "website/posts/May 2026.md"
    """
    date_str = event.get("date")
    next_month = pd.Timestamp(date_str) + pd.offsets.MonthBegin()
    filename = next_month.strftime("%b %Y") + ".md"
    return f"website/posts/{filename}"
 
 
if __name__ == "__main__":
 
    logger = utils.get_logger()
 
    groq_api_key = os.environ.get("GROQ_API_KEY")
    model_name = os.environ.get("MODEL_NAME")
    groq_client = Groq(api_key=groq_api_key)
 
    github_token = os.environ.get("TOKEN")
    repo_name = os.environ.get("GITHUB_REPOSITORY")
    branch_name = os.environ.get("BRANCH_NAME", "main")
    gh = Github(github_token)
    repo = gh.get_repo(repo_name)
 
    events_data = utils.get_events()
    latest_event = get_latest_event(events_data)
 
    out_path = output_file_path(latest_event)
 
    try:
        repo.get_contents(out_path, ref=branch_name)
        logger.info(f"Post already exists for this event: {out_path}; skipping.")
    except Exception:
        url = latest_event.get("url")
 
        if not url:
            logger.error("Latest event has no URL, cannot scrape")
        else:
            logger.info(f"Scraping {url}")
 
            try:
                scraped_text = utils.scrape_event_text(url)
 
                logger.info(f"Generating description for {latest_event.get('luma_event_id', 'unknown')}")
                cleaned_description = utils.get_llm_response(groq_client, model_name, LLM_PROMPT.format(text=scraped_text))

                latest_event["description"] = cleaned_description
                markdown_content = build_markdown(latest_event)

                # New event confirmed (generation succeeded) - clear out the old post(s)
                utils.delete_old_posts(directory="website/posts", keep_path=out_path, repo=repo, logger=logger, branch_name=branch_name)
                utils.commit_data(out_path, markdown_content, f"luma-info: {os.path.basename(out_path).replace('.md', '')} Summary", repo, logger, branch_name)
 
            except Exception as e:
                logger.error(f"Failed processing {url}: {e}")
