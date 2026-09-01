# SplitJoin

SplitJoin is a reliable, cross-platform command-line utility for splitting large files into fixed-size parts and reconstructing them later—even if every part has been renamed, moved, or shuffled.

Unlike traditional file splitters that rely on filenames or numbering, SplitJoin embeds metadata directly inside every part file. During reconstruction, it scans the available files, reads the embedded metadata, automatically identifies which parts belong together, verifies their integrity, and restores the original file safely.

---

# Features

* 📦 Split files into fixed-size parts
* 🔄 Rejoin files even if the part filenames have been renamed
* 🏷️ Embedded metadata inside every part file
* 🔍 Automatically discovers parts by scanning folders
* 🔐 SHA-256 verification for every part
* ✅ Final integrity verification of the reconstructed file
* 📁 Multiple split jobs can coexist inside the same directory
* 🚀 Native executables for Windows, Linux, and macOS
* 💾 Stream-based processing (does not load the entire file into memory)
* 📄 Supports very large files

---

# How It Works

Each generated part file contains two sections:

1. **Embedded JSON Metadata**
2. **Binary File Data**

The embedded metadata stores:

* Unique File ID
* Part Number
* Total Number of Parts
* Original Filename
* Original File Size
* SHA-256 Hash of the Original File
* SHA-256 Hash of the Part

Because this information is stored inside every part file, SplitJoin never depends on filenames.

You can safely:

* Rename part files
* Move them to another folder
* Shuffle their order
* Change their extensions

SplitJoin will still correctly identify and reconstruct the original file.

---

# Usage

## Windows

Use the compiled executable:

```cmd
splitjoin.exe split myfile.zip --size 900
```

or after installation:

```cmd
splitjoin split myfile.zip --size 900
```

---

## Linux

```bash
splitjoin split myfile.zip --size 900
```

---

## macOS

```bash
splitjoin split myfile.zip --size 900
```

---

# Split a File

Split a large file into **900 MB** parts:

### Windows

```cmd
splitjoin.exe split myfile.zip --size 900
```

### Linux / macOS

```bash
splitjoin split myfile.zip --size 900
```

Example:

```text
splitjoin split Ubuntu.iso --size 900
```

---

# Join Files

Restore the original file from a folder containing its parts.

### Windows

```cmd
splitjoin.exe join ./folder_with_parts --output restored_file.zip
```

### Linux / macOS

```bash
splitjoin join ./folder_with_parts --output restored_file.zip
```

Example:

```text
splitjoin join ./parts --output Ubuntu.iso
```

The filenames of the part files do **not** need to match the originals.

---

# List Available Split Jobs

If a folder contains parts from multiple split operations:

### Windows

```cmd
splitjoin.exe list ./folder_with_parts
```

### Linux / macOS

```bash
splitjoin list ./folder_with_parts
```

The command displays:

* File ID
* Original Filename
* Original File Size
* Total Parts
* Available Parts
* Missing Parts
* Status (Complete / Incomplete)

---

# Join a Specific File

If multiple split jobs exist in the same folder:

### Windows

```cmd
splitjoin.exe join ./folder_with_parts --file-id YOUR_FILE_ID --output restored_file.zip
```

### Linux / macOS

```bash
splitjoin join ./folder_with_parts --file-id YOUR_FILE_ID --output restored_file.zip
```

---

# Why SplitJoin?

Traditional splitters rely on filenames such as:

```text
movie.part001
movie.part002
movie.part003
```

If those files are renamed or mixed with parts from another split operation, reconstruction usually fails.

SplitJoin stores all identification data **inside every part file**, making reconstruction independent of filenames.

---

# Data Integrity

SplitJoin verifies data at multiple stages:

* SHA-256 verification of every part
* Detection of missing parts
* Detection of duplicate parts
* Detection of corrupted parts
* Final SHA-256 verification of the reconstructed file

If any verification fails, reconstruction stops to prevent generating a corrupted output file.

---

# Typical Workflow

1. Split a large file.
2. Transfer or store the generated parts.
3. Rename or reorganize them if desired.
4. Place all parts into one folder.
5. Run the **join** command.
6. SplitJoin automatically discovers, verifies, and reconstructs the original file.

---

# Command Summary

## Split

```text
splitjoin split <file> --size <MB>
```

## List

```text
splitjoin list <folder>
```

## Join

```text
splitjoin join <folder> --output <output-file>
```

## Join Specific File

```text
splitjoin join <folder> --file-id <UUID> --output <output-file>
```

---

# Supported Platforms

* Windows (`splitjoin.exe`)
* Linux (`splitjoin`)
* macOS (`splitjoin`)

---

# License

FREEEEEEEEEEE my utility
