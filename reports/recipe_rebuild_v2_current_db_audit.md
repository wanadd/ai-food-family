# Recipe Rebuild V2 Audit

DB unavailable locally: `(psycopg2.OperationalError) connection to server at "localhost" (::1), port 5432 failed: Permission denied (0x0000271D/10013)
	Is the server running on that host and accepting TCP/IP connections?
connection to server at "localhost" (127.0.0.1), port 5432 failed: Connection refused (0x0000274D/10061)
	Is the server running on that host and accepting TCP/IP connections?

(Background on this error at: https://sqlalche.me/e/20/e3q8)`

Run on VPS:
```bash
python backend/scripts/audit_recipe_rebuild_v2.py
```
