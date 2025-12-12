from openai import OpenAI
import os
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
msg = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role":"user","content":"Responda em PT-BR: diga 'Jarvis OK' em 5 palavras."}],
    max_tokens=20
)
print(msg.choices[0].message.content)
