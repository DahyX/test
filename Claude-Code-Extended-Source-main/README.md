<div align="center">

# ⚡ Claude Code Leak — Extended Source ( Apr 1 2026 )

### 🧠 Extended Leak Edition

<img src="https://img.shields.io/badge/ARCHIVED-ZIDHUXD-black?style=for-the-badge&logo=github">
<img src="https://img.shields.io/badge/TYPE-Source%20Code-blue?style=for-the-badge&logo=typescript">
<img src="https://img.shields.io/badge/RUNTIME-Bun-pink?style=for-the-badge&logo=bun">
<img src="https://img.shields.io/badge/UI-React%20%2B%20Ink-61DAFB?style=for-the-badge&logo=react&logoColor=black">

> Full Claude Code CLI source — cleaned, structured, and enhanced.

</div>

---

## 🚀 Overview

This repository contains the **complete internal source** of Claude Code.

But this isn’t just a dump.

This version is:

✨ Cleaned for readability
✨ Structured for exploration
✨ Optimized for developers
✨ Presented with clarity

---

## 🧠 What is Claude Code?

Claude Code is a **terminal-native AI assistant** capable of:

💻 File editing and manipulation
⚙️ Running shell commands
🔍 Searching entire codebases
🌐 Fetching and processing web data
🤖 Spawning agents and workflows
📦 Managing git operations

All directly from your CLI.

---

## 🧾 How It Became Public

The source surfaced due to:

🧩 Source maps accidentally published in npm package
🔍 Community reverse analysis
🌐 Public storage exposure

📣 First publicly highlighted by Chaofan Shou on X:
[https://x.com/Fried_rice/status/2038894956459290963](https://x.com/Fried_rice/status/2038894956459290963)

Later acknowledged and released publicly.

---

## 📊 Project Stats

| Metric      | Value               |
| ----------- | ------------------- |
| 🧠 Language | TypeScript (strict) |
| ⚡ Runtime   | Bun                 |
| 📦 Files    | ~1,900              |
| 📏 Lines    | 500K+               |
| 🎨 UI       | React + Ink         |

---

## 🏗️ Architecture Breakdown

### 🧰 Tool System

Every capability is a modular tool.

Includes:

📂 File operations
🔍 Search tools
⚙️ Execution tools
🤖 Agent tools

Each tool has:

✔ Schema
✔ Permissions
✔ Execution logic

---

### 💬 Command System

User-triggered slash commands:

| Command   | Action      |
| --------- | ----------- |
| `/commit` | Git commit  |
| `/review` | Code review |
| `/config` | Settings    |
| `/doctor` | Diagnostics |
| `/mcp`    | MCP control |

---

### 🧩 Service Layer

Handles:

🔐 Auth
📡 API communication
🧮 Token tracking
🧠 Memory system
🔌 Plugins

---

### 🔗 Bridge System

Connects CLI with IDEs:

🧑‍💻 VS Code
🧠 JetBrains

Handles messaging and session sync.

---

### 🛡️ Permission System

Every action is validated.

Modes:

🔹 Default
🔹 Plan
🔹 Auto
🔹 Bypass

---

### 🚩 Feature Flags

Build-time toggles:

🎙️ Voice mode
🤖 Agent triggers
🔗 Bridge mode
⚡ Proactive systems

---

## 📁 Directory Structure

```
src/
├── main.tsx
├── QueryEngine.ts
├── Tool.ts
├── commands.ts
├── tools.ts

├── tools/
├── commands/
├── components/
├── services/
├── hooks/
├── utils/
├── screens/

├── bridge/
├── coordinator/
├── plugins/
├── skills/
├── server/
├── tasks/
├── state/
```

---

## 📌 Key Files

| File              | Description              |
| ----------------- | ------------------------ |
| 🧠 QueryEngine.ts | Core AI execution engine |
| 🧰 Tool.ts        | Tool system definitions  |
| 💬 commands.ts    | Command registry         |
| 🚀 main.tsx       | CLI entry + UI           |

---

## 🔍 MCP Explorer

Explore the entire codebase programmatically.

### Install

```bash
claude mcp add claude-code-explorer -- npx -y claude-code-explorer-mcp
```

---

### Manual Setup

```bash
git clone https://github.com/nirholas/claude-code.git
cd claude-code/mcp-server
npm install
npm run build

claude mcp add claude-code-explorer -- node dist/index.js
```

---

## 🧠 Design Patterns

⚡ Parallel initialization
📦 Lazy loading
🤖 Agent orchestration
🔌 Plugin architecture

---

## 🎯 Why This Repo Exists

This is not just for viewing.

It’s for:

🧠 Learning large-scale AI systems
🔍 Reverse engineering architecture
⚙️ Understanding tool-based agents

---

## ⚠️ Disclaimer

This repository contains source code originally developed by Anthropic.

It is shared for:

📚 Educational purposes
🔬 Research
🧠 Exploration

---

## 🧬 Credits

👨‍💻 Original: Anthropic
🔍 Discovery: Community
⚡ Extended Version: **ZIDHUXD**

---

<div align="center">

### ⚡ Built for explorers, not beginners

</div>
