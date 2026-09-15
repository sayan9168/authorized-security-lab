# Authorized Security Lab

Enterprise-grade security assessment and adversarial emulation core for explicitly authorized environments.

This repository intentionally excludes weaponized payload delivery, arbitrary remote command execution, credential theft, persistence, and exploit automation. The core focuses on safe assessment orchestration, bounded network auditing, session metadata, module lifecycle, and auditable results.

## Quick start

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python -m aslab
```

Only scan assets you own or have explicit permission to assess.
