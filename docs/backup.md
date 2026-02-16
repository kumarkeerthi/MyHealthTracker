# Backup and Restore

## Scripts
- `backup.sh`: dumps PostgreSQL + archives uploads + compresses + optional S3 upload.
- `restore.sh`: restores DB dump and upload directory from an archive.
- `setup_backup_cron.sh`: installs daily cron automation.

## Example backup
```bash
S3_URI=s3://my-backups/myhealthtracker ./backup.sh
```

## Example restore
```bash
./restore.sh ./backups/myhealthtracker_backup_YYYYMMDD_HHMMSS.tar.gz
```

## Cron installation
```bash
CRON_SCHEDULE="0 2 * * *" ./setup_backup_cron.sh
```
