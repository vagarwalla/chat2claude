# chat2claude

Converts your chat therapy conversations into uploadable chunks to start a Claude project!

## Therapy Conversation Processing Workflow

Automated script to process ChatGPT conversation exports: automatically identifies therapy conversations, cleans and minifies them, then splits into upload-ready chunks.

## What You Need

1. **Python 3.7 or higher** installed on your computer
   - Check if you have Python: Open Command Prompt (Windows) or Terminal (Mac) and type `python --version`
   - If you don't have Python, download it from [python.org](https://www.python.org/downloads/)

2. **Your ChatGPT conversations file** (`conversations.json`)
   - Export your conversations from ChatGPT
   - Save it as `conversations.json` in the same folder as the script

3. **The script file**: `process_therapy_conversations.py`

## How to Use

### Option 1: Simple Method (Recommended)

1. Place `conversations.json` in the same folder as `process_therapy_conversations.py`
2. Double-click `process_therapy_conversations.py` (or right-click → "Open with Python")

### Option 2: Command Line Method

1. Open Command Prompt (Windows) or Terminal (Mac)
2. Navigate to the folder containing the script:
   ```
   cd path/to/folder
   ```
3. Run the script:
   ```
   python process_therapy_conversations.py
   ```
   
   Or if that doesn't work, try:
   ```
   python3 process_therapy_conversations.py
   ```

### Option 3: With Custom File Path

If your conversations file is in a different location:
```
python process_therapy_conversations.py path/to/your/conversations.json
```

## What the Script Does

1. **Identifies therapy conversations** automatically by finding the marker
2. **Filters** to extract only therapy conversations
3. **Cleans** the data (removes metadata, extracts messages)
4. **Minifies** using multiple techniques:
   - Converts to positional arrays
   - Normalizes whitespace
   - Removes JSON formatting
5. **Splits into chunks** of ~25,000 tokens each
6. **Creates output folder** with ready-to-upload files

## Output

The script creates a `test` folder containing:

- **Intermediate files** (for debugging if needed):
  - `therapy_conversations.json` - Filtered conversations
  - `therapy_conversations_cleaned.json` - Cleaned data
  - `therapy_conversations_final.json` - Final minified version

- **Upload folder**: `test/Upload these files/`
  - Contains chunked JSON files: `therapy_chunk_001.json`, `therapy_chunk_002.json`, etc.
  - These are ready to upload!

## Expected Results

- **Size reduction**: Typically 90-99% reduction from original file
- **Chunk files**: Automatically split into manageable sizes (~25,000 tokens each)
- **Format**: Messages use compact positional arrays: `["u", "message"]` or `["a", "message"]`

## Troubleshooting

### "File not found" error
- Make sure `conversations.json` is in the same folder as the script
- Or provide the full path: `python process_therapy_conversations.py "C:\path\to\conversations.json"`

### "Python is not recognized"
- Python is not installed or not in your PATH
- Install Python from [python.org](https://www.python.org/downloads/)
- Make sure to check "Add Python to PATH" during installation

### "No conversations found"
- The script couldn't identify therapy conversations automatically
- Check that your conversations file contains therapy-related conversations
- The script looks for patterns in `gizmo_id` or `conversation_template_id` fields

### Script runs but no output folder
- Check the console output for error messages
- The `test` folder should be created automatically
- If it fails, check that you have write permissions in the folder

## Example Output

```
============================================================
THERAPY CONVERSATION PROCESSING WORKFLOW
============================================================

Output directory: C:\Users\YourName\Downloads\test

Input file: conversations.json
Original size: 136,541,436 bytes (~34,135,359 tokens)

=== STEP 1: Identifying Therapy Marker ===
  ✓ Marker identified: gizmo_id = g-p-...

=== STEP 2: Filtering Therapy Conversations ===
  ✓ Saved 142 conversations

=== STEP 3: Cleaning Conversations ===
  ✓ Cleaning complete
  Size: 52,336,838 → 1,883,076 chars (96.40% reduction)

=== STEP 4: Applying Minification Techniques ===
  ✓ Minification complete

=== STEP 5: Splitting into Chunks ===
  ✓ Created 21 chunk files

============================================================
WORKFLOW COMPLETE!
============================================================
✓ Processed 142 conversations
✓ Size reduction: 98.68%
✓ Excellent! Achieved 98.68% reduction (target: ≥90%)
```

## Files to Share

To share this with a friend, give them:

1. **`process_therapy_conversations.py`** - The main script
2. **This README.md** - Instructions (optional, but helpful)

That's it! The script uses only Python's standard library, so no additional packages are needed.

## Notes

- The script automatically creates a `test` folder for all outputs
- Original file is never modified
- All intermediate files are saved for debugging if needed
- Chunk files are ready to upload immediately
