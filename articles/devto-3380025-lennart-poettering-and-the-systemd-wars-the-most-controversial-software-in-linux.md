---
title: "Lennart Poettering and the systemd Wars: The Most Controversial Software in Linux History"
date: 2026-03-21
topics: ["linux", "devops", "sysadmin", "opensource"]
published: true
canonical_url: "https://media.patentllm.org/en/blog/ai/nemotron-systemd-creator"
devto_url: "https://dev.to/soytuber/lennart-poettering-and-the-systemd-wars-the-most-controversial-software-in-linux-history-2a74"
devto_id: 3380025
---


No piece of software has divided the Linux community more bitterly than systemd. Depending on who you ask, it's either the most important infrastructure improvement in Linux since the 2.6 kernel, or an overengineered monstrosity that violates every principle Unix was built on.

The truth, as usual, is more interesting than either extreme.

## Lennart Poettering: The Most Controversial Developer in Linux

Lennart Poettering was a Red Hat engineer when he created systemd in 2010. He wasn't a random newcomer — he'd previously created PulseAudio (the Linux audio server that also generated enormous controversy) and Avahi (a zero-configuration networking implementation).

Poettering's pattern is consistent: he identifies infrastructure problems that the Linux community has tolerated for decades, builds comprehensive replacements, and then watches as the community splits between "finally, someone fixed this" and "how dare you change what was working."

With PulseAudio, the complaint was that it broke audio for millions of users during a rocky transition period (it did). With systemd, the complaint was more fundamental: it challenged the Unix philosophy itself.

## The Problem systemd Solved

Before systemd, Linux used SysVinit — a system initialization framework dating back to Unix System V (1983). Here's what booting a SysVinit system looked like:

1. The kernel starts PID 1 (`/sbin/init`)
2. Init reads `/etc/inittab` and executes shell scripts in `/etc/init.d/`
3. Each script starts one service, sequentially
4. Scripts depend on other scripts through naming conventions (S01network, S02sshd, S03apache)
5. Total boot time: 30-90 seconds on a modern machine

The problems were well-known:

**Sequential execution.** Starting services one-by-one is slow. If service A and service B are independent, they should start simultaneously. SysVinit couldn't do this.

**No dependency management.** The S01/S02/S03 numbering convention is fragile. If you add a new service that needs networking, you have to manually choose a number higher than S01network. Get it wrong and the service starts before the network is up.

**No process supervision.** If a service crashes, SysVinit doesn't notice. The admin has to set up external process monitors (monit, supervisord, daemontools) to handle restarts.

**Inconsistent scripting.** Every init script was a hand-written shell script. "Start" might mean `start-stop-daemon`, `daemon`, or just backgrounding the process with `&`. There was no standard interface.

Ubuntu tried to fix this with Upstart (2006), which added event-based activation. But Upstart's design was complex and still relied on shell scripts for service definitions.

## systemd's Design: The Declaration That Changed Everything

Poettering's key insight was that service management should be **declarative, not imperative.** Instead of shell scripts that execute commands, systemd uses unit files that describe desired state:

```ini
[Unit]
Description=My Web Application
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 /opt/myapp/server.py
Restart=on-failure
RestartSec=5
User=www-data

[Install]
WantedBy=multi-user.target
```

This 12-line file replaces a 50-line shell script and provides: dependency ordering (`After=`), automatic restart on crash (`Restart=on-failure`), user isolation (`User=www-data`), and standard start/stop/status commands (`systemctl start myapp`).

But systemd went further. Much further.

## The Scope Creep That Enraged Unix Purists

systemd didn't stop at init. Over time, it absorbed:

- **journald**: Binary logging (replacing syslog)
- **networkd**: Network configuration
- **resolved**: DNS resolution
- **timesyncd**: NTP client
- **logind**: Session management
- **timedated/localed/hostnamed**: System configuration
- **udevd**: Device management
- **nspawn**: Container runtime
- **homed**: Home directory management

This is where the controversy ignited. The Unix philosophy — "do one thing and do it well" — implies that an init system should initialize the system and nothing else. systemd became an entire platform.

## The Debate: Both Sides Have a Point

### The Case Against systemd

**"PID 1 should be simple."** The init process (PID 1) has special status in Unix — if it crashes, the entire system goes down. Traditional Unix kept PID 1 minimal for exactly this reason. systemd's PID 1 is complex, with many code paths that could theoretically fail.

**"Binary logs are hostile."** journald stores logs in a binary format. You can't `grep` them directly — you need `journalctl`. When the journal database corrupts (and it does), you lose all logs with no text fallback. The syslog community was incensed.

**"It violates separation of concerns."** Having the init system also handle DNS, NTP, networking, and containers means a bug in the DNS resolver could theoretically affect system boot. Components that should be independent are coupled through shared infrastructure.

**"Poettering doesn't take criticism well."** This is the human element. Bug reports were sometimes dismissed, alternative approaches were rejected without consideration, and the speed of adoption left distributions with limited time to evaluate the change. The relationship between Poettering and parts of the community became genuinely hostile — to the point where Poettering wrote a blog post about receiving death threats.

### The Case For systemd

**"SysVinit was broken and nobody was fixing it."** The sequential boot, the fragile numbering, the inconsistent scripts — these weren't theoretical problems. They were daily pain for system administrators. systemd fixed all of them.

**"Parallel boot is not optional."** Modern systems have SSDs that can start 50 services simultaneously. Sequential boot on an SSD is leaving 90% of the hardware idle. systemd's dependency graph enables parallel startup, reducing boot times from 30 seconds to 3 seconds.

**"Integration enables features."** journald + systemd together enable `journalctl -u nginx --since "1 hour ago"` — showing logs from one specific service for a specific time window. With syslog + SysVinit, this requires parsing text files and correlating timestamps manually.

**"The alternatives lost on merit."** Upstart, OpenRC, runit, s6 — all had their chance. Distributions evaluated them and chose systemd. Not because of politics or coercion, but because systemd solved more problems for more users.

## The Devuan Fork: Voting With Code

The most dramatic response to systemd came from the Devuan project — a fork of Debian that explicitly removes systemd and replaces it with sysvinit or OpenRC.

Devuan's creation in 2014 was accompanied by the "Veteran Unix Admins" open letter, which accused Debian of making a decision that "breaks the UNIX philosophy" and "creates a dangerous single point of failure."

Devuan still exists and has an active community. But its existence also proves the systemd camp's point: if you remove systemd, you have to maintain patches for hundreds of packages that now expect systemd features. It's an enormous ongoing maintenance burden, which is itself an argument for standardizing on systemd.

## systemd in 2026: The War Is Over

The controversy has largely settled. systemd won, not because everyone agrees it's the best design, but because:

1. **Every major distribution adopted it.** Debian, Ubuntu, Fedora, RHEL, SUSE, Arch — all use systemd as default.
2. **Software assumes it.** Docker, Kubernetes, most databases, most web servers — all ship systemd unit files. Not supporting systemd means maintaining your own service management.
3. **A generation of admins grew up with it.** New Linux users learn `systemctl` first and might never encounter SysVinit. The knowledge base has shifted.
4. **It's genuinely good at its job.** For all the controversy, systemd manages services reliably, boots fast, handles dependencies correctly, and provides excellent introspection tools.

## Practical systemd: What Developers Should Know

For developers who just want to run services, here's the 80/20 of systemd:

**User services** (no root required):
```bash
mkdir -p ~/.config/systemd/user/
# Create unit file at ~/.config/systemd/user/myapp.service
systemctl --user daemon-reload
systemctl --user enable --now myapp.service
```

**Essential commands:**
```bash
systemctl status myapp        # Is it running?
systemctl restart myapp       # Restart it
journalctl -u myapp -f        # Follow logs
systemctl edit myapp           # Override settings without modifying the unit file
systemctl list-timers          # See scheduled tasks (systemd timers replace cron)
```

**The unit file template that covers 90% of use cases:**
```ini
[Unit]
Description=My Application
After=network-online.target

[Service]
Type=simple
ExecStart=/path/to/your/binary
Restart=always
RestartSec=5
Environment=NODE_ENV=production

[Install]
WantedBy=default.target
```

Whether you love or hate the design philosophy, systemd is the init system you'll be using for the foreseeable future. Understanding it isn't optional — it's infrastructure literacy.


*I'm a semi-retired patent lawyer in Japan who started coding in December 2024. I build AI-powered search tools including [PatentLLM](https://patentllm.org) (3.5M US patent search engine) and various local-LLM applications on a single RTX 5090.*

