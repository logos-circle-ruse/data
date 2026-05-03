import utils
import os, json, datetime
import pandas as pd
from groq import Groq
from github import Github

LLM_PROMPT = """
You will receive text in Bulgarian.

Your task is to convert the text into clean Markdown suitable for publishing on a website.

Rules:
- Output must be only in Bulgarian.
- Do not add any new information.
- Do not hallucinate facts, names, dates, links, prices, locations, or claims.
- Do not translate the text into another language.
- Do not reword the meaning of the original text.
- Only restructure and format the provided text using Markdown.
- Keep the original meaning, tone, terminology, and factual content.
- You may fix obvious punctuation, spacing, capitalization, and formatting issues only if they do not change the meaning.
- Do not include explanations, comments, or notes outside the final Markdown.

Markdown formatting:
- Use headings, subheadings, bullet points, numbered lists, bold text, and links only when appropriate.
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

def get_circle_data(country: str, city: str) -> pd.DataFrame:
    """
    Get all Luma event IDs and descriptions for the given `country` and `city`
    """
    data = utils.get_circle_data()
    query = (data["location_city"].str.lower() == city.lower()) & (data["location_country"].str.lower() == country.lower())
    
    column_mapping = {
        "event_id": "luma_event_id",
        "event_description": "description"
    }
    data = data.loc[query, list(column_mapping.keys())]\
                .reset_index(drop=True)\
                .rename(columns=column_mapping)
    
    data["description"] = data["description"].apply(
        lambda description: description[:description.index("За Logos")]
    )
    return data.copy()


def get_events() -> dict:
    """
    Get current website events
    """
    file_path = os.path.join(os.path.dirname(__file__), "website", "events.json")
    
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return data


def get_llm_response(client: Groq, model_name: str, prompt: str) -> str:
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
        reasoning_effort="medium",
    )
    return completion.choices[0].message.content


def get_website_updates() -> pd.DataFrame:
    """
    Process the data
    """
    circle_data = get_circle_data("Bulgaria", "Ruse")
    luma_events = get_events()

    website_updates = pd.DataFrame(luma_events["updates"]).iloc[1:].reset_index(drop=True)
    backfill = "description" not in website_updates.columns

    if backfill:
        website_updates = website_updates.merge(circle_data, "left", "luma_event_id").assign(is_blank = True)
    else:
        event_mapping = circle_data.set_index("luma_event_id").to_dict()["description"]
        website_updates = website_updates.assign(
            is_blank = pd.isna(website_updates["description"])
        )
        website_updates["description"] = website_updates.apply(
            lambda row: event_mapping.get(row["luma_event_id"]) if row["is_blank"] else row["description"], axis=1
        )

    website_updates = website_updates.rename(columns={"is_blank": "is_new"})
    return website_updates.copy()

if __name__ == "__main__":

    logger = utils.get_logger()
    github_token = os.environ.get("TOKEN")
    groq_api_key = os.environ.get("GROQ_API_KEY")
    repository_name = os.environ.get("GITHUB_REPOSITORY")
    model_name = os.environ.get("MODEL_NAME")

    groq_client = Groq(api_key=groq_api_key)
    data = get_website_updates()
    
    processed = []
    for row in data.to_dict("records"):
    
        if pd.isna(row["description"]):
            continue
        
        logger.info(f"Processing {row['luma_event_id']} [{row['date']}]")
        row["description"] = get_llm_response(groq_client, model_name, LLM_PROMPT.format(text=row["description"]))
        processed.append(row)

    if processed:
        processed = pd.DataFrame(processed)
        events_data = get_events()

        query = ~data["luma_event_id"].isin(processed["luma_event_id"])
        final = pd.concat([
            data.loc[query].copy(), 
            processed, 
            pd.DataFrame([events_data["updates"][0]])
        ], ignore_index=True)

        final["date"] = pd.to_datetime(final["date"])
        final = final.sort_values("date", ascending=False)\
                    .drop(["is_new"], axis=1)\
                    .reset_index(drop=True)\
                    .assign(date = final["date"].astype(str))
        
        events_data["updates"] = [
            {
                key: value
                for key, value in event_update.items()
                if not pd.isna(value)
            }
            for event_update in final.to_dict("records")
        ]
        json_content = json.dumps(events_data, indent=2)

        g = Github(github_token)
        repo = g.get_repo(repository_name)

        utils.commit_data(
            file_path="website/events.json",
            content=json_content,
            commit_message=f"events: Add formatted descriptions for missing descriptions",
            logger=logger,
            repo=repo,
        )