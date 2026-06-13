import os
import json
from datetime import datetime

import utils


ZA_LOGOS_SECTION = """## За Logos

Logos е напълно децентрализирана, спазваща поверителност и политически неутрална технологична платформа. Стека включва три модулни децентрализирани протокола: Блокчейн, Съобщения, и Съхранение. В комбинация, те осигуряват техническата основа за кибер държави, паралелни общества, мрежови държави или всякакви публични институции без граници, основани на доброволно съгласие.

Logos е и колекция от учебни общности, които ще управляват и поддържат мрежата в духа на оригиналните [cypherpunks](https://en.wikipedia.org/wiki/Cypherpunk?utm_source=luma). Заедно, те формират гражданското движение необходимо за изграждането на социалните, икономическите и управленските институции които ще съществуват в технологичния стек.

В крайна сметка, тези институции ще се включат в конкурентен пазар, който може да запълни празнините в управлението в реалния свят, предоставяйки публични услуги с минимално участие на външни посредници и устойчиви на корупция, навсякъде където има достъп до интернет.

Прочетете нашия [манифест](https://logos.co/manifesto?utm_source=luma), за да се запознаете по-подробно с нашите идеали и технология."""


def get_events() -> dict:
    """
    Load current website events
    """
    file_path = os.path.join(
        os.path.dirname(__file__),
        "website",
        "events.json"
    )

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return data


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
    return f"{description}\n\n{ZA_LOGOS_SECTION}\n"


def output_file_path(event: dict) -> str:
    """
    Build the output markdown file path using a %b %Y date format,
    e.g. "May 2026.md"
    """
    date_str = event.get("date")
    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    filename = date_obj.strftime("%b %Y") + ".md"

    output_dir = os.path.join(
        os.path.dirname(__file__),
        "website",
        "posts"
    )
    os.makedirs(output_dir, exist_ok=True)

    return os.path.join(output_dir, filename)


if __name__ == "__main__":

    logger = utils.get_logger()

    events_data = get_events()
    latest_event = get_latest_event(events_data)

    out_path = output_file_path(latest_event)

    if os.path.exists(out_path):
        logger.info(f"{out_path} already exists, skipping")
    else:
        logger.info(
            f"Generating summary for {latest_event.get('luma_event_id', 'unknown')}"
        )

        markdown_content = build_markdown(latest_event)

        with open(out_path, "w", encoding="utf-8") as f:
            f.write(markdown_content)

        logger.info(f"Wrote {out_path}")
