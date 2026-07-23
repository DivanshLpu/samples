Here are the exact commands to build a standalone executable on each OS. You need to run the matching command **on that actual OS** — PyInstaller doesn't cross-compile.

## 🐧 Linux

```bash
# Install Python + pip if not already present
sudo apt update && sudo apt install -y python3 python3-pip

# Install PyInstaller
pip3 install pyinstaller

# Build the executable
pyinstaller --onefile --name split_join_linux split_join.py

# Output binary will be at:
# dist/split_join_linux

# Make it executable and test
chmod +x dist/split_join_linux
./dist/split_join_linux split myfile.zip --size 900
```

## 🍎 macOS

```bash
# Install Python if needed (via Homebrew)
brew install python3

# Install PyInstaller
pip3 install pyinstaller

# Build the executable
pyinstaller --onefile --name split_join_mac split_join.py

# Output binary will be at:
# dist/split_join_mac

# Make it executable and test
chmod +x dist/split_join_mac
./dist/split_join_mac split myfile.zip --size 900
```
> Note: macOS Gatekeeper may block the binary the first time — right-click → Open, or run:
> `xattr -d com.apple.quarantine dist/split_join_mac`

## 🪟 Windows

Run in **PowerShell** or **Command Prompt**:

```powershell
# Install PyInstaller (assuming Python is already installed and on PATH)
pip install pyinstaller

# Build the executable
pyinstaller --onefile --name split_join_windows split_join.py

# Output will be at:
# dist\split_join_windows.exe

# Test it
dist\split_join_windows.exe split myfile.zip --size 900
```

---

## After building on each OS

You'll end up with 3 separate files:
```
split_join_linux      (no extension)
split_join_mac        (no extension)
split_join_windows.exe
```

Each one is fully standalone — no Python installation needed to run them on that OS.