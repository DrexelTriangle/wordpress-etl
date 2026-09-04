#!/usr/bin/env bash
# Dump the wp-polls tables into Data/ for the poll stage of the pipeline.
#
# Polls are the one part of the legacy site the WordPress exporter does not
# emit: wp-polls keeps its data in its own tables, so there is nothing in
# wp-export.zip to read. This pulls them straight from the WordPress database
# into two TSVs that Utils/WPPolls.py consumes.
#
# Needs an ssh key for the hosts, nothing else -- the database credentials are
# read from wp-config.php on the web host (readable without sudo) and used to
# connect to the database host directly. Nothing is printed.
set -euo pipefail

WEB_HOST=${WP_WEB_HOST:-10.248.40.141}
DB_HOST=${WP_DB_HOST:-10.248.42.122}
SSH_USER=${WP_SSH_USER:-tadmin}
WP_CONFIG=${WP_CONFIG:-/var/www/html/thetriangle.org/wp-config.php}
OUT=${OUT_DIR:-$(cd "$(dirname "$0")/.." && pwd)/Data}

# pollq_timestamp/pollq_expiry are Unix timestamps, so the dates come out
# unambiguous -- no site-timezone guesswork. Tabs and newlines inside answer
# text would break the TSV, so flatten them here rather than in the parser.
Q_SQL='SELECT pollq_id, pollq_timestamp, pollq_expiry, pollq_totalvotes,
              pollq_active,
              REPLACE(REPLACE(pollq_question, CHAR(9), " "), CHAR(10), " ")
       FROM wp_pollsq ORDER BY pollq_id'
A_SQL='SELECT polla_qid, polla_aid, polla_votes,
              REPLACE(REPLACE(polla_answers, CHAR(9), " "), CHAR(10), " ")
       FROM wp_pollsa ORDER BY polla_qid, polla_aid'

if [ -z "${WP_DB_PASSWORD:-}" ]; then
  echo "reading db credentials from $SSH_USER@$WEB_HOST:$WP_CONFIG"
  creds=$(ssh "$SSH_USER@$WEB_HOST" "sed -n \"s/^define(\\s*'DB_\\(USER\\|PASSWORD\\|NAME\\)'\\s*,\\s*'\\(.*\\)'\\s*).*/\\1=\\2/p\" $WP_CONFIG")
  WP_DB_USER=${WP_DB_USER:-$(printf '%s\n' "$creds" | sed -n 's/^USER=//p')}
  WP_DB_PASSWORD=$(printf '%s\n' "$creds" | sed -n 's/^PASSWORD=//p')
  WP_DB_NAME=${WP_DB_NAME:-$(printf '%s\n' "$creds" | sed -n 's/^NAME=//p')}
fi

if [ -z "${WP_DB_USER:-}" ] || [ -z "${WP_DB_PASSWORD:-}" ]; then
  echo "ERROR: no database credentials; set WP_DB_USER and WP_DB_PASSWORD." >&2
  exit 1
fi

mkdir -p "$OUT"
run() { MYSQL_PWD="$WP_DB_PASSWORD" mysql -h "$DB_HOST" -u "$WP_DB_USER" \
          --default-character-set=utf8mb4 -N -B "${WP_DB_NAME:-wordpress}" -e "$1" > "$2"; }

run "$Q_SQL" "$OUT/wp-pollsq.tsv"
run "$A_SQL" "$OUT/wp-pollsa.tsv"

echo "wrote $OUT/wp-pollsq.tsv ($(wc -l < "$OUT/wp-pollsq.tsv") polls)"
echo "wrote $OUT/wp-pollsa.tsv ($(wc -l < "$OUT/wp-pollsa.tsv") options)"
