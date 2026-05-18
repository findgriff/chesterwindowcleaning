# chesterwindowcleaner.co.uk

Static-HTML marketing site + Python-stdlib lead-capture backend + lightweight CRM for a solo-trader window-cleaning business in Chester.

See `docs/superpowers/specs/` for the design spec and `docs/superpowers/plans/` for the implementation plan.

## Local development

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
pytest backend/tests/ -v
python3 -m backend.app   # serves http://127.0.0.1:8094
```

## Deploy

```bash
make deploy-site
make deploy-backend
make logs
```
