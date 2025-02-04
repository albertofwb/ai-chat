import openai

# for backward compatibility, you can still use `https://api.deepseek.com/v1` as `base_url`.
client = openai.OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="nokeyneeded")
model_name = "deepseek-r1:14b"
response = client.chat.completions.create(
    model=model_name,
    messages=[
        {"role": "system", "content": "You are a helpful assistant"},
        {"role": "user", "content": "Hello"},
  ],
    max_tokens=1024,
    temperature=1.3,
    stream=False
)