# Service orchestration with Docker Compose

**One line:** declaring a set of containers, their storage, their network and their start order in a
single file, so an entire multi-service system starts with one command.

> 🧊 **Layman box.** A restaurant kitchen needs an oven, a fridge, a dishwasher and a coffee machine.
> You could install each one by hand every morning, remembering which plug goes where and which must
> warm up before the others. Compose is the floor plan: it says which appliances exist, what each
> plugs into, which shelf keeps its contents overnight, and what has to be hot before service starts.
> One switch turns the kitchen on.

---

## The problem it solves

A modern application is rarely one process. This project alone needs a model server, a vector
database, a relational database, an experiment tracker and a trace viewer. Started by hand, that is
five installations, five sets of version drift, five ports to remember, and a README that goes stale
the first time someone upgrades something.

Three specific problems fall out of that:

1. **Reproducibility.** "Works on my machine" is usually a version difference nobody wrote down.
2. **Wiring.** Services need to find each other, and hardcoded IP addresses do not survive a restart.
3. **Lifecycle.** Starting is easy. Stopping *completely* — no leftover containers, no leftover
   networks, no half-deleted state — is where hand-rolled setups leak.

---

## How it works

Compose reads one YAML file describing **services** (containers), **volumes** (persistent storage)
and **networks** (how they reach each other), then reconciles reality against that description.

```mermaid
flowchart TD
    F["docker-compose.yml"] --> E["docker compose up"]
    E --> N["create network<br/>atelier_default"]
    E --> V["create named volumes<br/>pgdata · qdrant · mlflow"]
    N --> C1["postgres"]
    V --> C1
    C1 -->|"healthcheck passes"| C2["langfuse"]
    N --> C3["qdrant"]
    N --> C4["mlflow"]
    C1 --- DNS["service name = hostname<br/>langfuse reaches postgres at postgres:5432"]
```

The core of this project's file:

```yaml
services:
  postgres:
    image: postgres:16-alpine
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U atelier -d atelier"]
  langfuse:
    image: langfuse/langfuse:2
    depends_on:
      postgres: {condition: service_healthy}
    environment:
      DATABASE_URL: postgresql://atelier:${POSTGRES_PASSWORD}@postgres:5432/langfuse
volumes:
  pgdata:
```

**"Run Postgres, keep its data in a Docker-managed volume, and consider it healthy only when it
answers `pg_isready`. Do not start Langfuse until that happens, and let Langfuse find Postgres by the
name `postgres`, because on a Compose network the service name *is* the hostname."**

Three details in that snippet carry most of the weight:

- **`image: postgres:16-alpine`** — pinned. `latest` means a future `up` silently changes your
  database version.
- **`pgdata:/var/lib/postgresql/data`** — a *named volume*. Containers are disposable, so anything
  written inside a container's own filesystem dies with it. Data has to live somewhere that outlives
  the container.
- **`depends_on: {condition: service_healthy}`** — ordering by *readiness*, not by existence. Plain
  `depends_on` only waits for the container to be created, which is almost never what you want.

---

## Variations and trade-offs

| Approach | Good for | Bad for |
|---|---|---|
| **Compose** | One machine, development, small deployments. Trivially readable | No scheduling, no self-healing across machines, no rolling updates |
| **Kubernetes** | Many machines, autoscaling, rolling deploys, real failure recovery | Vastly more concepts and YAML for a stack that fits on one laptop |
| **Install natively** | Maximum performance, direct hardware access | Version drift, no isolation, painful to reproduce |
| **One container with everything** | Nothing, really | Violates one-process-per-container, makes upgrades and logs a mess |

**Named volumes vs bind mounts** is the trade-off worth internalising. A bind mount maps a *host*
directory into the container, which is ideal for source code you are editing live. A named volume is
managed by Docker and lives inside its VM, which is right for service data — nothing on the host
touches it, and no host filesystem quirk (permissions, path length, a syncing cloud drive) can
corrupt it.

**When Compose is the wrong tool:** the moment you need more than one machine. Its scaling story
(`deploy.replicas`) exists but has no scheduler behind it outside Swarm.

---

## Interview questions you should be able to answer

**What is the difference between an image and a container?**
An image is an immutable filesystem template plus metadata. A container is one running instance of
it, with a thin writable layer on top. Many containers, one image. Deleting a container does not
touch the image, and anything written to that writable layer dies with the container.

**Why pin image tags?**
Because `latest` is not a version, it is a moving pointer. An unpinned stack means a `docker compose
pull` can change your database major version, or swap an application for one with a different
migration state, with no diff to review. Pinning makes upgrades a deliberate commit.

**What does `depends_on` actually guarantee?**
By default, only start *order* — the dependency container is created first. It does **not** wait for
the process inside to be usable. Adding `condition: service_healthy` upgrades it to wait for a
passing healthcheck, which is the version that is actually useful. Without a healthcheck declared on
the dependency, that condition cannot be used at all.

**Where does container data go, and what survives a restart?**
Writes inside the container go to its writable layer and die with it. Writes to a mounted volume
survive. `docker compose down` removes containers and networks but keeps named volumes;
`down --volumes` deletes them. That distinction is why destructive cleanup deserves its own command.

**How do containers find each other?**
Compose puts them on a user-defined bridge network with an embedded DNS server, where each service
name resolves to that service's current container IP. So `postgres:5432` works from inside Langfuse
and keeps working after either container is recreated with a new IP.

**Why one process per container?**
So the lifecycle, logs, resource limits and restart policy of each thing are separately observable
and separately controllable. Bundling five processes into one container means a crash in any of them
is invisible to Docker, and an upgrade to any of them rebuilds all five.

**What is an orphan container, and why does `--remove-orphans` matter?**
If you rename or delete a service, its container keeps running while no longer matching the file.
The file then no longer describes reality, and the stale container still holds its ports. Making
`--remove-orphans` the default in `make down` means "stop" always means stop *everything this
project ever started*.

---

## In this project

[`docker-compose.yml`](../../docker-compose.yml) declares four services. Ollama is deliberately the
fifth service *not* in the file — it runs natively on the host so it reaches the GPU without WSL2
passthrough ([decision 9](../decision-log.md)). Every image is pinned. Nothing is bind-mounted,
because the repo lives on a syncing Google Drive path, and the `langfuse` database is created by an
inlined Compose `config` rather than a mounted `.sql` file for the same reason
([decision 12](../decision-log.md)).

`make down` uses `--remove-orphans` and keeps volumes; the destructive variant is a separate
`make clean`. Only Postgres declares a healthcheck — which is exactly why this project needs the
next concept.
