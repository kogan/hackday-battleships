#!/usr/bin/env python3

import argparse
import os
import re
import subprocess
import sys

commands = {}
flags = {"project": ""}

connection_re = re.compile(r"^postgres://(?P<user>.+?):(?P<password>.+?)@//cloudsql/(?P<host>.+)$")


def command(name):
    def decorator(f):
        commands[name] = f
        return f

    return decorator


def get_db_connection():
    p = subprocess.Popen(
        [
            "gcloud",
            "--project",
            flags["project"],
            "secrets",
            "versions",
            "access",
            "--secret",
            "DATABASE_URL",
            "latest",
        ],
        stdout=subprocess.PIPE,
    )
    stdout, stderr = p.communicate()
    conn = stdout.decode("utf-8")
    match = connection_re.match(conn).groupdict()
    instance_name, db_name = match["host"].rsplit("/", maxsplit=1)
    return instance_name, db_name, match["user"], match["password"]


def run_docker(*args):
    env = dict(os.environ)
    instance, db, user, password = get_db_connection()
    env.update(
        {
            "DB_INSTANCE": instance,
            "DB_USER": user,
            "DB_PASSWORD": password,
            "DB_NAME": db,
            "PROJECT_ID": flags["project"],
            "CONTAINER_NAME": "engine",
        }
    )
    subprocess.Popen(["docker-compose", "pull"], env=env).wait()
    subprocess.Popen(
        ["docker-compose", "run", "--rm", *args],
        stderr=sys.stderr,
        stdin=sys.stdin,
        stdout=sys.stdout,
        env=env,
    ).wait()

    # stop the proxy so it's not running in the background
    # docker-compose run doesn't support stopping dependencies
    subprocess.Popen(["docker-compose", "rm", "--stop", "-f", "clouddb"]).wait()


@command("psql")
def psql():
    run_docker("cloudpsql")


@command("shell")
def shell():
    run_docker("cloudshell")


def main():
    parser = argparse.ArgumentParser(description="Connect to a running gcp cloudrun instance")
    parser.add_argument(
        "--project", dest="project", help="Project to connect to", required=True,
    )
    parser.add_argument("command", choices=commands.keys())
    args = parser.parse_args()
    if not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
        print("env var GOOGLE_APPLICATION_CREDENTIALS is not set", file=sys.stderr)
        exit(1)
    flags["project"] = args.project
    commands[args.command]()


if __name__ == "__main__":
    main()
