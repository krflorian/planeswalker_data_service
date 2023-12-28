# %%
from pathlib import Path
import re
import random
import os
from src.objects import Rule

# os.chdir(r"/home/max/projects/planeswalker_companion")


def load_rules(rules_file=Path("data/MagicCompRules.txt")):
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
                            print(examples[0])
                        else:
                            examples = []
                        processed_rules.append(
                            Rule(
                                text=rule,
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
    print(rule.rule_id)
    print(rule.chapter)
    print(rule.text)

    return processed_rules


# %%

text = load_rules()
rules = extract_rules(text)


# %%
"""
for rule in rules:
    if rule.examples:
    # if rule.chapter.startswith("Glossary"):
    # if rule.subchapter is not None:
        print(rule.chapter)
        print(rule.subchapter)
        print(rule.text)
        print("examples:")
        for example in rule.examples:
            print(example)
        print("____________")


filtered_rules = [rule for rule in rules if len(rule) > 1000]
print(len(filtered_rules))
i = 10
for _ in range(min(i, len(filtered_rules))):
    print("_______________")
    rule = random.choice(filtered_rules)
    print(rule.chapter)
    print("character length: ", len(rule))
    print("~token length: ", len(rule.text.split()) // 2)
    print(rule.text)
"""


# %%
# check rules
import random
import matplotlib.pyplot as plt

plt.hist([len(rule) for rule in rules])
plt.title("rule length")
plt.show()


# %%
# load model
from sentence_transformers import SentenceTransformer

model = SentenceTransformer(
    "thenlper/gte-large"
)  # sentence-transformers/all-MiniLM-L6-v2
model

# %%
# create vector db
from src.vector_db import VectorDB

# add rules
texts = []
for rule in rules:
    text = ""
    if rule.subchapter is not None:
        text += rule.subchapter + " - "
    text += rule.text
    texts.append(text)

assert len(texts) == len(rules)
rules_db = VectorDB(
    texts=texts,
    data=rules,
    model=model,
)

# add example vectors
for rule in rules:
    if rule.examples:
        embeddings_and_data = rules_db.get_embeddings(
            texts=rule.examples,
            data=[rule for _ in range(len(rule.examples))],
            model=model,
        )

        rules_db.add(embeddings_and_data)


# %%
# tests
TEST_CASES_KEYWORDS = [
    "what happens if i attack with a 1/1 deathouch creature and my opponent blocks with a 2/2 token?",
    "what happens if i attack with a 1/1 first strike creature and my opponent blocks with a 3/1 creature?",
    "what happens if i attack with a 5/5 creature with trample and my opponent blocks with a 1/1 creature?",
    "what happens if i attack with a 5/5 creature with trample and my opponent blocks with a 5/1 creature?",
    "what happens if i attack with a 5/5 creature with trample and my opponent blocks with a 1/1 creature with deathtouch?",
]


for question in TEST_CASES_KEYWORDS:
    results = rules_db.query(
        question, model=model, k=10, threshold=0.2, lasso_threshold=0.02
    )
    print("______________")
    print("______________")
    print("question:", question)
    print()
    print("received chunks: ", len(results))
    print("______________")

    for rule, distance in results:
        print(rule.chapter, "-", rule.subchapter)
        print(rule.rule_id, ": distance = ", distance)
        print(rule.text)
        print("____________")


# %%
# save db
from pathlib import Path

db_name = "rules_db_gte"
rules_db_file = Path(f"data/{db_name}.p")
rules_db.dump(rules_db_file)
