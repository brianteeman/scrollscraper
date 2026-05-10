# EC2 Deployment Guide

This document covers deploying ScrollScraper via docker-compose on the existing EC2,
replacing the current fastcgi-wrapper setup. nginx remains on the host for TLS
termination; the application runs inside a Docker container.

## Prerequisites

- Docker and docker-compose installed (docker-compose was installed at `/usr/local/bin/docker-compose`)
- The Docker image built on the EC2 (see below)
- The MP3 files already present on the host

## 1. Clone / update the repo on the EC2

```bash
cd /newvolume/dockerWork122023/checkout/scrollscraper
git pull
```

## 2. Build the Docker image

```bash
docker build -t scrollscraper .
```

The first build takes 10–15 minutes. Subsequent rebuilds are faster due to layer caching.

## 3. Create the state directory

```bash
mkdir -p /var/opt/scrollscraper-state/smil
touch /var/opt/scrollscraper-state/smil/daystampAndLock.txt
```

## 4. Configure the environment

```bash
cp .env.example .env
```

Edit `.env` and set both variables for production:

```
MP3_DIR=/srv/www/scrollscraper.adatshalom.net/public_html/ORT_MP3s.recoded
STATE_DIR=/var/opt/scrollscraper-state
```

## 5. Start the container

```bash
docker-compose up -d
```

Verify it is running:

```bash
docker-compose ps
curl -s http://127.0.0.1:8080/cgi-bin/scrollscraper.cgi \
  "book=2&startc=15&startv=27&endc=15&endv=27" | head -5
```

## 6. Update the nginx config

Back up the existing config, install the new one, test, and reload:

```bash
cp /etc/nginx/conf.d/scrollscraper.conf \
   /etc/nginx/conf.d/scrollscraper.conf.pre-docker

cp deploy/nginx-scrollscraper.conf /etc/nginx/conf.d/scrollscraper.conf

nginx -t && service nginx reload
```

The site should now be live. Test in a browser:
`https://scrollscraper.adatshalom.net/scrollscraper.cgi?book=2&startc=15&startv=27&endc=15&endv=27`

## 7. Stop the old fastcgi-wrapper

Once the Docker-based site is confirmed working:

```bash
kill $(pgrep -f fastcgi-wrapper) && \
  chkconfig fastcgi-wrapper off 2>/dev/null || true
```

## 8. Fix the certbot cron

The existing cron runs certbot 60 times on the 1st of each month due to a
wildcard minute field. Fix it:

```bash
crontab -e   # or edit /etc/cron.d/certbot directly
```

Change:
```
* 3 1 * * root certbot-auto --nginx --force-renewal renew --post-hook="service nginx reload"
```
To:
```
0 3 1 * * root certbot-auto --nginx renew --post-hook="service nginx reload"
```

(Removed `--force-renewal` so renewal only happens when the cert is near expiry,
and fixed the minute field from `*` to `0`.)

## Rollback

If anything goes wrong, restore the previous nginx config and the fastcgi-wrapper:

```bash
cp /etc/nginx/conf.d/scrollscraper.conf.pre-docker \
   /etc/nginx/conf.d/scrollscraper.conf
nginx -t && service nginx reload
# restart fastcgi-wrapper if needed
/usr/bin/perl /usr/bin/fastcgi-wrapper.pl &
```
