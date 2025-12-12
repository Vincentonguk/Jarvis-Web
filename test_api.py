from openai import OpenAI
import os
c = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
r = c.chat.completions.create(
  model="gpt-4o-mini",
  messages=[{"role":"user","content":"Diga apenas: Jarvis OK em 5 palavras."}],
  max_tokens=20
)
print(r.choices[0].message.content)
