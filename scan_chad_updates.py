#!/usr/bin/env python3
import argparse
import http.cookiejar
import json
import os
import sqlite3
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def human_rows(rows):
    lines = [
        "# Chad Updates for Codex",
        "",
        f"Open requests: {len(rows)}",
        "",
        "Use this as implementation intake. Verify the code, test it, commit it, and deploy it before marking anything complete.",
        "",
    ]
    if not rows:
        lines.append("No open Chad Updates are waiting for implementation.")
    for row in rows:
        lines.extend([
            f"## #{row['id']} {row['title']}",
            f"- Status: {row['status']}",
            f"- Category: {row['category']}",
            f"- Requested by: {row.get('created_by_name') or 'Team'}",
            f"- Updated: {row.get('updated_at') or ''}",
            f"- Details: {row['details']}",
        ])
        comments = row.get("comments") or []
        if comments:
            lines.append("- Discussion:")
            for comment in comments[-8:]:
                lines.append(f"  - {comment.get('user_name') or 'Team'} ({comment.get('created_at') or ''}): {comment.get('body') or ''}")
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def scan_local(limit, db_override=""):
    data_dir = Path(os.environ.get("APP_DATA_DIR", str(ROOT / "app_data")))
    db_path = Path(db_override or os.environ.get("STUDIO_DB", str(data_dir / "studio.db")))
    if not db_path.exists():
        return None
    con = sqlite3.connect(str(db_path))
    con.row_factory = sqlite3.Row
    try:
        rows = [
            dict(row)
            for row in con.execute(
                """select cu.*,u.name created_by_name
                   from chad_updates cu left join users u on u.id=cu.created_by
                   where cu.status!='completed'
                   order by case cu.status when 'new' then 0 when 'considering' then 1 when 'planned' then 2 else 3 end,
                   cu.updated_at desc limit ?""",
                (limit,),
            )
        ]
        comments = [
            dict(row)
            for row in con.execute(
                """select cc.*,u.name user_name
                   from chad_update_comments cc left join users u on u.id=cc.user_id
                   where cc.update_id in (select id from chad_updates where status!='completed')
                   order by cc.created_at asc,cc.id asc"""
            )
        ]
    except sqlite3.OperationalError as exc:
        con.close()
        raise RuntimeError(f"{db_path} is not a Hancock Studio database: {exc}") from exc
    con.close()
    comment_map = {}
    for comment in comments:
        comment_map.setdefault(comment["update_id"], []).append(comment)
    for row in rows:
        row["comments"] = comment_map.get(row["id"], [])
    return human_rows(rows)


def scan_live(base_url, email, password, limit):
    if not email or not password:
        raise RuntimeError("Set STUDIO_EMAIL and STUDIO_PASSWORD to scan the live site.")
    base = base_url.rstrip("/")
    cookies = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(cookies),
        urllib.request.HTTPRedirectHandler(),
    )
    login_body = urllib.parse.urlencode({"username": email, "password": password}).encode("utf-8")
    login_req = urllib.request.Request(
        base + "/login",
        data=login_body,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    opener.open(login_req, timeout=30).read()
    url = f"{base}/api/codex-updates?limit={limit}"
    with opener.open(url, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))
    return payload.get("markdown") or human_rows(payload.get("updates") or [])


def main():
    parser = argparse.ArgumentParser(description="Pull open Chad Updates into a Codex-ready brief.")
    parser.add_argument("--live", action="store_true", help="Read from the live Render site instead of the local database.")
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--db", default="", help="Path to a local studio.db file.")
    parser.add_argument("--base-url", default=os.environ.get("STUDIO_BASE_URL", "https://hancock-live-marketing-studio.onrender.com"))
    parser.add_argument("--email", default=os.environ.get("STUDIO_EMAIL", "rknight@hancockclaims.com"))
    parser.add_argument("--password", default=os.environ.get("STUDIO_PASSWORD", ""))
    args = parser.parse_args()
    try:
        if args.live:
            text = scan_live(args.base_url, args.email, args.password, args.limit)
        else:
            text = scan_local(args.limit, args.db)
            if text is None:
                text = scan_live(args.base_url, args.email, args.password, args.limit)
        sys.stdout.write(text)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:500]
        raise SystemExit(f"Could not scan Chad Updates: HTTP {exc.code} {detail}")
    except Exception as exc:
        raise SystemExit(f"Could not scan Chad Updates: {exc}")


if __name__ == "__main__":
    main()
