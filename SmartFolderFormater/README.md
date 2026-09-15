# Smart File Organizer

A simple native Windows desktop file organizer written in **C using the Win32 API (`windows.h`)**.

No Qt, GTK, raylib, or other GUI framework is required.

## Features

- Native Windows GUI
- Folder selection dialog
- File scanning using Windows file APIs
- Automatic file categorization
- Preview of files before moving them
- Images, Documents, Videos, Audio, Archives, Programs, Other
- Creates category folders automatically
- Does not overwrite existing files
- Renames duplicates using `_1`, `_2`, etc.
- Organization history
- Undo the complete last organization batch
- Simple status reporting
- Single C source file for easy lab submission

## Project structure

```text
SmartFileOrganizer/
├── src/
│   └── main.c
├── data/
│   └── history.log        # created automatically after organizing
├── SmartFileOrganizer.exe # created by run.bat
├── run.bat
└── README.md
```

## Requirements

Windows 10/11 and a GCC compiler such as MinGW-w64.

The following Windows libraries are used:

- `windows.h`
- `shell32.dll`

No third-party GUI library is required.

## Build and Run

Open Command Prompt in the project folder and run:

```bat
run.bat
```

The script:

1. Checks whether `gcc` is available.
2. Compiles `src\main.c`.
3. Creates `SmartFileOrganizer.exe`.
4. Starts the application.

You can also compile manually:

```bat
gcc src\main.c -o SmartFileOrganizer.exe -mwindows -Wall -Wextra -O2 -lshell32 -lole32
```

## How to use

1. Open the application.
2. Click **Browse...**.
3. Select a folder such as `Downloads`.
4. Click **Scan**.
5. Review the detected files.
6. Click **Organize Files**.
7. The application creates folders such as:

```text
Downloads/
├── Images/
├── Documents/
├── Videos/
├── Audio/
├── Archives/
├── Programs/
└── Other/
```

8. If you want to reverse the last complete organization operation, click **Undo Last Organization**.

## File categories

### Images

```text
jpg jpeg png gif bmp webp svg ico tif tiff
```

### Documents

```text
pdf doc docx txt rtf xls xlsx ppt pptx csv odt ods odp
```

### Videos

```text
mp4 mkv avi mov wmv flv webm m4v
```

### Audio

```text
mp3 wav flac aac ogg m4a wma
```

### Archives

```text
zip rar 7z tar gz bz2 xz
```

### Programs

```text
exe msi bat cmd com
```

Everything else goes into `Other`.

## Safety behavior

The application does not overwrite an existing file.

For example, if:

```text
Images\photo.jpg
```

already exists, a new file may become:

```text
Images\photo_1.jpg
```

The application also asks for confirmation before moving files.

## Undo system

Every successful move is written to:

```text
data\history.log
```

Each organization run receives a batch ID. The Undo button restores all files belonging to the latest batch rather than only one file.

## Important limitations

This is a desktop educational project, not a production file-management system.

- It currently scans only the selected folder, not its subfolders.
- File type detection is based on file extension.
- Hidden files are skipped.
- Undo depends on the source and destination files still being available and unchanged.
- Very large folders are limited to 10,000 files per scan.

## Concepts demonstrated

This project demonstrates several C and Windows programming concepts:

- Win32 window creation
- Windows message loop
- GUI controls
- Event handling
- File system traversal
- `FindFirstFileA` / `FindNextFileA`
- `CreateDirectoryA`
- `MoveFileExA`
- Windows folder dialogs
- Structures and enums
- Strings and buffers
- File I/O
- Dynamic memory with `realloc`
- Logging
- Error handling
- Modular program design

## Future improvements

Possible V2 features:

- Drag and drop
- Recursive folder scanning
- Custom categories
- Custom extension rules
- File size statistics
- Duplicate detection using file hashes
- Search and filtering
- Dark mode
- Scheduled automatic organization
- Exportable reports
- More detailed operation history
