# %%
from pathlib import Path
import re
import random
import os
from src.objects import Rule, RuleType

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
    pattern = r"(\n\d{3}\.\d+.)"
    rules = re.split(pattern, rules)
    rules = ["".join(x) for x in zip(rules[1::2], rules[0::2])]
    for rule in rules:
        rule_id = re.match(pattern, rule)
        rule_id = rule_id.group(0).replace("\n", "")
        processed_rules.append(
            Rule(text=rule, rule_id=rule_id, rule_type=RuleType.RULE)
        )

    # chunk glossary
    glossary_entries = glossary_entries.split("\n\n")
    glossary_entries = [x for x in glossary_entries if (x != "" and x != "\n")]
    for entry in glossary_entries:
        entry_id = entry.split("\n")[0]
        processed_rules.append(
            Rule(text=entry, rule_id=entry_id, rule_type=RuleType.GLOSSARY)
        )

    rule = random.choice(processed_rules)
    print("random rule:")
    print(rule.rule_id)
    print(rule.rule_type)
    print(rule.text)

    return processed_rules


# %%

text = load_rules()
rules = extract_rules(text)


# %%

import matplotlib.pyplot as plt

plt.hist([len(rule) for rule in rules])
plt.title("rule length")
plt.show()

# %%
import random

filtered_rules = [rule for rule in rules if len(rule) > 1000]

print(len(filtered_rules))
i = 10
for _ in range(min(i, len(filtered_rules))):
    print("_______________")
    rule = random.choice(filtered_rules)
    print("character length: ", len(rule))
    print("~token length: ", len(rule.text.split()) // 2)
    print(rule.text)

# %%
from sentence_transformers import SentenceTransformer

model = SentenceTransformer(
    "thenlper/gte-large"
)  # sentence-transformers/all-MiniLM-L6-v2
model

# %%
from src.vector_db import VectorDB

rules_db = VectorDB(
    texts=[rule.text for rule in rules],
    data=rules,
    model=model,
)

# %%

from pathlib import Path

db_name = "rules_db_gte"
rules_db_file = Path(f"data/{db_name}.p")
card_db.dump(rules_db_file)
