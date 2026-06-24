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
* Docker & Docker Compose

## 📦 Installation & Setup

Choose one of the following methods to install and run NoteFlow.

### Option 1: Docker Installation (Recommended for Linux)

#### 1. Prerequisites
Ensure you have Docker and Docker Compose installed on your system:

```bash
sudo apt update
sudo apt install docker.io docker-compose
sudo usermod -aG docker $USER
# (Log out and log back in, or open a new terminal for changes to take effect)
