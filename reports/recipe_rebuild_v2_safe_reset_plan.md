# Recipe Rebuild V2 — Safe Reset Plan

- Generated: 2026-06-10T13:14:40.579965+00:00
- Mode: **dry-run**
- Backup id: `none`

- Error: `(psycopg2.OperationalError) connection to server at "localhost" (::1), port 5432 failed: Permission denied (0x0000271D/10013)
	Is the server running on that host and accepting TCP/IP connections?
connection to server at "localhost" (127.0.0.1), port 5432 failed: Connection refused (0x0000274D/10061)
	Is the server running on that host and accepting TCP/IP connections?

(Background on this error at: https://sqlalche.me/e/20/e3q8)`


## Apply requirements

- `--apply` requires `--backup-id` pointing to `backups/recipe_rebuild_v2/<id>/manifest.md`
- Stage 1: dry-run only unless explicitly approved.