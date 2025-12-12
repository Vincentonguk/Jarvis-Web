# -*- coding: utf-8 -*-
import os, sys, time, socket, argparse, json
from typing import Optional, List, Dict

# ====== Config de memória persistente ======
HERE = os.path.dirname(os.path.abspath(__file__))
MEM_FILE = os.path.join(HERE, "jarvis_mem.json")
MAX_TURNS = 20  # limita a memória (últimas N mensagens user+assistant)

def load_memory() -> List[Dict[str, str]]:
    try:
        if os.path.exists(MEM_FILE):
            with open(MEM_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                return [m for m in data if "role" in m and "content" in m]
    except Exception:
        pass
    return []

def save_memory(conversation: List[Dict[str, str]]) -> None:
    try:
        with open(MEM_FILE, "w", encoding="utf-8") as f:
            json.dump(conversation[-2*MAX_TURNS:], f, ensure_ascii=False, indent=2)
    except Exception:
        pass

# ====== IA (OpenAI) com memória ======
conversation: List[Dict[str, str]] = load_memory()

def llm_reply(prompt: str) -> str:
    from openai import OpenAI
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        return "Sem OPENAI_API_KEY configurada. Defina a chave e tente novamente."

    client = OpenAI(api_key=key)
    conversation.append({"role": "user", "content": prompt})
    if len(conversation) > 2 * MAX_TURNS:
        del conversation[: len(conversation) - 2 * MAX_TURNS]

    system_msg = {
        "role": "system",
        "content": (
            "Você é o Jarvis, um assistente útil e educado. "
            "Responda em português BR por padrão. "
            "Se o usuário pedir explicitamente outro idioma, responda nesse idioma. "
            "Seja claro e objetivo; use explicações passo a passo apenas quando pedirem."
        ),
    }

    try:
        msg = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[system_msg] + conversation,
            temperature=0.6,
            max_tokens=300,
        )
        reply = msg.choices[0].message.content.strip()
        conversation.append({"role": "assistant", "content": reply})
        save_memory(conversation)
        return reply
    except Exception as e:
        return f"OpenAI erro: {e}"

# ====== TTS opcional ======
def init_tts():
    try:
        import pyttsx3
        eng = pyttsx3.init()
        vid = None
        for v in eng.getProperty("voices"):
            name = (v.name or "").lower()
            lang = "".join(getattr(v, "languages", [])).lower()
            if "portuguese" in name or "pt_" in lang or "brazil" in name:
                vid = v.id
                break
        if vid:
            eng.setProperty("voice", vid)
        eng.setProperty("rate", 185)
        eng.setProperty("volume", 1.0)
        return eng
    except Exception:
        return None

def say(text: str, tts_engine=None, voice_on=False):
    print(f"Jarvis: {text}")
    if voice_on and tts_engine:
        try:
            tts_engine.say(text)
            tts_engine.runAndWait()
        except Exception:
            pass

# ====== Ações locais ======
def ip_local() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "desconhecido"

def spawn_cubo(url="http://127.0.0.1:8000"):
    try:
        import httpx
        httpx.post(
            f"{url}/spawn",
            json={"id": "cube1", "type": "cube", "pos": [0, 1.2, 0.5], "color": "#00ffff"},
            timeout=3.0,
        )
        return "Cubo criado."
    except Exception:
        return "Não consegui falar com o servidor de cena."

def handle(cmd: str, voice_on: bool, tts_engine, scene_url: str) -> Optional[bool]:
    c = cmd.strip().lower()

    if c in {"parar", "sair", "quit", "exit"}:
        say("Encerrando. Até logo!", tts_engine, voice_on)
        return True

    if c in {"/reset", "reset", "limpar memória", "limpar memoria"}:
        conversation.clear()
        save_memory(conversation)
        say("Memória limpa.", tts_engine, voice_on)
        return False

    if c in {"/mem", "memoria", "memória"}:
        say(f"Itens na memória: {len(conversation)}", tts_engine, voice_on)
        return False

    if c in {"/save", "salvar"}:
        save_memory(conversation)
        say("Memória salva.", tts_engine, voice_on)
        return False

    if "hora" in c:
        say(time.strftime("Agora são %H:%M."), tts_engine, voice_on)
        return False

    if "ip" in c:
        say(f"Seu IP local é {ip_local()}", tts_engine, voice_on)
        return False

    if "spawn cubo" in c or "criar cubo" in c:
        say(spawn_cubo(scene_url), tts_engine, voice_on)
        return False

    resp = llm_reply(cmd)
    say(resp, tts_engine, voice_on)
    return False

def main():
    ap = argparse.ArgumentParser(description="Jarvis CLI (texto)")
    ap.add_argument("--voice", choices=["on", "off"], default="off", help="voz TTS local")
    ap.add_argument("--scene", default="http://127.0.0.1:8000", help="URL do servidor de cena")
    args = ap.parse_args()

    voice_on = args.voice == "on"
    tts_engine = init_tts() if voice_on else None

    print("Jarvis: online. Digite comandos. ('parar' para sair)")
    print("Dicas: 'que horas são', 'qual meu ip', 'spawn cubo', '/reset', '/mem', '/save', ou qualquer pergunta de IA.")
    if conversation:
        print(f"(memória carregada: {len(conversation)} itens)")

    try:
        while True:
            cmd = input("Você> ").strip()
            if not cmd:
                continue
            done = handle(cmd, voice_on, tts_engine, args.scene)
            if done:
                break
    except (KeyboardInterrupt, EOFError):
        print()
        say("Encerrando. Até logo!", tts_engine, voice_on)
    finally:
        save_memory(conversation)

if __name__ == "__main__":
    main()
