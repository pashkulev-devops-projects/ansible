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

Installs and configures a WireGuard server on Ubuntu. The role generates the
server private key on the managed host and never copies it to the controller.
It exposes the derived public key through the
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

The initial implementation supports Ubuntu hosts. Additional operating
systems should be added only after their package and service behavior is
tested.
