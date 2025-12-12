import os, sys, time, platform, socket, subprocess
import speech_recognition as sr
import pyttsx3

# ===== TTS (voz) =====
def init_tts():
    eng = pyttsx3.init()
    # tenta voz pt-BR se existir
    vid = None
    for v in eng.getProperty("voices"):
        name = (v.name or "").lower()
        lang = "".join(v.languages).lower() if hasattr(v, "languages") else ""
        if "portuguese" in name or "pt_" in lang or "brazil" in name:
            vid = v.id; break
    if vid: eng.setProperty("voice", vid)
    eng.setProperty("rate", 185)   # velocidade
    eng.setProperty("volume", 1.0)
    return eng

tts = init_tts()

def say(text:str):
    print(f"Jarvis:", text)
    try:
        tts.say(text); tts.runAndWait()
    except Exception:
        pass

# ===== STT (escuta) =====
r = sr.Recognizer()

def listen(timeout=4, phrase_time_limit=8):
    with sr.Microphone() as mic:
        r.adjust_for_ambient_noise(mic, duration=0.6)
        audio = r.listen(mic, timeout=timeout, phrase_time_limit=phrase_time_limit)
    try:
        # usa serviço grátis do Google (precisa internet)
        text = r.recognize_google(audio, language="pt-BR")
        return text.strip()
    except sr.UnknownValueError:
        return ""
    except Exception as e:
        print("STT erro:", e)
        return ""

# ===== util =====
def get_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]; s.close()
        return ip
    except Exception:
        return "desconhecido"

# ===== OpenAI opcional =====
def reply_llm(prompt:str):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        msg = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role":"system","content":"Responda em PT-BR, breve e útil."},
                      {"role":"user","content":prompt}],
            temperature=0.6,
            max_tokens=180
        )
        return msg.choices[0].message.content.strip()
    except Exception as e:
        print("OpenAI erro:", e)
        return None

# ===== Ações locais simples =====
def handle_command(cmd:str):
    c = cmd.lower()

    if c in ("sair","fechar","encerrar","tchau","parar"):
        say("Encerrando. Até logo!"); sys.exit(0)

    if "que horas" in c or "hora" in c:
        say(time.strftime("Agora são %H:%M.")); return

    if "ip" in c:
        say(f"Seu IP local é {get_ip()}"); return

    if "abrir jupyter" in c:
        subprocess.Popen(["cmd","/c","start","", "http://localhost:8888/lab"]); 
        say("Abrindo Jupyter."); return

    if "abrir vscode" in c or "abrir vs code" in c:
        subprocess.Popen(["cmd","/c","code","C:\\Dev\\projects\\MeuProjeto"])
        say("Abrindo Visual Studio Code."); return

    if "spawn cubo" in c or "criar cubo" in c:
        # exemplo: envia comando pro Jarvis server (se você rodar ele depois)
        try:
            import httpx
            httpx.post("http://127.0.0.1:8000/spawn",
                       json={"id":"cube1","type":"cube","pos":[0,1.2,0.5],"color":"#00ffff"},
                       timeout=3.0)
            say("Cubo criado.")
        except Exception:
            say("Não consegui falar com o servidor de cena.")
        return

    # fallback IA (se tiver key)
    llm = reply_llm(cmd)
    if llm:
        say(llm)
    else:
        say("Comando recebido, mas não tenho uma ação definida para isso.")

def main():
    say("Jarvis online. Diga 'parar' para encerrar.")
    while True:
        try:
            input("Pressione Enter e fale... ")
            say("Estou ouvindo.")
            text = listen()
            if not text:
                say("Não entendi. Pode repetir?")
                continue
            print("Você:", text)
            handle_command(text)
        except KeyboardInterrupt:
            say("Encerrando por teclado."); break
        except Exception as e:
            print("Loop erro:", e)

if __name__ == "__main__":
    main()
