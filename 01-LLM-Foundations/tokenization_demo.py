import tiktoken

encoder = tiktoken.get_encoding("o200k_base")

samples = [
    "Artificial intelligence is changing scientific research.",
    "الذكاء الاصطناعي يغير طريقة البحث العلمي.",

    "Cybersecurity",
    "الأمن السيبراني",

    "Artificial Intelligence and Cybersecurity",
    "الذكاء الاصطناعي والأمن السيبراني",

    "Large Language Models",
    "نماذج اللغة الكبيرة",

    "AI Agents",
    "وكلاء الذكاء الاصطناعي"
]


for text in samples:
    tokens = encoder.encode(text)

    print("\nText:", text)
    print("Number of tokens:", len(tokens))
    print("Token IDs:", tokens)

    print("Token pieces:")
    for token in tokens:
        print(token, repr(encoder.decode([token])))