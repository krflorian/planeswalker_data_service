# %%
from pathlib import Path
import re
import random
import wikipedia
from sentence_transformers import SentenceTransformer

from src.vector_db import VectorDB
from src.objects import Rule


def load_rules(rules_file: Path = Path("data/rules/MagicCompRules.txt")) -> str:
    with open(rules_file, "r", encoding="utf-8") as f:
        text = f.read()
    return text


def extract_rules(text: str) -> list[str]:
    # split the text by the word 'Credits' and take the second part starting with the rules
    text = text.split("Credits", 1)[1]
    # split the text by the word 'Glossary' and take the first part as rules
    rules = text.split("Glossary", 1)[0]
    # split the text by the word 'Glossary' and take the second part as text
    text = text.split("Glossary", 1)[1]
    # split the text by the word 'Credits' and take the first part as glossary_entries
    glossary_entries = text.split("Credits", 1)[0]

    # chunk rules
    processed_rules = []

    rule_pattern = r"(\n\d{3}\.\d+.)"
    chapter_pattern = r"(\n\d{3}\. .*)"
    chapters = re.split(chapter_pattern, rules)
    for text in chapters[1:]:
        # chapter
        if re.match(chapter_pattern, text):
            chapter = text
            chapter = chapter.replace("\n", "")
        else:
            # rules
            rules = re.split(rule_pattern, text)
            rules = [r for r in rules if r not in ["\n", ""]]
            subchapter = None
            for rule in rules:
                # rule id
                if re.match(rule_pattern, rule):
                    rule_id = rule
                    rule_id = rule_id.replace("\n", "")
                # rule text
                else:
                    if len(rule.split()) // 2 > 1:  # minimum 2 tokens
                        if "Example:" in rule:
                            rule = rule.split("Example:")
                            examples = rule[1:]
                            rule = rule[0]
                        else:
                            examples = []
                        processed_rules.append(
                            Rule(
                                text=rule.strip(),
                                rule_id=rule_id,
                                chapter=chapter,
                                subchapter=subchapter,
                                examples=examples,
                            )
                        )
                    else:
                        subchapter = rule_id + " " + rule

    # chunk glossary
    glossary_entries = glossary_entries.split("\n\n")
    glossary_entries = [x for x in glossary_entries if (x not in ["", "\n"])]
    for entry in glossary_entries:
        entry_id = entry.split("\n")[0]
        processed_rules.append(Rule(text=entry, rule_id=entry_id, chapter="Glossary"))

    rule = random.choice(processed_rules)
    print("random rule:")
    print(rule.chapter)
    print(rule.rule_id)
    print(rule.text)

    return processed_rules


def parse_keywords_from_wikipedia():
    # Specify the title of the Wikipedia page
    wiki = wikipedia.page("List of Magic: The Gathering keywords")

    # Extract the plain text content of the page, excluding images, tables, and other data.
    text = wiki.content
    wiki_pattern = r"(=== [^=]+ ===)"
    processed_text = re.split(wiki_pattern, text)

    # add rules
    rules = []
    for text in processed_text[1:]:
        if text.startswith("==="):
            keyword = text.replace("===", "")
            keyword = keyword.strip()
        else:
            rule = Rule(text=text, rule_id=keyword, chapter="Keywords")
            rules.append(rule)

    rule = random.choice(rules)
    print("random wikipedia keyword:")
    print(rule.chapter)
    print(rule.rule_id)
    print(rule.text)
    return rules


if __name__ == "__main__":
    # create variables
    db_name = "rules_db_gte"
    rules_text_file = Path("data/rules/MagicCompRules.txt")
    rules_db_file = Path(f"data/artifacts/{db_name}.p")

    # load model
    model = SentenceTransformer(
        "thenlper/gte-large"
    )  # sentence-transformers/all-MiniLM-L6-v2

    # load rules
    text = load_rules(rules_text_file)
    rules = extract_rules(text)
    rules.extend(parse_keywords_from_wikipedia())

    # create rule texts
    texts = []
    for rule in rules:
        text = ""
        if rule.subchapter is not None:
            text += rule.subchapter + " - "
        if rule.chapter in ["Keywords", "Glossary"]:
            text += rule.rule_id + " - "
        text += rule.text
        texts.append(text)

    rules_db = VectorDB(
        texts=texts,
        data=rules,
        model=model,
    )

    # add vectors for examples
    for rule in rules:
        if not rule.examples:
            continue

        embeddings_and_data = rules_db.get_embeddings(
            texts=rule.examples,
            data=[rule for _ in range(len(rule.examples))],
            model=model,
        )

        rules_db.add(embeddings_and_data)

    # save rules db
    rules_db.dump(rules_db_file)
