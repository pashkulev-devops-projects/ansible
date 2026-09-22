#!/usr/bin/env python3
import json
import logging
import os
import sys
import tempfile
import time
import uuid
from pathlib import Path

from azure.appconfiguration.provider import SettingSelector, WatchKey, load
from azure.identity import ManagedIdentityCredential


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def write_json(path, value, mode):
    destination = Path(path)

    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=destination.parent,
        delete=False,
    ) as temporary_file:
        json.dump(value, temporary_file, indent=2, sort_keys=True)
        temporary_file.write("\n")
        temporary_file.flush()
        os.fsync(temporary_file.fileno())
        os.chmod(temporary_file.name, mode)

    os.replace(temporary_file.name, destination)


def build_outputs(provider, settings):
    configuration = {}
    secrets = {}

    for output_key, source in settings.items():
        target = secrets if source["secret"] else configuration
        target[output_key] = provider[source["key"]]

    return configuration, secrets


def publish(provider, config, previous_output):
    configuration, secrets = build_outputs(provider, config["settings"])
    current_output = (configuration, secrets)

    if current_output == previous_output:
        return previous_output

    output_directory = Path(config["output_directory"])
    release_directory = Path(tempfile.mkdtemp(prefix="release-", dir=output_directory))

    write_json(release_directory / "configuration.json", configuration, 0o644)
    write_json(release_directory / "secrets.json", secrets, 0o600)

    temporary_current = output_directory / f".current-{uuid.uuid4()}"
    os.symlink(release_directory.name, temporary_current)
    os.replace(temporary_current, output_directory / "current")

    logging.info("Published Azure runtime configuration.")
    return current_output


def main():
    with open(sys.argv[1], encoding="utf-8") as config_file:
        config = json.load(config_file)

    credential = ManagedIdentityCredential()
    settings = list(config["settings"].values())
    selectors = [
        SettingSelector(key_filter=source["key"], label_filter=config["label"])
        for source in settings
    ]
    selectors.append(
        SettingSelector(
            key_filter=config["sentinel_key"],
            label_filter=config["label"],
        )
    )

    provider = load(
        endpoint=config["endpoint"],
        credential=credential,
        keyvault_credential=credential,
        selects=selectors,
        refresh_on=[WatchKey(config["sentinel_key"], config["label"])],
        refresh_interval=config["refresh_interval_seconds"],
        secret_refresh_interval=config["refresh_interval_seconds"],
    )

    output = publish(provider, config, None)

    while True:
        time.sleep(config["refresh_interval_seconds"])
        provider.refresh()
        output = publish(provider, config, output)


if __name__ == "__main__":
    main()
