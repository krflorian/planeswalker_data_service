


from transformers import pipeline

config = {"nli_classifier": "../data/models/bart-large-mnli"}

nli_classifier_model = pipeline(
    "zero-shot-classification",
    model=config.get("nli_classifier", "facebook/bart-large-mnli"),
)


 texts = [
        "I want a fireball deck with standard cards",
        "can you help me with my Ojer Taq commander deck?",
        "Hi!",
        "tell me a fact about magic",
        "Explain Arahbo's eminence ability",
        "How do replacement effects work with damage modifiers like Torbran, Thane of Red Fell and City on Fire",
    ]

    for text in texts:
        score, intent = classify_intent(text, nli_classifier_model)
        print(intent, score, text)