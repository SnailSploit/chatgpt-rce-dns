# Security Policy

## Responsible Disclosure

This repository contains security research conducted on AI sandbox environments. The research was performed responsibly with the following safeguards:

### Research Methodology

1. **Controlled Environment:** All testing performed on researcher-owned accounts
2. **No Real Data Exfiltration:** DNS exfiltration tested against researcher-controlled infrastructure only
3. **Vendor Notification:** Full report submitted to OpenAI prior to any public disclosure
4. **Minimal Harm:** No attempts to access other users' data or escalate beyond research scope

### Disclosure Timeline

| Date | Action |
|------|--------|
| December 2024 | Research initiated |
| January 2025 | Complete findings submitted to OpenAI |
| January 2025 | OpenAI response: Report dismissed |
| February 2025 | Public disclosure after vendor dismissal |

## Vulnerability Status

### Confirmed Vulnerabilities

| Vulnerability | CWE | CVSS | Vendor Status |
|--------------|-----|------|---------------|
| Python Pickle Deserialization RCE | CWE-502 | 8.1 | Dismissed |
| DNS Exfiltration via Canvas Rendering | CWE-200 | 7.5 | Dismissed |
| Combined Kill Chain | Combined | 9.1 | Dismissed |

### Comparable CVEs

For reference, an identical vulnerability class in a similar context:

- **CVE-2024-50050** (Meta Llama-Stack)
  - Vulnerability: Pickle deserialization RCE
  - CVSS: 9.3 (Snyk)
  - Response: Patched in 11 days
  - Fix: Replaced pickle with JSON

## Reporting Security Issues

If you discover additional vulnerabilities or have concerns about this research:

1. **Email:** Contact via GitHub profile
2. **Do not** create public issues for sensitive security matters
3. **PGP key available** upon request for encrypted communication

## Legal Disclaimer

This research is provided for **educational and defensive purposes only**. 

The techniques documented should only be used:
- In authorized security assessments
- With explicit permission from system owners
- In compliance with all applicable laws

The researcher assumes no liability for:
- Unauthorized use of these techniques
- Any damage resulting from misuse
- Actions taken based on this information

## Use of This Research

You may use this research to:
- ✅ Improve your own AI system's security posture
- ✅ Develop detection mechanisms for similar attacks
- ✅ Educate security teams about AI-specific threats
- ✅ Inform responsible security research

You should NOT use this research to:
- ❌ Attack systems without authorization
- ❌ Exfiltrate data from AI platforms
- ❌ Cause harm to users or organizations
- ❌ Violate terms of service or laws

## Acknowledgments

This research builds upon the work of:
- Oligo Security (CVE-2024-50050 discovery)
- The broader AI security research community
- Open-source security tool developers

---

*"Every serialized object is a potential payload. Every rendered hostname is a potential leak."*
