#!/usr/bin/env python3
"""Batch auto-map materials for multiple courses.

Usage example:
    python scripts/auto_map_materials.py \
        --base-url http://127.0.0.1:8000 \
        --email lecturer@example.com \
        --password drlecturer123 \
        --courses 1 2 3 \
        --min-similarity 0.55 \
        --min-quality 0.7

The script logs in once, then calls `/api/v1/recommendations/course/{course_id}/auto-map`
for each course ID provided.
"""
from __future__ import annotations

import argparse
import sys
from typing import Iterable, List

import requests


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Batch auto-map materials for courses")
    parser.add_argument(
        "--base-url",
        default="http://127.0.0.1:8000",
        help="Backend base URL (default: http://127.0.0.1:8000)",
    )
    parser.add_argument("--email", required=True, help="Lecturer or admin email")
    parser.add_argument("--password", required=True, help="Account password")
    parser.add_argument(
        "--courses",
        nargs="+",
        type=int,
        required=True,
        help="List of course IDs to auto-map (space separated)",
    )
    parser.add_argument(
        "--min-similarity",
        type=float,
        default=0.55,
        help="Similarity threshold passed to the API (default: 0.55)",
    )
    parser.add_argument(
        "--min-quality",
        type=float,
        default=0.7,
        help="Quality threshold passed to the API (default: 0.7)",
    )
    return parser.parse_args(list(argv) if argv is not None else None)


def login(base_url: str, email: str, password: str) -> str:
    resp = requests.post(
        f"{base_url}/api/v1/auth/login",
        data={"username": email, "password": password},
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    token = data.get("access_token")
    if not token:
        raise RuntimeError("Login succeeded but no access_token returned")
    return token


def auto_map_course(
    base_url: str,
    token: str,
    course_id: int,
    min_similarity: float,
    min_quality: float,
) -> dict:
    resp = requests.post(
        f"{base_url}/api/v1/recommendations/course/{course_id}/auto-map",
        headers={"Authorization": f"Bearer {token}"},
        json={"min_similarity": min_similarity, "min_quality": min_quality},
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)

    try:
        token = login(args.base_url.rstrip("/"), args.email, args.password)
    except Exception as exc:  # pragma: no cover - CLI helper
        print(f"✖ Login failed: {exc}", file=sys.stderr)
        return 1

    print("✓ Logged in successfully. Starting auto-map runs…")
    success_count = 0
    for course_id in args.courses:
        try:
            result = auto_map_course(
                args.base_url.rstrip("/"),
                token,
                course_id,
                args.min_similarity,
                args.min_quality,
            )
            success_count += 1
            print(
                f"  • Course {course_id}: {result.get('mappings_created', 0)} mappings created"
            )
        except requests.HTTPError as http_err:
            status = http_err.response.status_code
            body = http_err.response.text
            print(
                f"  ✖ Failed course {course_id} (status {status}): {body[:200]}",
                file=sys.stderr,
            )
        except Exception as exc:  # pragma: no cover - CLI helper
            print(f"  ✖ Failed course {course_id}: {exc}", file=sys.stderr)

    print(f"Done. Successful course runs: {success_count}/{len(args.courses)}")
    return 0 if success_count == len(args.courses) else 2


if __name__ == "__main__":
    raise SystemExit(main())
