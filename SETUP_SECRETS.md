# Secrets Setup Guide

This project uses secrets management to avoid committing sensitive data to git.

## For Python Backend (.env)

1. Create `.env` at the repo root (already in `.gitignore`):
   ```bash
   echo 'OPENAI_API_KEY="your-key-here"' > .env
   ```
   - Never commit `.env`
   - `.env` is auto-loaded by `config.py` on startup

## For ESP32 Firmware (secrets.h)

1. Copy the template:
   ```bash
   cp firmware/secrets.h.example firmware/secrets.h
   ```

2. Edit `firmware/secrets.h` with your actual values:
   ```c
   #define WIFI_SSID "your-network-name"
   #define WIFI_PASSWORD "your-wifi-password"
   #define OTA_SERVER_IP "192.168.1.100"          // laptop IP running the FastAPI server
   #define OTA_SERVER_PORT 5001
   #define OTA_BASE_URL "http://192.168.1.100:5001"
   ```

3. Never commit `firmware/secrets.h` — it's in `.gitignore`

## Workflow

- During firmware compilation (via LangChain agent), the generated `.cpp` includes `#include "secrets.h"`
- The build system (Arduino CLI) finds `secrets.h` at compile time
- Your actual SSID/password/IPs never appear in the git history or templates

## If You Accidentally Commit a Secret

1. **Rotate the secret immediately** (GitHub will scan and flag it)
2. Rewrite git history with `git filter-branch` or `git filter-repo` to remove all traces
3. Never rely on "delete in the next commit" — it stays in the object database
