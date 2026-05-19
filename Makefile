.PHONY: deploy-site deploy-backend logs backup-pull tail-db test

test:
	. .venv/bin/activate && pytest backend/tests/ -v

deploy-site:
	bash infra/scripts/deploy-site.sh

deploy-backend:
	bash infra/scripts/deploy-backend.sh

logs:
	ssh dev 'journalctl -u chesterwc-backend -f'

backup-pull:
	mkdir -p backups
	scp dev:/var/backups/chesterwc/db-$$(date -u +%Y-%m-%d).sqlite.gz backups/

tail-db:
	ssh -t dev 'sqlite3 /var/lib/chesterwc/app.db'
