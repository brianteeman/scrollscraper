# EC2 Deployment Guide

Deploys ScrollScraper via docker-compose on the existing EC2, replacing the
fastcgi-wrapper setup. nginx stays on the host for TLS/LetsEncrypt; the app
runs in a Docker container on `127.0.0.1:8080`.

**Do this in one sitting.** The nginx switch takes under a second and is
instantly reversible, but don't leave things half-done between phases.

---

## Prerequisites

### One-time: give ec2-user Docker access

Running as `ec2-user`, you will get "permission denied" on the Docker socket
unless you add yourself to the `docker` group:

```bash
sudo usermod -aG docker ec2-user
newgrp docker          # activates the group in the current session without re-logging-in
```

### One-time: clone the repo

```bash
mkdir -p /home/ec2-user/Development/checkouts
cd /home/ec2-user/Development/checkouts
git clone https://github.com/jae-63/scrollscraper.git
cd scrollscraper
```

---

## Phase 1 — Build and test (zero user impact)

The live site is completely untouched during this entire phase.

### 1. Build the Docker image

```bash
docker build -t scrollscraper .
```

First build takes ~15 minutes. Subsequent rebuilds are much faster (layer cache).

### 2. Create persistent host directories

```bash
# Rate-limiting state + generated MP3 cache
mkdir -p /var/opt/scrollscraper-state/smil
touch /var/opt/scrollscraper-state/smil/daystampAndLock.txt

# buildmp3.cgi shell-script working directory
mkdir -p /var/opt/scrollscraper-workdir
```

### 3. Configure the environment

```bash
cp .env.example .env
```

Edit `.env` and set all three variables:

```
MP3_DIR=/srv/www/scrollscraper.adatshalom.net/public_html/ORT_MP3s.recoded
STATE_DIR=/var/opt/scrollscraper-state
WORK_DIR=/var/opt/scrollscraper-workdir
```

### 4. Start the container

```bash
docker-compose up -d
docker-compose ps      # should show status "running"
```

### 5. Test on port 8080 — before touching nginx

```bash
curl -s "http://127.0.0.1:8080/cgi-bin/scrollscraper.cgi?book=2&startc=15&startv=27&endc=15&endv=27" \
  | grep -i "title\|error"
```

Expected output contains: `<title>Exodus ...`

**If this fails, stop here and debug.** The live site is still running normally
via fastcgi-wrapper. Do not proceed to Phase 2 until this test passes.

---

## Phase 2 — The nginx switch (~30 seconds of risk)

Only proceed once the Phase 1 test passes.

### 6. Back up the current nginx config

```bash
sudo cp /etc/nginx/conf.d/scrollscraper.conf \
        /etc/nginx/conf.d/scrollscraper.conf.pre-docker
```

### 7. Install the new nginx config

```bash
sudo cp deploy/nginx-scrollscraper.conf /etc/nginx/conf.d/scrollscraper.conf
```

### 8. Validate — must pass before reloading

```bash
sudo nginx -t
```

If this does **not** say `syntax is ok`, restore and stop:

```bash
sudo cp /etc/nginx/conf.d/scrollscraper.conf.pre-docker \
        /etc/nginx/conf.d/scrollscraper.conf
```

### 9. Reload nginx

```bash
sudo service nginx reload
```

This is graceful — in-flight requests finish before the config switches.

### 10. Verify in your browser

Open:
```
https://scrollscraper.adatshalom.net/scrollscraper.cgi?book=2&startc=15&startv=27&endc=15&endv=27
```

You should see the Torah display for Exodus 15:27.

---

## Rollback

If anything looks wrong after the nginx reload, one command restores the previous
setup. The fastcgi-wrapper process is never stopped during deployment, so rollback
is immediate:

```bash
sudo cp /etc/nginx/conf.d/scrollscraper.conf.pre-docker \
        /etc/nginx/conf.d/scrollscraper.conf \
  && sudo nginx -t \
  && sudo service nginx reload
```

Verify fastcgi-wrapper is still running (it should be):

```bash
pgrep -a fastcgi-wrapper
```

If it has somehow stopped:

```bash
sudo /usr/bin/perl /usr/bin/fastcgi-wrapper.pl &
```

---

## Phase 3 — Cleanup (only after running happily for a day or two)

Once you are confident the Docker setup is stable:

### Stop fastcgi-wrapper

```bash
sudo kill $(pgrep -f fastcgi-wrapper)
```

### Fix the certbot cron

The existing cron has two bugs: a wildcard minute field causes it to run 60 times
on the 1st of each month, and `--force-renewal` forces unnecessary renewals.

Edit `/etc/cron.d/certbot` — change:
```
* 3 1 * * root certbot-auto --nginx --force-renewal renew --post-hook="service nginx reload"
```
To:
```
0 3 1 * * root certbot-auto --nginx renew --post-hook="service nginx reload"
```

---

## Keeping the repo up to date on EC2

```bash
cd /home/ec2-user/Development/checkouts/scrollscraper
git pull
docker build -t scrollscraper .
docker-compose up -d   # restarts the container with the new image
```

---

## Known limitation: MP3 generation

The main Torah display (`scrollscraper.cgi`) works fully in Docker. The on-the-fly
MP3 builder (`buildmp3.cgi`) has a working-directory path issue under
`python3 -m http.server --cgi` that is tracked as a separate bug. MP3 generation
may not work until that is fixed in a follow-on PR.
