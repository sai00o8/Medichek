from groq import Groq

client = Groq(api_key="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")

models = client.models.list()

for model in models.data:
    print(model.id)