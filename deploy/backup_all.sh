#!/bin/sh
set -eu
"$(dirname "$0")/backup_database.sh"
"$(dirname "$0")/backup_media.sh"
