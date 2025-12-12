import streamlit as st
import json, os, time, socket
from typing import List, Dict
from openai import OpenAI

HERE = os.path.dirname(os.path.abspath(__file__))
MEM_FILE = os.path.join(HERE, "jarvis_mem.json")
MAX_TURNS = 20

def load_memory():
    if os.path.exists(MEM_FILE):
        try:
            with open(MEM_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                return data[-2 * MAX_TURNS :]
        except:
            pass
    return []

def save_memory(conv):
    try:
        with open(MEM_FILE, "w", encoding="utf-8") as f:
            json.dump(conv[-2 * MAX_TURNS:], f, ensure_ascii=False, indent=2)
    except:
        pass

def ip_local():
    try:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "desconhecido"

def spawn_cubo(url="http://127.0.0.1:8000"):
    try:
        import httpx
        httpx.post(
            f"{url}/spawn",
            json={"id": "cube1", "type": "cube", "pos": [0, 1.2, 0.5], "color": "#00ffff"},
            timeout=3,
        )
        return "Cubo criado."
    except:
        return "Não consegui falar com o servidor de cena."

def llm_reply(prompt, conversation):
    client = OpenAI()
    system_msg = {
        "role": "system",
        "content": (
            "Você é o Jarvis, assistente brasileiro educado e útil. "
            "Explique passo a passo só quando for pedido."
        ),
    }
    conversation.append({"role": "user", "content": prompt})
    msgs = [system_msg] + conversation[-2 * MAX_TURNS :]
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=msgs,
            temperature=0.6,
            max_tokens=300,
        )
        reply = resp.choices[0].message.content.strip()
        conversation.append({"role": "assistant", "content": reply})
        save_memory(conversation)
        return reply
    except Exception as e:
        return f"OpenAI erro: {e}"

st.set_page_config(page_title="Jarvis Web", page_icon="🤖")
st.title("🤖 Jarvis — Versão Web")
st.caption("Assistente IA com memória persistente, comandos especiais e suporte a cena 3D.")

if "conversation" not in st.session_state:
    st.session_state.conversation = load_memory()

conversation = st.session_state.conversation

with st.expander("📚 Memória"):
    st.write(conversation[-10:])

user_input = st.chat_input("Digite sua mensagem...")

def process_command(cmd):
    c = cmd.lower()
    if c in {"parar", "sair", "exit", "quit"}:
        return "Encerrando (simulado na versão web)."
    if c in {"/reset", "reset"}:
        conversation.clear()
        save_memory(conversation)
        return "Memória limpa."
    if c in {"/mem", "memoria", "memória"}:
        return f"Itens na memória: {len(conversation)}"
    if "hora" in c:
        return time.strftime("Agora são %H:%M.")
    if "ip" in c:
        return f"Seu IP local é {ip_local()}"
    if "spawn cubo" in c or "criar cubo" in c:
        return spawn_cubo()
    return None

for msg in conversation:
    if msg["role"] == "user":
        st.chat_message("user").write(msg["content"])
    else:
        st.chat_message("assistant").write(msg["content"])

if user_input:
    st.chat_message("user").write(user_input)
    conversation.append({"role": "user", "content": user_input})

    cmd_result = process_command(user_input)
    if cmd_result:
        st.chat_message("assistant").write(cmd_result)
        conversation.append({"role": "assistant", "content": cmd_result})
        save_memory(conversation)
    else:
        reply = llm_reply(user_input, conversation)
        st.chat_message("assistant").write(reply)
        save_memory(conversation)
