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
