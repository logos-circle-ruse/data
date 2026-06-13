import utils
import pandas as pd
import requests
from github import Github
from groq import Groq

LLM_PROMPT = """
You will receive text in Bulgarian.

Your task is to convert the text into clean Markdown suitable for publishing on a website.

Rules:
- Return only one paragraph.
- Do not use headings, bullet points, numbered lists, tables, blockquotes, or code blocks.
- Output must be only in Bulgarian.
- Do not add any new information.
- Do not hallucinate facts, names, links, prices, locations, or claims.
- Do not include any dates.
- Remove all dates from the output, including years, months, weekdays, exact dates, relative dates, event dates, deadlines, and date ranges.
- Do not replace removed dates with vague phrases such as „скоро“, „наскоро“, „предстои“, „тогава“ or „в този период“, unless such wording already exists in the original text.
- Do not translate the text into another language.
- Do not change the meaning of the original text, except for removing date-related information.
- Do not reword unnecessarily.
- Only restructure the text into a clear, readable paragraph.
- You may fix obvious punctuation, spacing, capitalization, and formatting issues only if they do not change the meaning.
- You may use Markdown bold only when it helps preserve emphasis already present in the original text.
- Write all verbs in the sega istorichesko vreme (present historic tense) in Bulgarian. For example, use „провежда се", „включва", „представя" instead of „се проведе", „включваше", „представи".
- Do not include explanations, notes, labels, or comments outside the final paragraph.
- Write ALL verbs in Bulgarian past tense (минало свършено време) WITHOUT EXCEPTION.
- This includes the very first sentence.
- NEVER start with „Провежда се" — always use „Проведе се".
- NEVER mix tenses within the same paragraph.
- Do not mix Latin and Cyrillic script. Write everything in Bulgarian Cyrillic only.
- Every single verb must be in past tense: „проведе се", „присъстваха", „обсъди се", „предложи се", „представи се".
- Ensure strict grammatical gender agreement in Bulgarian between verbs, nouns, and adjectives. For example: „обсъди се проектът" (masculine), „обсъди се платформата" (feminine), „обсъди се представянето" (neuter).
- Ensure strict agreement between verbs and their subjects in number (singular/plural).
- If the subject is plural, the verb must also be plural. For example: „обсъди се проектът" (singular) but „обсъдиха се проектите" (plural).
- Every single verb in the output must follow this rule without exception.

Markdown formatting:
- Preserve important details from the original text.
- Remove unnecessary repetition only if the same idea is repeated without adding new meaning.

Summary rule:
- If the text is long or unsuitable for direct publishing, summarize it into one paragraph.
- The summary must be up to 4 sentences.
- Include only the most important information from the original text.
- The summary must remain in Bulgarian.
- Do not include information that is not explicitly present in the original text.

Input text:
```
{text}
```

Return only the final Markdown.
"""

def get_website_updates() -> pd.DataFrame:
    """
    Load website updates
    """
    events = utils.get_events()
    updates = pd.DataFrame(events["updates"])
    if "description" not in updates.columns:
        updates["description"] = None

    updates["is_new"] = updates["description"].isna()
    return updates.copy()


if __name__ == "__main__":

    logger = utils.get_logger()

    github_token = os.environ.get("TOKEN")
    groq_api_key = os.environ.get("GROQ_API_KEY")
    repository_name = os.environ.get("GITHUB_REPOSITORY")
    model_name = os.environ.get("MODEL_NAME")

    groq_client = Groq(api_key=groq_api_key)
    data = get_website_updates()

    processed = []
    for row in data.loc[data["is_new"]].to_dict("records"):

        url = row.get("url")

        if not url:
            logger.warning("Skipping row without URL")
            continue

        logger.info(f"Scraping {url}")

        try:
            scraped_text = utils.scrape_event_text(url)
            logger.info(
                f"Generating description for {row.get('luma_event_id', 'unknown')}"
            )
            cleaned_description = utils.get_llm_response(
                groq_client,
                model_name,
                LLM_PROMPT.format(text=scraped_text)
            )
            row["description"] = cleaned_description
            processed.append(row)

        except Exception as e:
            logger.error(f"Failed processing {url}: {e}")

    if processed:

        processed = pd.DataFrame(processed)

        query = ~data.index.isin(processed.index)

        final = pd.concat(
            [
                data.loc[query].copy(),
                processed
            ],
            ignore_index=True
        )
        final = final.drop(columns=["is_new"])

        events_data = utils.get_events()
        events_data["updates"] = [
            {
                key: value
                for key, value in row.items()
                if not pd.isna(value)
            }
            for row in final.to_dict("records")
        ]

        json_content = json.dumps(
            events_data,
            indent=2,
            ensure_ascii=False
        )

        g = Github(github_token)
        repo = g.get_repo(repository_name)

        utils.commit_data(
            file_path="website/events.json",
            content=json_content,
            commit_message="events: Add scraped descriptions",
            logger=logger,
            repo=repo,
        )

    else:
        logger.info("No new descriptions to process")