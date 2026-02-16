# Backup and Restore Operations Guide

This guide covers backup creation, verification, restore drills, and cron automation.

## Scripts

- `backup.sh`
  - Dumps PostgreSQL data.
  - Archives uploaded assets.
  - Compresses output into timestamped backup artifacts.
  - Optionally uploads artifacts to S3 when `S3_URI` is provided.
- `restore.sh`
  - Restores database dump and uploaded assets from a selected backup archive.
- `setup_backup_cron.sh`
  - Registers scheduled backup execution through cron.

## Backup strategy recommendations

- **Daily automated backups** minimum.
- **Pre-change backups** before migrations or production updates.
- **Offsite copies** (S3/object storage) for disaster recovery.
- **Retention policy** (e.g., daily for 14 days, weekly for 8 weeks, monthly for 6 months).

## Example commands

### Local + optional S3 backup

```bash
S3_URI=s3://my-backups/myhealthtracker ./backup.sh
```

### Restore from archive

```bash
./restore.sh ./backups/myhealthtracker_backup_YYYYMMDD_HHMMSS.tar.gz
```

### Install daily cron at 02:00

```bash
CRON_SCHEDULE="0 2 * * *" ./setup_backup_cron.sh
```

## Verification checklist

After each backup:

1. Confirm archive exists and size is non-trivial.
2. Validate DB dump file is present in archive.
3. Confirm uploads directory snapshot exists.
4. If using S3, verify object uploaded and checksum/size match.

After each restore test:

1. Start stack and run `GET /health`.
2. Validate representative user data is present.
3. Confirm uploaded image assets are accessible.
4. Review logs for migration or integrity errors.

## Restore drill practice

Run restore drills at least monthly in staging:
- Use newest backup.
- Time the full RTO path (download + restore + validation).
- Record issues and improve runbook steps.

## Common pitfalls

- Running restore against the wrong environment.
- Missing `.env` credentials during restore.
- Assuming backup success without verification.
- Retaining only local backups on the same host.
