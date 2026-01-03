"""
Automated workflow to process ChatGPT conversation files:
1. Automatically identify therapy marker
2. Extract therapy conversations
3. Clean and minify using all techniques
4. Chunk and organize output files
"""

import json
import sys
import os
import re
from datetime import datetime
from collections import Counter

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


# ============================================================================
# MARKER IDENTIFICATION
# ============================================================================

def identify_marker_pattern(conversations):
    """
    Identify therapy marker using pattern analysis.
    Returns the most common gizmo_id or template_id.
    """
    gizmo_ids = []
    template_ids = []
    
    for conv in conversations:
        gizmo_id = conv.get('gizmo_id', '')
        template_id = conv.get('conversation_template_id', '')
        
        if gizmo_id and gizmo_id.startswith('g-p-'):
            gizmo_ids.append(gizmo_id)
        if template_id and template_id.startswith('g-p-'):
            template_ids.append(template_id)
    
    # Count occurrences
    gizmo_counter = Counter(gizmo_ids)
    template_counter = Counter(template_ids)
    
    # Find most common
    most_common_gizmo = gizmo_counter.most_common(1)
    most_common_template = template_counter.most_common(1)
    
    candidates = []
    if most_common_gizmo:
        candidates.append(('gizmo_id', most_common_gizmo[0][0], most_common_gizmo[0][1]))
    if most_common_template:
        candidates.append(('template_id', most_common_template[0][0], most_common_template[0][1]))
    
    if not candidates:
        return None, None
    
    # Sort by count (descending)
    candidates.sort(key=lambda x: x[2], reverse=True)
    
    marker_type, marker_value, count = candidates[0]
    
    print(f"  Found {len(gizmo_ids)} gizmo_ids and {len(template_ids)} template_ids")
    print(f"  Most common: {marker_type} = {marker_value} ({count} occurrences)")
    
    return marker_type, marker_value


def identify_marker_llm(conversations):
    """
    Fallback: Use LLM to identify therapy marker.
    This is a placeholder - implement with OpenAI/Anthropic API if needed.
    """
    # Sample a few conversations for analysis
    sample_size = min(5, len(conversations))
    samples = conversations[:sample_size]
    
    # Extract titles and first messages for context
    context = []
    for conv in samples:
        title = conv.get('title', '')
        gizmo_id = conv.get('gizmo_id', '')
        template_id = conv.get('conversation_template_id', '')
        context.append({
            'title': title,
            'gizmo_id': gizmo_id,
            'template_id': template_id
        })
    
    # TODO: Implement LLM API call here
    # For now, return None to fall back to pattern analysis
    print("  LLM identification not implemented - using pattern analysis")
    return None, None


def identify_marker(conversations):
    """
    Automatically identify the therapy marker.
    Tries pattern analysis first, then LLM if needed.
    """
    print("\n=== STEP 1: Identifying Therapy Marker ===")
    
    if not conversations:
        print("  Error: No conversations to analyze")
        return None, None
    
    # Try pattern analysis first
    marker_type, marker_value = identify_marker_pattern(conversations)
    
    if marker_type and marker_value:
        print(f"  ✓ Marker identified: {marker_type} = {marker_value}")
        return marker_type, marker_value
    
    # Fallback to LLM if pattern analysis fails
    print("  Pattern analysis failed - trying LLM...")
    marker_type, marker_value = identify_marker_llm(conversations)
    
    if marker_type and marker_value:
        print(f"  ✓ Marker identified via LLM: {marker_type} = {marker_value}")
        return marker_type, marker_value
    
    print("  ✗ Could not identify marker automatically")
    return None, None


# ============================================================================
# FILTERING
# ============================================================================

def filter_conversations(input_file, marker_type, marker_value, output_file):
    """
    Filter conversations by the identified marker.
    """
    print(f"\n=== STEP 2: Filtering Therapy Conversations ===")
    print(f"Reading {input_file}...")
    
    with open(input_file, 'r', encoding='utf-8') as f:
        all_conversations = json.load(f)
    
    total_count = len(all_conversations)
    print(f"Total conversations loaded: {total_count}")
    
    if not marker_type or not marker_value:
        print("  ✗ Error: No marker provided for filtering")
        return []
    
    # Filter conversations
    therapy_conversations = []
    for conv in all_conversations:
        if marker_type == 'gizmo_id':
            if conv.get('gizmo_id') == marker_value:
                therapy_conversations.append(conv)
        elif marker_type == 'template_id':
            if conv.get('conversation_template_id') == marker_value:
                therapy_conversations.append(conv)
        else:
            # Check both
            if conv.get('gizmo_id') == marker_value or conv.get('conversation_template_id') == marker_value:
                therapy_conversations.append(conv)
    
    filtered_count = len(therapy_conversations)
    print(f"Found {filtered_count} therapy conversations")
    
    if filtered_count == 0:
        print("  ✗ Error: No conversations found matching the marker")
        print("  Please check that the marker is correct or that the file contains therapy conversations.")
        return []
    
    # Save filtered conversations
    print(f"Saving filtered conversations to {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(therapy_conversations, f, ensure_ascii=False, indent=2)
    
    print(f"  ✓ Saved {filtered_count} conversations")
    return therapy_conversations


# ============================================================================
# CLEANING (from clean_therapy_conversations.py)
# ============================================================================

def extract_messages_from_mapping(mapping, root_node_id=None):
    """Traverse the mapping structure to extract actual conversation messages."""
    if not mapping:
        return []
    
    # Find root node if not provided
    if root_node_id is None:
        for node_id, node in mapping.items():
            if node.get('parent') is None:
                root_node_id = node_id
                break
    
    if root_node_id is None:
        return []
    
    messages = []
    visited = set()
    
    def traverse(node_id):
        if node_id in visited or node_id not in mapping:
            return
        
        visited.add(node_id)
        node = mapping[node_id]
        msg = node.get('message')
        
        if msg:
            author = msg.get('author', {})
            role = author.get('role')
            content = msg.get('content', {})
            metadata = msg.get('metadata', {})
            
            # Skip hidden messages
            if metadata.get('is_visually_hidden_from_conversation'):
                for child_id in node.get('children', []):
                    traverse(child_id)
                return
            
            # Skip tool messages
            if role == 'tool':
                for child_id in node.get('children', []):
                    traverse(child_id)
                return
            
            # Skip system messages with empty content
            if role == 'system':
                parts = content.get('parts', [])
                first_part = parts[0] if parts else None
                if not first_part or (isinstance(first_part, str) and first_part.strip() == ''):
                    for child_id in node.get('children', []):
                        traverse(child_id)
                    return
            
            # Skip user profile/instruction messages
            if 'user_profile' in content or 'user_instructions' in content:
                for child_id in node.get('children', []):
                    traverse(child_id)
                return
            
            # Skip empty content messages
            parts = content.get('parts', [])
            if not parts:
                for child_id in node.get('children', []):
                    traverse(child_id)
                return
            
            first_part = parts[0]
            if not first_part or (isinstance(first_part, str) and first_part.strip() == ''):
                for child_id in node.get('children', []):
                    traverse(child_id)
                return
            
            # Only keep user and assistant messages with actual content
            if role in ['user', 'assistant']:
                content_text = first_part if isinstance(first_part, str) else str(first_part)
                if content_text.strip():
                    messages.append({
                        'r': 'u' if role == 'user' else 'a',
                        'c': content_text.strip()
                    })
        
        # Traverse children
        for child_id in node.get('children', []):
            traverse(child_id)
    
    traverse(root_node_id)
    return messages


def clean_conversation(conv):
    """Clean a single conversation, keeping only essential data."""
    # Extract date from create_time
    create_time = conv.get('create_time')
    if create_time:
        date_str = datetime.fromtimestamp(create_time).strftime('%Y-%m-%d')
    else:
        date_str = None
    
    # Extract title
    title = conv.get('title', '')
    
    # Extract messages from mapping
    mapping = conv.get('mapping', {})
    messages = extract_messages_from_mapping(mapping)
    
    # Build cleaned structure
    cleaned = {
        'd': date_str,
        'tt': title,
        'm': messages
    }
    
    # Remove None/empty values
    if cleaned['d'] is None:
        del cleaned['d']
    if not cleaned.get('tt'):
        del cleaned['tt']
    
    return cleaned


def clean_conversations(input_file, output_file):
    """Clean the therapy conversations JSON file."""
    print(f"\n=== STEP 3: Cleaning Conversations ===")
    print(f"Reading {input_file}...")
    
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"Processing {len(data)} conversations...")
    
    cleaned_data = []
    for i, conv in enumerate(data):
        if (i + 1) % 10 == 0:
            print(f"  Processed {i + 1}/{len(data)} conversations...")
        
        cleaned = clean_conversation(conv)
        cleaned_data.append(cleaned)
    
    print(f"Writing cleaned data to {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(cleaned_data, f, ensure_ascii=False, separators=(',', ':'))
    
    # Calculate size reduction
    original_size = len(json.dumps(data, ensure_ascii=False))
    cleaned_size = len(json.dumps(cleaned_data, ensure_ascii=False))
    reduction = original_size - cleaned_size
    reduction_pct = (reduction / original_size) * 100 if original_size > 0 else 0
    
    print(f"  ✓ Cleaning complete")
    print(f"  Size: {original_size:,} → {cleaned_size:,} chars ({reduction_pct:.2f}% reduction)")
    
    return cleaned_data, cleaned_size


# ============================================================================
# MINIFICATION TECHNIQUES
# ============================================================================

def apply_positional_arrays(data):
    """Convert messages from objects to positional arrays."""
    converted_data = []
    for conv in data:
        converted_conv = {}
        if 'd' in conv:
            converted_conv['d'] = conv['d']
        if 'tt' in conv:
            converted_conv['tt'] = conv['tt']
        
        # Convert messages to positional arrays
        if 'm' in conv:
            converted_conv['m'] = [[msg['r'], msg['c']] for msg in conv['m']]
        
        converted_data.append(converted_conv)
    
    return converted_data


def normalize_whitespace(data):
    """Normalize whitespace in message content."""
    for conv in data:
        if 'm' in conv:
            for msg in conv['m']:
                if isinstance(msg, list) and len(msg) >= 2:
                    content = msg[1]  # Content is at index 1
                    if isinstance(content, str):
                        # Collapse multiple spaces to single space
                        content = re.sub(r' {2,}', ' ', content)
                        # Collapse multiple newlines to single newline
                        content = re.sub(r'\n{2,}', '\n', content)
                        # Remove leading/trailing whitespace from each line
                        lines = content.split('\n')
                        content = '\n'.join(line.strip() for line in lines)
                        msg[1] = content
    
    return data


def minify_json_data(data):
    """Minify JSON by removing all whitespace."""
    return json.dumps(data, ensure_ascii=False, separators=(',', ':'))


def apply_minification_techniques(input_file, output_file):
    """Apply all minification techniques in sequence."""
    print(f"\n=== STEP 4: Applying Minification Techniques ===")
    
    # Read cleaned data
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    original_size = len(json.dumps(data, ensure_ascii=False, separators=(',', ':')))
    
    # Step 4a: Positional Arrays
    print("  4a. Converting to positional arrays...")
    data = apply_positional_arrays(data)
    size_after_positional = len(json.dumps(data, ensure_ascii=False, separators=(',', ':')))
    reduction = original_size - size_after_positional
    reduction_pct = (reduction / original_size) * 100 if original_size > 0 else 0
    print(f"     Size: {original_size:,} → {size_after_positional:,} chars ({reduction_pct:.2f}% reduction)")
    
    # Step 4b: Normalize Whitespace
    print("  4b. Normalizing whitespace in content...")
    data = normalize_whitespace(data)
    size_after_whitespace = len(json.dumps(data, ensure_ascii=False, separators=(',', ':')))
    reduction = size_after_positional - size_after_whitespace
    reduction_pct = (reduction / size_after_positional) * 100 if size_after_positional > 0 else 0
    print(f"     Size: {size_after_positional:,} → {size_after_whitespace:,} chars ({reduction_pct:.2f}% reduction)")
    
    # Step 4c: Minify JSON (already minified, but ensure it's written correctly)
    print("  4c. Writing minified JSON...")
    minified_json_str = minify_json_data(data)
    final_size = len(minified_json_str)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(minified_json_str)
    
    print(f"  ✓ Minification complete")
    print(f"  Final size: {final_size:,} chars (~{final_size // 4:,} tokens)")
    
    return data, final_size


# ============================================================================
# CHUNKING
# ============================================================================

def split_into_chunks(data, tokens_per_chunk=25000, output_dir='Upload these files', output_prefix='therapy_chunk'):
    """Split JSON data into chunks and save to output directory."""
    print(f"\n=== STEP 5: Splitting into Chunks ===")
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    total_size = len(json.dumps(data, ensure_ascii=False, separators=(',', ':')))
    total_tokens = total_size // 4
    print(f"Total size: {total_size:,} chars (~{total_tokens:,} tokens)")
    print(f"Target chunk size: ~{tokens_per_chunk:,} tokens")
    
    # Calculate how many chunks we'll need
    estimated_chunks = (total_tokens + tokens_per_chunk - 1) // tokens_per_chunk
    print(f"Estimated chunks: {estimated_chunks}")
    
    # Split conversations into chunks
    chunks = []
    current_chunk = []
    current_size = 0
    
    for conv in data:
        conv_json = json.dumps(conv, ensure_ascii=False, separators=(',', ':'))
        conv_size = len(conv_json)
        conv_tokens = conv_size // 4
        
        # Check if adding this conversation would exceed the limit
        if current_size + conv_tokens > tokens_per_chunk and current_chunk:
            # Save current chunk
            chunks.append(current_chunk)
            current_chunk = [conv]
            current_size = conv_tokens
        else:
            current_chunk.append(conv)
            current_size += conv_tokens
    
    # Add final chunk
    if current_chunk:
        chunks.append(current_chunk)
    
    # Write chunks to files in output directory
    print(f"Writing {len(chunks)} chunks to {output_dir}/...")
    chunk_files = []
    for i, chunk in enumerate(chunks, 1):
        chunk_size = len(json.dumps(chunk, ensure_ascii=False, separators=(',', ':')))
        chunk_tokens = chunk_size // 4
        filename = os.path.join(output_dir, f"{output_prefix}_{i:03d}.json")
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(chunk, f, ensure_ascii=False, separators=(',', ':'))
        
        chunk_files.append(filename)
        print(f"  Chunk {i}: {len(chunk)} conversations, {chunk_size:,} chars (~{chunk_tokens:,} tokens)")
    
    print(f"  ✓ Created {len(chunks)} chunk files in '{output_dir}' directory")
    
    return chunk_files


# ============================================================================
# MAIN WORKFLOW
# ============================================================================

def main():
    """Main workflow orchestration."""
    print("=" * 60)
    print("THERAPY CONVERSATION PROCESSING WORKFLOW")
    print("=" * 60)
    
    # Determine input file
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    else:
        input_file = 'conversations.json'
    
    # Check if file exists
    if not os.path.exists(input_file):
        print(f"\n✗ Error: File not found: {input_file}")
        print(f"  Please make sure the file exists in the current directory,")
        print(f"  or provide the path as an argument:")
        print(f"    python process_therapy_conversations.py path/to/conversations.json")
        sys.exit(1)
    
    # Create test folder for all outputs
    test_dir = 'test'
    os.makedirs(test_dir, exist_ok=True)
    print(f"\nOutput directory: {os.path.abspath(test_dir)}")
    
    # Track original size
    original_size = os.path.getsize(input_file)
    print(f"\nInput file: {input_file}")
    print(f"Original size: {original_size:,} bytes (~{original_size // 4:,} tokens)")
    
    try:
        # Step 1: Identify marker
        with open(input_file, 'r', encoding='utf-8') as f:
            all_conversations = json.load(f)
        
        marker_type, marker_value = identify_marker(all_conversations)
        
        if not marker_type or not marker_value:
            print("\n✗ Error: Could not identify therapy marker")
            print("  Please check that the file contains therapy conversations,")
            print("  or manually specify the marker in the script.")
            sys.exit(1)
        
        # Step 2: Filter conversations
        filtered_file = os.path.join(test_dir, 'therapy_conversations.json')
        therapy_conversations = filter_conversations(input_file, marker_type, marker_value, filtered_file)
        
        if not therapy_conversations:
            sys.exit(1)
        
        # Track size after filtering
        filtered_size = os.path.getsize(filtered_file)
        
        # Step 3: Clean conversations
        cleaned_file = os.path.join(test_dir, 'therapy_conversations_cleaned.json')
        cleaned_data, cleaned_size = clean_conversations(filtered_file, cleaned_file)
        
        # Step 4: Apply minification
        minified_file = os.path.join(test_dir, 'therapy_conversations_final.json')
        final_data, final_size = apply_minification_techniques(cleaned_file, minified_file)
        
        # Step 5: Calculate overall reduction
        print(f"\n=== SIZE REDUCTION SUMMARY ===")
        reduction_from_original = original_size - final_size
        reduction_pct = (reduction_from_original / original_size) * 100 if original_size > 0 else 0
        
        print(f"Original size:     {original_size:,} chars (~{original_size // 4:,} tokens)")
        print(f"After filtering:   {filtered_size:,} chars (~{filtered_size // 4:,} tokens)")
        print(f"After cleaning:   {cleaned_size:,} chars (~{cleaned_size // 4:,} tokens)")
        print(f"Final size:       {final_size:,} chars (~{final_size // 4:,} tokens)")
        print(f"\nTotal reduction:   {reduction_from_original:,} chars (~{reduction_from_original // 4:,} tokens)")
        print(f"Reduction:        {reduction_pct:.2f}%")
        
        # Step 6: Chunking
        output_dir = os.path.join(test_dir, 'Upload these files')
        chunk_files = split_into_chunks(final_data, tokens_per_chunk=25000, output_dir=output_dir)
        
        # Final summary
        print(f"\n" + "=" * 60)
        print("WORKFLOW COMPLETE!")
        print("=" * 60)
        print(f"✓ Processed {len(therapy_conversations)} conversations")
        print(f"✓ Size reduction: {reduction_pct:.2f}%")
        
        if reduction_pct >= 90:
            print(f"✓ Excellent! Achieved {reduction_pct:.2f}% reduction (target: ≥90%)")
        else:
            print(f"⚠ Warning: Only achieved {reduction_pct:.2f}% reduction (target: ≥90%)")
            print(f"  Chunks still created, but compression may not be optimal.")
        
        print(f"\n✓ Created {len(chunk_files)} chunk files in '{output_dir}' directory")
        print(f"  Files are ready to upload!")
        print(f"\nOutput location: {os.path.abspath(output_dir)}")
        
    except FileNotFoundError as e:
        print(f"\n✗ Error: File not found: {e}")
        print("  Please check that the file path is correct.")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"\n✗ Error: Invalid JSON in {input_file}")
        print(f"  Details: {e}")
        print("  Please check that the file is valid JSON.")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
