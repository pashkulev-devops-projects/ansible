# Ansible infrastructure collection

Reusable Ansible content for infrastructure managed by
`pashkulev-devops-projects`.

## Installation from Git

Add the collection to the consuming project's `requirements.yml` and pin it
to an immutable commit:

```yaml
collections:
  - name: https://github.com/pashkulev-devops-projects/ansible.git
    type: git
    version: <COMMIT_SHA>
```

## Roles

### `pashkulev.infrastructure.wireguard_server`

Installs and configures a WireGuard server on supported systemd-based Debian
and Red Hat distributions. The role generates the server private key on the
managed host and never copies it to the controller. It exposes the derived
public key through the
`wireguard_server_public_key` Ansible fact.

```yaml
- name: Configure WireGuard
  hosts: wireguard_servers
  roles:
    - role: pashkulev.infrastructure.wireguard_server
      wireguard_server_address: 10.100.0.1/24
      wireguard_listen_port: 51820
      wireguard_peers:
        - public_key: "{{ runner_public_key }}"
          allowed_ips:
            - 10.100.0.2/32
```

The initial implementation supports Ubuntu 24.04, RHEL 9, and Amazon Linux
2023 when `wireguard-tools` is available in the configured repositories.

### `pashkulev.infrastructure.azure_runtime_synchronizer`

Runs a systemd service that uses the Azure Arc managed identity to load App
Configuration values and resolve Key Vault references. It refreshes on the
configured sentinel every five minutes and atomically switches the `current`
release directory only after both files are written.

```yaml
- role: pashkulev.infrastructure.azure_runtime_synchronizer
  azure_runtime_synchronizer_config:
    endpoint: https://example.azconfig.io
    label: prod
    key_prefix: example:
    sentinel_key: example:configuration:sentinel
    refresh_interval_seconds: 300
    output_directory: /var/lib/example/runtime
```

The service loads every setting matching `key_prefix` and `label`. It removes
the prefix from output keys. Ordinary values are written to
`current/configuration.json`; Key Vault references are resolved and written to
`current/secrets.json` with mode `0600`.

For example, `example:api:openai:model` becomes `api:openai:model`. A new
runtime value needs no role change: add it under the configured prefix. Secrets
must be stored in Key Vault and referenced from App Configuration.

Consumers must resolve `current` once, then read both files from that resolved
directory. This gives each reload a consistent configuration generation.
