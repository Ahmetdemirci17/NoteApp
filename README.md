# 📝 NoteFlow

A modern, AI-powered note-taking application built with Python.

NoteFlow is a feature-rich desktop note management application inspired by modern productivity tools. It combines powerful note organization, rich text editing, and AI-assisted workflows into a clean and intuitive interface.

## ✨ Features

### 📚 Note Management

* Create, edit, and delete notes
* Real-time search functionality
* Tag-based organization
* Automatic saving
* Word and character counter
* Local JSON-based storage

### 🎨 Rich Text Editing

* Bold text formatting
* Italic text formatting
* Underlined text
* Text color customization
* Text highlighting
* Custom fonts and font sizes
* Modern editing experience

### 🌙 Modern User Interface

* Light Mode and Dark Mode
* Three-panel layout
* Responsive design
* Built with CustomTkinter
* Keyboard shortcuts for productivity

### 🤖 AI-Powered Features

* Integrated Gemini AI assistant
* Note summarization
* Grammar and spelling correction
* Merge related notes into a single document
* Context-aware conversations based on note content

## ⌨️ Keyboard Shortcuts

| Shortcut         | Action            |
| ---------------- | ----------------- |
| Ctrl + N         | Create New Note   |
| Ctrl + S         | Save Note         |
| Ctrl + A         | Select All Text   |
| Ctrl + Shift + A | Open AI Assistant |

## 🛠️ Technologies Used

* Python 3.12+
* Tkinter
* CustomTkinter
* Google Gemini API
* Keyring
* JSON Storage

## 📦 Installation

### Clone the Repository

```bash
git clone https://github.com/Ahmetdemirci17/Noteapp.git
cd Noteapp
```

### Create a Virtual Environment

```bash
python -m venv venv
```

Linux/macOS:

```bash
source venv/bin/activate
```

Windows:

```bash
venv\Scripts\activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Run the Application

```bash
python main.py
```

## 🧠 AI Capabilities

NoteFlow leverages Google's Gemini AI to:

* Summarize long notes
* Improve grammar and writing quality
* Merge notes with similar topics
* Answer questions about your notes
* Assist with content creation and organization

## 📁 Data Storage

All notes and settings are stored locally on the user's machine using JSON files.

Example structure:

```text
data/
├── notes.json
└── settings.json
```

,

## 🚀 Roadmap

* Markdown support
* Cloud synchronization
* PDF export
* Advanced text editor tools
* Multiple notebooks/workspaces
* AI-powered automatic tagging
* Cross-device synchronization

## 🔒 Privacy

Your notes are stored locally on your device. No note data is shared externally unless you explicitly use AI-powered features.

## 📄 License

This project is licensed under the MIT License.

## 👨‍💻 Developer

**Ahmet Demirci**

GitHub: https://github.com/Ahmetdemirci17
