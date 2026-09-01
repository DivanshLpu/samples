"""
split_join.py - Split any file into fixed-size parts, and reliably rejoin
them later — EVEN IF THE PART FILES HAVE BEEN RENAMED.

How it works:
  Each part file contains a small JSON header (with a unique file_id,
  its part_index, total_parts, and hashes) followed by the raw chunk data.
  Joining scans a folder, reads these embedded headers (ignoring filenames
  entirely), groups parts by file_id, sorts by part_index, verifies each
  part's hash, concatenates them, and verifies the final file's hash
  against the original.

USAGE:
  Split a file into 900MB parts:
    python main.py split myfile.zip --size 900

  Join parts back (parts can be renamed/shuffled):
    python main.py join ./folder_with_parts --output myfile_restored.zip

  If a folder has parts from MORE THAN ONE split job, list file_ids first:
    python main.py list ./folder_with_parts

  Then join a specific one:
    python main.py join ./folder_with_parts --file-id <id> --output myfile_restored.zip
"""

import argparse
import os
import sys
import json
import uuid
import hashlib

CHUNK_READ_SIZE = 8 * 1024 * 1024
HEADER_LEN_BYTES = 4


def human_size(num_bytes):
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if num_bytes < 1024:
            return f"{num_bytes:.2f} {unit}"
        num_bytes /= 1024
    return f"{num_bytes:.2f} PB"


def sha256_of_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            block = f.read(CHUNK_READ_SIZE)
            if not block:
                break
            h.update(block)
    return h.hexdigest()


def write_part_header(outfile, header_dict):
    header_bytes = json.dumps(header_dict).encode("utf-8")
    outfile.write(len(header_bytes).to_bytes(HEADER_LEN_BYTES, "big"))
    outfile.write(header_bytes)


def read_part_header(path):
    try:
        with open(path, "rb") as f:
            len_bytes = f.read(HEADER_LEN_BYTES)
            if len(len_bytes) < HEADER_LEN_BYTES:
                return None, None
            header_len = int.from_bytes(len_bytes, "big")
            if header_len <= 0 or header_len > 1_000_000:
                return None, None
            header_bytes = f.read(header_len)
            if len(header_bytes) < header_len:
                return None, None
            header = json.loads(header_bytes.decode("utf-8"))
            if header.get("format") != "split_join_v1":
                return None, None
            payload_offset = HEADER_LEN_BYTES + header_len
            return header, payload_offset
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return None, None


def split_file(input_path, part_size_bytes, output_dir=None):
    if not os.path.isfile(input_path):
        print(f"Error: file not found: {input_path}")
        sys.exit(1)

    total_size = os.path.getsize(input_path)
    base_name = os.path.basename(input_path)
    out_dir = output_dir or os.path.dirname(os.path.abspath(input_path))
    os.makedirs(out_dir, exist_ok=True)

    file_id = uuid.uuid4().hex

    print(f"Splitting '{input_path}' ({human_size(total_size)}) into parts of {human_size(part_size_bytes)} each...")
    print(f"file_id: {file_id}  (embedded in every part — used to match parts, not filenames)")

    print("Computing checksum of original file...")
    original_hash = sha256_of_file(input_path)

    total_parts = (total_size + part_size_bytes - 1) // part_size_bytes if total_size > 0 else 1

    part_num = 0
    with open(input_path, "rb") as infile:
        for part_index in range(total_parts):
            part_num += 1
            part_name = f"{base_name}.part{part_num:03d}"
            part_path = os.path.join(out_dir, part_name)
            tmp_payload_path = part_path + ".payload.tmp"

            bytes_this_part = min(part_size_bytes, total_size - infile.tell())
            with open(tmp_payload_path, "wb") as tmp:
                remaining = bytes_this_part
                while remaining > 0:
                    data = infile.read(min(CHUNK_READ_SIZE, remaining))
                    if not data:
                        break
                    tmp.write(data)
                    remaining -= len(data)

            part_hash = sha256_of_file(tmp_payload_path)
            part_size_actual = os.path.getsize(tmp_payload_path)

            header = {
                "format": "split_join_v1",
                "file_id": file_id,
                "part_index": part_index,
                "total_parts": total_parts,
                "original_name": base_name,
                "original_size": total_size,
                "original_sha256": original_hash,
                "part_size": part_size_actual,
                "part_sha256": part_hash,
            }

            with open(part_path, "wb") as outfile:
                write_part_header(outfile, header)
                with open(tmp_payload_path, "rb") as tmp:
                    while True:
                        data = tmp.read(CHUNK_READ_SIZE)
                        if not data:
                            break
                        outfile.write(data)

            os.remove(tmp_payload_path)
            print(f"  Created {part_name} ({human_size(part_size_actual)}) [part_index={part_index}]")

    print(f"\nDone. {total_parts} parts created in: {out_dir}")
    print("Each part is self-describing — rename, move, or shuffle them freely;")
    print("'join' will still reconstruct the file correctly.")


def scan_for_parts(paths):
    candidate_files = []
    for p in paths:
        if os.path.isdir(p):
            for name in os.listdir(p):
                full = os.path.join(p, name)
                if os.path.isfile(full):
                    candidate_files.append(full)
        elif os.path.isfile(p):
            candidate_files.append(p)
        else:
            print(f"Warning: path not found, skipping: {p}")

    groups = {}
    for path in candidate_files:
        header, payload_offset = read_part_header(path)
        if header is None:
            continue
        fid = header["file_id"]
        groups.setdefault(fid, {"parts": {}, "meta": header})
        groups[fid]["parts"][header["part_index"]] = (path, payload_offset, header)

    return groups


def list_parts(paths):
    groups = scan_for_parts(paths)
    if not groups:
        print("No valid split_join part files found in the given path(s).")
        return

    print(f"Found {len(groups)} distinct file(s) among the parts:\n")
    for fid, info in groups.items():
        meta = info["meta"]
        found = len(info["parts"])
        total = meta["total_parts"]
        status = "COMPLETE" if found == total else f"INCOMPLETE ({found}/{total} parts found)"
        print(f"file_id: {fid}")
        print(f"  original_name: {meta['original_name']}")
        print(f"  original_size: {human_size(meta['original_size'])}")
        print(f"  status: {status}\n")


def join_files(paths, output_path=None, file_id=None):
    groups = scan_for_parts(paths)

    if not groups:
        print("Error: no valid split_join part files found in the given path(s).")
        sys.exit(1)

    if file_id:
        if file_id not in groups:
            print(f"Error: file_id '{file_id}' not found among the parts.")
            sys.exit(1)
        selected = {file_id: groups[file_id]}
    elif len(groups) == 1:
        selected = groups
    else:
        print(f"Error: found parts for {len(groups)} different files here.")
        print("Specify --file-id. Run 'list' to see options:\n")
        list_parts(paths)
        sys.exit(1)

    fid, info = next(iter(selected.items()))
    meta = info["meta"]
    total_parts = meta["total_parts"]
    original_name = meta["original_name"]

    missing = [i for i in range(total_parts) if i not in info["parts"]]
    if missing:
        print(f"Error: cannot reconstruct '{original_name}' — missing part_index(es): {missing}")
        sys.exit(1)

    output_path = output_path or f"restored_{original_name}"
    print(f"Reconstructing '{original_name}' -> '{output_path}' from {total_parts} parts...")

    with open(output_path, "wb") as outfile:
        for part_index in range(total_parts):
            path, payload_offset, header = info["parts"][part_index]

            with open(path, "rb") as infile:
                infile.seek(payload_offset)
                h = hashlib.sha256()
                remaining = header["part_size"]
                while remaining > 0:
                    data = infile.read(min(CHUNK_READ_SIZE, remaining))
                    if not data:
                        break
                    h.update(data)
                    remaining -= len(data)
                if h.hexdigest() != header["part_sha256"]:
                    print(f"Error: part_index {part_index} (file: {path}) failed checksum verification!")
                    sys.exit(1)

            with open(path, "rb") as infile:
                infile.seek(payload_offset)
                remaining = header["part_size"]
                while remaining > 0:
                    data = infile.read(min(CHUNK_READ_SIZE, remaining))
                    if not data:
                        break
                    outfile.write(data)
                    remaining -= len(data)

            print(f"  Verified + joined part_index {part_index} (from file: {os.path.basename(path)})")

    final_size = os.path.getsize(output_path)
    print(f"\nDone. Restored file size: {human_size(final_size)}")

    if final_size == meta["original_size"]:
        print("Size check: OK")
    else:
        print(f"Size check: MISMATCH (expected {meta['original_size']}, got {final_size})")

    print("Verifying full-file checksum...")
    final_hash = sha256_of_file(output_path)
    if final_hash == meta["original_sha256"]:
        print("Checksum check: OK — restored file is identical to the original.")
    else:
        print("Checksum check: FAILED — restored file does NOT match the original!")


def main():
    parser = argparse.ArgumentParser(description="Split or join large files, tracked by embedded metadata (not filenames).")
    subparsers = parser.add_subparsers(dest="command", required=True)

    split_p = subparsers.add_parser("split", help="Split a file into self-describing parts")
    split_p.add_argument("input_file")
    split_p.add_argument("--size", type=float, default=900, help="Part size in MB (default: 900)")
    split_p.add_argument("--gb", action="store_true", help="Interpret --size as GB")
    split_p.add_argument("--output-dir")

    join_p = subparsers.add_parser("join", help="Rejoin parts, matched by embedded metadata")
    join_p.add_argument("paths", nargs="+")
    join_p.add_argument("--output")
    join_p.add_argument("--file-id")

    list_p = subparsers.add_parser("list", help="List distinct files found among parts")
    list_p.add_argument("paths", nargs="+")

    args = parser.parse_args()

    if args.command == "split":
        multiplier = (1024 ** 3) if args.gb else (1024 ** 2)
        part_size_bytes = int(args.size * multiplier)
        split_file(args.input_file, part_size_bytes, args.output_dir)
    elif args.command == "join":
        join_files(args.paths, args.output, args.file_id)
    elif args.command == "list":
        list_parts(args.paths)


if __name__ == "__main__":
    main()