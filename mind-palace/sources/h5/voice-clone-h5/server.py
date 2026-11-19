#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MiniMax 音色克隆 H5 工具 · 本地后端
启动后浏览器自动打开 http://localhost:8765
"""
import os
import sys
import time
import threading
import webbrowser
import requests
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__, static_folder=BASE_DIR, static_url_path="")
CORS(app)

DASHSCOPE_URL = "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation"
MODEL = "MiniMax/speech-2.8-hd"
PORT = 8765


def get_api_key():
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return auth[7:].strip()
    return ""


@app.route("/")
def index():
    return send_from_directory(BASE_DIR, "index.html")


@app.route("/api/health")
def health():
    return jsonify({"ok": True, "model": MODEL})


@app.route("/api/clone", methods=["POST"])
def clone():
    api_key = get_api_key()
    if not api_key:
        return jsonify({"error": "缺少 API Key"}), 401
    if "audio" not in request.files:
        return jsonify({"error": "请上传音频文件"}), 400

    audio = request.files["audio"]
    audio_bytes = audio.read()
    if len(audio_bytes) < 1024:
        return jsonify({"error": "音频文件太小（< 1KB），请检查文件"}), 400
    if len(audio_bytes) > 20 * 1024 * 1024:
        return jsonify({"error": "音频文件太大（> 20MB），请压缩后再试"}), 400

    # 1. 上传到公网（catbox.moe）
    print(f"📤 上传音频到公网：{audio.filename} ({len(audio_bytes)//1024} KB)")
    try:
        r = requests.post(
            "https://catbox.moe/user/api.php",
            data={"reqtype": "fileupload"},
            files={"fileToUpload": (audio.filename, audio_bytes, "audio/mpeg")},
            timeout=180,
        )
    except Exception as e:
        return jsonify({"error": f"上传到公网失败：{e}"}), 500
    audio_url = r.text.strip()
    if r.status_code != 200 or not audio_url.startswith("http"):
        return jsonify({"error": f"上传到公网失败：{r.text[:200]}"}), 500
    print(f"   ✅ {audio_url}")

    # 2. 调百炼 voice_clone
    voice_id = f"myvoice{int(time.time())}"
    print(f"🎙️  克隆音色 → {voice_id}")
    payload = {
        "model": MODEL,
        "input": {
            "action": "voice_clone",
            "voice_id": voice_id,
            "audio_url": audio_url,
            "text": "这是一段用来测试克隆音色的试听文本，请忽略内容本身。",
        },
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json; charset=utf-8",
    }
    try:
        r = requests.post(DASHSCOPE_URL, headers=headers, json=payload, timeout=120)
        r.raise_for_status()
        out = r.json()
    except Exception as e:
        return jsonify({"error": f"调用百炼 API 失败：{e}"}), 500

    base = out.get("output", {}).get("base_resp", {})
    if base.get("status_code") != 0:
        msg = base.get("status_msg", "未知错误")
        return jsonify({"error": f"克隆失败：{msg}（请检查 API Key 是否有效、账号是否开通了 MiniMax 服务）"}), 500

    demo_audio = out["output"].get("demo_audio", "")
    print(f"   ✅ 克隆成功！voice_id = {voice_id}")
    return jsonify({
        "voice_id": voice_id,
        "demo_audio": demo_audio,
        "audio_url": audio_url,
    })


@app.route("/api/synthesize", methods=["POST"])
def synthesize():
    api_key = get_api_key()
    if not api_key:
        return jsonify({"error": "缺少 API Key"}), 401

    data = request.json or {}
    text = (data.get("text") or "").strip()
    voice_id = (data.get("voice_id") or "").strip()
    if not text:
        return jsonify({"error": "文本为空"}), 400
    if not voice_id:
        return jsonify({"error": "缺少 voice_id"}), 400
    if len(text) > 10000:
        return jsonify({"error": "单段文本超过 10000 字符，请拆分"}), 400

    payload = {
        "model": MODEL,
        "input": {
            "text": text,
            "voice_setting": {"voice_id": voice_id, "speed": 1.0, "vol": 1.0, "pitch": 0},
            "audio_setting": {"sample_rate": 32000, "bitrate": 128000, "format": "mp3", "channel": 1},
        },
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    try:
        r = requests.post(DASHSCOPE_URL, headers=headers, json=payload, timeout=300)
        r.raise_for_status()
        out = r.json()
    except Exception as e:
        return jsonify({"error": f"合成失败：{e}"}), 500

    audio_hex = out.get("output", {}).get("data", {}).get("audio", "")
    if not audio_hex:
        base = out.get("output", {}).get("base_resp", {})
        return jsonify({"error": f"合成失败：{base.get('status_msg', '返回为空')}"}), 500

    return jsonify({
        "audio_hex": audio_hex,
        "chars": len(text),
    })


def open_browser():
    time.sleep(1.5)
    webbrowser.open(f"http://localhost:{PORT}")


if __name__ == "__main__":
    print()
    print("=" * 60)
    print(f"  🎙️  MiniMax 音色克隆工具  ·  本地服务已启动")
    print(f"  📱  浏览器地址：http://localhost:{PORT}")
    print(f"  ⏹   关闭服务：按 Ctrl+C  (或关掉这个窗口)")
    print("=" * 60)
    print()
    threading.Thread(target=open_browser, daemon=True).start()
    try:
        app.run(host="127.0.0.1", port=PORT, debug=False, use_reloader=False)
    except KeyboardInterrupt:
        print("\n👋 已关闭")
