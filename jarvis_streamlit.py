import streamlit as st
import json, os, time, socket
from typing import List, Dict
from openai import OpenAI

from io import StringIO
from contextlib import redirect_stdout, redirect_stderr

HERE = os.path.dirname(os.path.abspath(__file__))
MEM_FILE = os.path.join(HERE, "jarvis_mem.json")
MAX_TURNS = 20

# ---------------------------
# Stage 4 demo (safe import)
# ---------------------------
STAGE4_AVAILABLE = True
STAGE4_IMPORT_ERROR = ""

try:
    from src.stage4_agents.agent_demo import run_stage4_demo
except Exception as e:
    STAGE4_AVAILABLE = False
    STAGE4_IMPORT_ERROR = str(e)


def run_stage4_and_capture(verbose: bool = True) -> str:
    """Run Stage 4 demo and capture stdout/stderr to display in Streamlit."""
    if not STAGE4_AVAILABLE:
        return f"Stage 4 indisponível (erro no import): {STAGE4_IMPORT_ERROR}"

    buf = StringIO()
    with redirect_stdout(buf), redirect_stderr(buf):
        run_stage4_demo(verbose=verbose)

    out = buf.getvalue().strip()
    return out if out else "Stage 4 executou, mas não houve output capturado. Verifique os logs do app."


# ---------------------------
# Memory
# ---------------------------
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


# ---------------------------
# Utilities
# ---------------------------
def ip_local():
    try:
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


# ---------------------------
# LLM
# ---------------------------
def llm_reply(prompt, conversation):
    client = OpenAI()
    system_msg = {
        "role": "system",
        "content": (
            "Você é o Jarvis, assistente brasileiro educado e útil. "
            "Explique passo a passo só quando for pedido."
        ),
    }

    # Append user once (do NOT append elsewhere)
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


# ---------------------------
# UI
# ---------------------------
st.set_page_config(page_title="Jarvis Web", page_icon="🤖")
st.title("🤖 Jarvis — Versão Web")
st.caption("Assistente IA com memória persistente, comandos especiais e suporte a cena 3D.")

if "conversation" not in st.session_state:
    st.session_state.conversation = load_memory()

conversation = st.session_state.conversation

with st.expander("📚 Memória"):
    st.write(conversation[-10:])

with st.expander("🧪 Stage 4 — Agent Demo"):
    if not STAGE4_AVAILABLE:
        st.error(f"Não consegui importar Stage 4: {STAGE4_IMPORT_ERROR}")
        st.info("Dica: crie src/__init__.py e src/stage4_agents/__init__.py (arquivos vazios) e reinicie o app.")
    else:
        stage4_verbose = st.checkbox("Verbose (mostrar output do demo)", value=True)
        if st.button("Run Stage 4 Demo"):
            output = run_stage4_and_capture(verbose=stage4_verbose)
            st.code(output)

user_input = st.chat_input("Digite sua mensagem...")


def process_command(cmd):
    c = cmd.lower().strip()

    if c in {"parar", "sair", "exit", "quit"}:
        return "Encerrando (simulado na versão web)."

    if c in {"/reset", "reset"}:
        conversation.clear()
        save_memory(conversation)
        return "Memória limpa."

    if c in {"/mem", "memoria", "memória"}:
        return f"Itens na memória: {len(conversation)}"

    if c in {"/stage4", "stage4", "rodar stage4"}:
        return run_stage4_and_capture(verbose=True)

    if "hora" in c:
        return time.strftime("Agora são %H:%M.")

    if "ip" in c:
        return f"Seu IP local é {ip_local()}"

    if "spawn cubo" in c or "criar cubo" in c:
        return spawn_cubo()

    return None


# Render chat history
for msg in conversation:
    if msg.get("role") == "user":
        st.chat_message("user").write(msg.get("content", ""))
    else:
        st.chat_message("assistant").write(msg.get("content", ""))

# Input handling
if user_input:
    st.chat_message("user").write(user_input)

    cmd_result = process_command(user_input)
    if cmd_result:
        st.chat_message("assistant").write(cmd_result)
        conversation.append({"role": "user", "content": user_input})
        conversation.append({"role": "assistant", "content": cmd_result})
        save_memory(conversation)
    else:
        reply = llm_reply(user_input, conversation)
        st.chat_message("assistant").write(reply)
        save_memory(conversation)
