#!/usr/bin/env python3
"""
demo_automation.py

Script to:
 1. Fetch demo info (title, DDL, ssh_pubkey, etc.) and linked editor (email & id)
 2. Create a new demo on IPOL
 3. Create a GitHub repo from template
 4. Fetch IPOL SSH pubkey and add as deploy key to the repo
 5. Attach the original demo's editor to the new demo
 6. Update DDL with latest build info and general requirements
"""

import argparse
import sqlite3
import os
import time
from datetime import datetime
import requests
import json
from github import Auth, Github
import sys

NEW_PREFIX = "55555000"

#DB fetch logic
def fetch_demo_info(db_path, demo_ids):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    results = []

    for demo_id in demo_ids:
        print(f"\nFetching info for demo_id: {demo_id}")

        cursor.execute("""
            SELECT ID, title, ssh_pubkey
            FROM demo
            WHERE editor_demo_id = ?
        """, (demo_id,))
        demo_row = cursor.fetchone()
        if not demo_row:
            print(f"No demo found with editor_demo_id = {demo_id}")
            continue

        ID, title, ssh_pubkey = demo_row

        #Fetch editor email
        cursor.execute("""
            SELECT editorID
            FROM demo_editor
            WHERE demoID = ?
        """, (ID,))
        editor_row = cursor.fetchone()
        editor_id = editor_row[0] if editor_row else None

        editor_email = None
        if editor_id:
            cursor.execute("""SELECT mail FROM editor WHERE ID = ?""", (editor_id,))
            mail_row = cursor.fetchone()
            editor_email = mail_row[0] if mail_row else None

        print(f"Found editor ID: {editor_id}, email: {editor_email}")

        #Fetch latest demodescription
        cursor.execute("""
            SELECT demodescriptionId
            FROM demo_demodescription
            WHERE demoID = ?
        """, (ID,))
        demodesc_ids = [row[0] for row in cursor.fetchall()]
        if not demodesc_ids:
            print(f"No demo_descriptions found for demo_id = {demo_id}")
            continue

        placeholders = ', '.join(['?'] * len(demodesc_ids))
        cursor.execute(f"""
            SELECT ID, creation, DDL
            FROM demodescription
            WHERE ID IN ({placeholders})
        """, demodesc_ids)
        demodescs = cursor.fetchall()

        def parse_creation_val(v):
            if v is None:
                return datetime.min
            if isinstance(v, (int, float)):
                try:
                    return datetime.fromtimestamp(v)
                except Exception:
                    return datetime.min
            if isinstance(v, str):
                for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
                    try:
                        return datetime.strptime(v, fmt)
                    except Exception:
                        pass
                try:
                    return datetime.fromisoformat(v)
                except Exception:
                    pass
                try:
                    return datetime.fromtimestamp(float(v))
                except Exception:
                    return datetime.min
            return datetime.min

        latest = max(demodescs, key=lambda x: parse_creation_val(x[1]))
        _, creation, ddl_blob = latest
        ddl_text = ddl_blob.decode("utf-8") if isinstance(ddl_blob, (bytes, bytearray)) else ddl_blob

        results.append({
            "original_demo_id": demo_id,
            "db_ID": ID,
            "title": title,
            "ssh_pubkey": ssh_pubkey,
            "editor_id": editor_id,
            "editor_email": editor_email,
            "latest_demodescription_id": latest[0],
            "latest_creation": creation,
            "ddl_text": ddl_text
        })

        print(f"Found title: {title}")
        print(f"Latest demodescription ID: {latest[0]} created at {creation}")
        print("DDL preview (first 300 chars):")
        print((ddl_text or "")[:300])

    conn.close()
    return results


def ipol_add_demo(host, new_demoid, title, ddl_str):
    url = f"{host}/api/demoinfo/demo"
    params = {"state": "test", "title": f"{title} - test", "demo_id": new_demoid, "ddl": ddl_str}

    r = requests.post(url, params=params)
    print(f"[IPOL] add_demo -> status={r.status_code}")

    if r.status_code == 409:
        print("Conflict: A demo with this title or demo ID already exists. Skipping creation.")
        sys.exit(0)

    r.raise_for_status()
    return r.json()


def ipol_get_ssh_key(host, demoid):
    url = f"{host}/api/demoinfo/ssh_keys/{demoid}"
    r = requests.get(url)
    print(f"[IPOL] get_ssh_keys -> {r.status_code}")
    r.raise_for_status()
    return r.json()


def ipol_add_editor_to_demo(host, new_demoid, editor_id):
    url = f"{host}/api/demoinfo/demos/{new_demoid}/editor/{editor_id}"
    print(f"[IPOL] Adding editor {editor_id} to demo {new_demoid}")
    r = requests.post(url)
    print(f"[IPOL] add_editor_to_demo -> {r.status_code}")
    r.raise_for_status()
    return r.json()


def create_github_repo_from_template(gh_token, org_name, template_repo, reponame, description):
    gh = Github(auth=Auth.Token(gh_token))
    org = gh.get_organization(org_name)
    try:
        repo = org.get_repo(reponame)
        print("Repo already exists:", repo.full_name)
        return repo
    except Exception:
        pass

    template = gh.get_repo(f"{org_name}/{template_repo}")
    repo = org.create_repo_from_template(
        name=reponame,
        repo=template,
        description=description,
        private=False,
    )
    time.sleep(2)
    return repo


def add_deploy_key_to_repo(repo, ipol_host, pubkey):
    try:
        repo.create_key(title=ipol_host, key=pubkey, read_only=True)
        print("Deploy key added.")
    except Exception as e:
        print("Deploy key might already exist:", e)


def make_new_demoid(old_demoid):
    return int(f"{NEW_PREFIX}{old_demoid}")


def cp2_demo_page(ipol_host, demoid):
    return f"{ipol_host}/cp2/showDemo?demo_id={demoid}"


def process_one(db_path, old_demoid, ipol_host, gh_org, template_repo, gh_token):
    fetched = fetch_demo_info(db_path, [old_demoid])
    if not fetched:
        print(f"Skipping {old_demoid} because nothing found.")
        return

    info = fetched[0]
    title = info["title"]
    ddl_text = info["ddl_text"]
    editor_id = info["editor_id"]
    editor_email = info["editor_email"]

    print(f"\nPreparing new demo for original {old_demoid} (title: {title})")
    new_demoid = make_new_demoid(old_demoid)
    print("New demo id:", new_demoid)
    cp2_url = cp2_demo_page(ipol_host, new_demoid)
    print("CP2 page for new demo will be:", cp2_url)

    # Create GitHub repo
    repo = create_github_repo_from_template(gh_token, gh_org, template_repo, str(new_demoid), f"{title} - test")
    if repo:
        print("Created GitHub repo:", repo.full_name)

    # Fetch latest commit SHA
    latest_commit_sha = repo.get_branch("main").commit.sha
    print("Latest commit SHA:", latest_commit_sha)

    # Update DDL
    ddl_dict = json.loads(ddl_text)

    # Update build section
    ddl_dict["build"] = {
        "url": f"git@github.com:{gh_org}/{new_demoid}.git",
        "rev": latest_commit_sha,
        "dockerfile": ".ipol/Dockerfile"
    }

    # Update general -> requirements
    if "general" not in ddl_dict or not isinstance(ddl_dict["general"], dict):
        ddl_dict["general"] = {}
    ddl_dict["general"]["requirements"] = "docker"

    updated_ddl_str = json.dumps(ddl_dict)

    # Create new demo on IPOL
    resp = ipol_add_demo(ipol_host, new_demoid, title, updated_ddl_str)
    print("IPOL add_demo response:", resp)

    # Fetch SSH pubkey
    pubkey_resp = ipol_get_ssh_key(ipol_host, new_demoid)
    pubkey = pubkey_resp.get("pubkey") if isinstance(pubkey_resp, dict) else None
    if pubkey:
        print("Fetched pubkey (truncated):", pubkey[:120])
        add_deploy_key_to_repo(repo, ipol_host, pubkey)

    # Add editor to new demo
    if editor_id:
        try:
            editor_resp = ipol_add_editor_to_demo(ipol_host, new_demoid, editor_id)
            print("Editor successfully linked:", editor_resp)
        except Exception as e:
            print(f"Failed to add editor to demo: {e}")
    else:
        print("No editor_id found for this demo.")

    print("Done. New demo CP2 page:", cp2_url)


def main():
    p = argparse.ArgumentParser(description="Copy demo(s) from DB to new IPOL demos + GitHub repos")
    p.add_argument("--db-path", required=True, help="Path to demoinfo.db")
    p.add_argument("--demo-ids", nargs="+", required=True, type=int, help="Old demo ids (editor_demo_id)")
    p.add_argument("--ipol-host", default=os.environ.get("IPOL_HOST", "https://integration.ipol.im"))
    p.add_argument("--gh-org", default=os.environ.get("GH_ORG", "ipol-demos"))
    p.add_argument("--template", default=os.environ.get("TEMPLATE_REPO", "template-python"))
    args = p.parse_args()

    gh_token = os.environ.get("GH_TOKEN")
    if not gh_token:
        raise SystemExit("GH_TOKEN env var required for real runs.")

    for old in args.demo_ids:
        try:
            process_one(args.db_path, old, args.ipol_host, args.gh_org, args.template, gh_token)
        except Exception as e:
            print(f"Error processing demo {old}: {e}")


if __name__ == "__main__":
    main()

