import os, json, subprocess, signal, time
from pathlib import Path
import streamlit as st

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
DATA.mkdir(exist_ok=True)
PID = DATA / "runner.pid"
LOG = DATA / "logs.json"
STATE = DATA / ".state.json"
ENV_FILE = ROOT / ".env.local"
RUNNER = ROOT / "kucoin-bot-run.sh"

st.set_page_config(page_title="KuCoin MultiBot (Paper)", page_icon="🤖", layout="wide")
st.title("🤖 KuCoin MultiBot — Paper Dashboard")

def read_env():
    env = {"ENV": "paper"}
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k,v = line.split("=",1)
            env[k.strip()] = v.strip()
    return env

def write_env(upd: dict):
    cur = read_env()
    cur.update(upd)
    lines = [f"{k}={v}" for k,v in cur.items()]
    ENV_FILE.write_text("\n".join(lines) + "\n")

env = read_env()
st.sidebar.subheader("Environment")
st.sidebar.write(f"Current ENV: `{env.get('ENV','paper')}`")
with st.sidebar.expander("Edit .env.local"):
    new_env = st.text_area("Contents of .env.local", ENV_FILE.read_text() if ENV_FILE.exists() else "", height=200)
    if st.button("Save .env.local"):
        ENV_FILE.write_text(new_env)
        st.success("Saved .env.local")

c1, c2, c3, c4 = st.columns(4)
if c1.button("Smoke Test"):
    subprocess.run(["bash", str(RUNNER), "--smoke"], check=False)
    st.success("Smoke executed")

if c2.button("Run Once"):
    subprocess.run(["bash", str(RUNNER), "--once"], check=False)
    st.success("One iteration executed")

def start_loop():
    if PID.exists():
        return False, "Loop already running"
    proc = subprocess.Popen(["bash", str(RUNNER), "--loop"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    PID.write_text(str(proc.pid))
    return True, f"Loop started with PID {proc.pid}"

def stop_loop():
    if not PID.exists(): return False, "No loop PID found"
    try:
        pid = int(PID.read_text().strip())
        os.kill(pid, signal.SIGTERM)
        time.sleep(1)
    except Exception as e:
        return False, f"Failed to stop: {e}"
    finally:
        PID.unlink(missing_ok=True)
    return True, "Loop stopped"

if c3.button("Start 60s Loop (paper)"):
    ok, msg = start_loop()
    st.write(msg)
if c4.button("Stop Loop"):
    ok, msg = stop_loop()
    st.write(msg)

st.subheader("logs.json (tail)")
if LOG.exists():
    try:
        data = [json.loads(line) for line in LOG.read_text().splitlines()[-50:] if line.strip()]
        st.json(data)
    except Exception as e:
        st.warning(f"Could not parse logs.json: {e}")
else:
    st.info("No logs.json yet")

st.subheader(".state.json")
if STATE.exists():
    try:
        st.json(json.loads(STATE.read_text()))
    except Exception as e:
        st.warning(f"Could not parse .state.json: {e}")
else:
    st.info("No .state.json yet")
