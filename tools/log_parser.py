#!/usr/bin/env python3
"""
DNS Exfiltration Log Parser - Educational Tool
===============================================

Parses dnsmasq logs to extract and reconstruct exfiltrated data
from DNS subdomain-encoded queries.

Usage:
    python log_parser.py /path/to/dnsmasq.log --zone exfil.lab
    cat dnsmasq.log | python log_parser.py --zone exfil.lab

Part of: Dual Critical Failures Research
Author: Kai Aizen (SnailSploit)
"""

import argparse
import base64
import re
import sys
from collections import defaultdict
from datetime import datetime


def parse_dnsmasq_log(log_content: str, zone: str) -> dict:
    """
    Parse dnsmasq log and extract queries for the specified zone.
    
    Args:
        log_content: Raw log file content
        zone: Target DNS zone to filter
    
    Returns:
        Dictionary mapping timestamps to query data
    """
    # Pattern for dnsmasq query logs
    # Example: Jun 01 12:00:01 dnsmasq[12345]: query[A] p001_db.MFRGGZDFMZTQ.exfil.lab from 127.0.0.1
    pattern = rf'(\w+\s+\d+\s+[\d:]+).*query\[([A-Z]+)\]\s+([^\s]+\.{re.escape(zone)})\s+from\s+([\d.:]+)'
    
    queries = []
    seen_fqdns = set()  # Deduplicate
    
    for line in log_content.split('\n'):
        match = re.search(pattern, line)
        if match:
            timestamp_str, qtype, fqdn, source = match.groups()
            
            # Skip duplicates (browser may query multiple times)
            if fqdn in seen_fqdns:
                continue
            seen_fqdns.add(fqdn)
            
            # Extract subdomain (everything before the zone)
            subdomain = fqdn.replace(f'.{zone}', '')
            
            queries.append({
                'timestamp': timestamp_str,
                'query_type': qtype,
                'fqdn': fqdn,
                'subdomain': subdomain,
                'source': source
            })
    
    return queries


def extract_chunks(queries: list) -> list:
    """
    Extract and sort encoded chunks from query subdomains.
    
    Args:
        queries: List of query dictionaries
    
    Returns:
        Sorted list of (index, chunk) tuples
    """
    chunks = []
    
    for query in queries:
        subdomain = query['subdomain']
        
        # Pattern: p{index}_db.{chunk} or just p{index}.{chunk}
        match = re.match(r'p(\d+)(?:_db)?\.(.+)', subdomain)
        if match:
            index = int(match.group(1))
            chunk = match.group(2)
            chunks.append((index, chunk))
        else:
            # Try without index (single chunk)
            chunks.append((0, subdomain))
    
    # Sort by index
    chunks.sort(key=lambda x: x[0])
    
    return chunks


def decode_payload(chunks: list) -> str:
    """
    Decode Base32-encoded chunks to original data.
    
    Args:
        chunks: Sorted list of (index, chunk) tuples
    
    Returns:
        Decoded string
    """
    # Concatenate chunks
    encoded = ''.join(chunk for _, chunk in chunks)
    
    # Normalize: uppercase, remove any separators
    encoded = encoded.upper().replace('.', '').replace('-', '')
    
    # Add padding if needed (Base32 requires multiples of 8)
    padding_needed = (8 - len(encoded) % 8) % 8
    if padding_needed:
        encoded += '=' * padding_needed
    
    try:
        decoded = base64.b32decode(encoded).decode('utf-8')
        return decoded
    except Exception as e:
        return f"[DECODE ERROR: {e}]"


def print_analysis(queries: list, chunks: list, decoded: str, zone: str):
    """Print formatted analysis report."""
    
    print("=" * 70)
    print("DNS EXFILTRATION ANALYSIS REPORT")
    print("=" * 70)
    print()
    
    print(f"[ZONE]    {zone}")
    print(f"[QUERIES] {len(queries)} unique DNS queries captured")
    print(f"[CHUNKS]  {len(chunks)} payload chunks extracted")
    print()
    
    print("-" * 70)
    print("CAPTURED QUERIES (chronological):")
    print("-" * 70)
    for i, q in enumerate(queries[:20]):  # Limit output
        print(f"  [{q['timestamp']}] {q['query_type']:4s} {q['fqdn']}")
    if len(queries) > 20:
        print(f"  ... and {len(queries) - 20} more queries")
    print()
    
    print("-" * 70)
    print("EXTRACTED CHUNKS (sorted by index):")
    print("-" * 70)
    for idx, chunk in chunks:
        print(f"  [{idx:03d}] {chunk}")
    print()
    
    print("-" * 70)
    print("RECONSTRUCTED PAYLOAD:")
    print("-" * 70)
    print()
    print(f"  {decoded}")
    print()
    
    # If it looks like JSON or structured data, try to pretty print
    if decoded.startswith('{') or decoded.startswith('['):
        try:
            import json
            parsed = json.loads(decoded)
            print("-" * 70)
            print("PARSED JSON:")
            print("-" * 70)
            print(json.dumps(parsed, indent=2))
        except:
            pass
    
    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(
        description='DNS Exfiltration Log Parser',
        epilog='Part of Dual Critical Failures Research by SnailSploit'
    )
    
    parser.add_argument('logfile', nargs='?', help='Path to dnsmasq log file (or stdin)')
    parser.add_argument('--zone', '-z', default='exfil.lab', help='DNS zone to filter (default: exfil.lab)')
    parser.add_argument('--raw', '-r', action='store_true', help='Output raw decoded data only')
    
    args = parser.parse_args()
    
    # Read log content
    if args.logfile:
        with open(args.logfile, 'r') as f:
            log_content = f.read()
    elif not sys.stdin.isatty():
        log_content = sys.stdin.read()
    else:
        parser.print_help()
        print("\nError: Provide a log file or pipe data via stdin")
        sys.exit(1)
    
    # Parse
    queries = parse_dnsmasq_log(log_content, args.zone)
    
    if not queries:
        print(f"No queries found for zone: {args.zone}")
        sys.exit(1)
    
    # Extract chunks
    chunks = extract_chunks(queries)
    
    # Decode
    decoded = decode_payload(chunks)
    
    # Output
    if args.raw:
        print(decoded)
    else:
        print_analysis(queries, chunks, decoded, args.zone)


if __name__ == '__main__':
    main()
