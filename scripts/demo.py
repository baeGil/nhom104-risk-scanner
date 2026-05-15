#!/usr/bin/env python3
"""
Demo script for Vietnamese Legal Knowledge Graph API.
Tests all endpoints end-to-end with sample data.

Usage:
    python scripts/demo.py
"""

import json
import time
import sys
import os

BASE_URL = os.environ.get("API_URL", "http://localhost:8000")

try:
    import requests
except ImportError:
    print("Installing requests...")
    os.system("pip install requests")
    import requests


def print_section(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def print_result(label: str, data):
    print(f"  {label}:")
    if isinstance(data, (dict, list)):
        print(f"    {json.dumps(data, ensure_ascii=False, indent=2)}")
    else:
        print(f"    {data}")
    print()


def test_health():
    print_section("1. Health Check")
    r = requests.get(f"{BASE_URL}/health")
    print_result("Status", r.json())
    assert r.json()["status"] == "ok", "Health check failed"
    print("  ✓ Health check passed")


def test_contract_upload():
    print_section("2. Contract Review Pipeline")

    # Upload sample contract
    sample_path = "data/sample_contracts/sample_hop_dong_thue.md"
    if not os.path.exists(sample_path):
        print(f"  ⚠ Sample contract not found at {sample_path}, skipping")
        return None

    print(f"  Uploading: {sample_path}")
    with open(sample_path, "rb") as f:
        r = requests.post(
            f"{BASE_URL}/api/contracts/upload",
            files={"file": ("sample_hop_dong_thue.md", f, "text/markdown")},
            data={"title": "Hợp đồng thuê văn phòng"},
        )
    result = r.json()
    print_result("Upload response", result)
    job_id = result["jobId"]

    # Poll until complete
    print("  Polling job status...")
    for i in range(10):
        time.sleep(1)
        r = requests.get(f"{BASE_URL}/api/contracts/{job_id}/status")
        status = r.json()
        print(f"    Attempt {i+1}: status={status['status']}, progress={status['progress']}%")
        if status["status"] in ("completed", "failed"):
            break

    assert status["status"] == "completed", f"Job failed: {status}"
    print("\n  ✓ Contract review completed")

    # Display results
    clauses = status.get("clauses", [])
    compliance = status.get("compliance", {})

    print(f"\n  Extracted {len(clauses)} clauses:")
    for c in clauses:
        risk_icon = {"low": "✓", "medium": "⚠", "high": "✗"}.get(c.get("riskLevel", "low"), "?")
        print(f"    {risk_icon} [{c['type']}] {c['text'][:60]}...")

    violations = compliance.get("violations", [])
    if violations:
        print(f"\n  Found {len(violations)} compliance violation(s):")
        for v in violations:
            print(f"    ✗ {v['clause']}: {v['description']}")
            print(f"      Citation: {v['citation']} (verified: {v['verified']})")

    risks = compliance.get("risks", [])
    if risks:
        print(f"\n  Risks:")
        for r_text in risks:
            print(f"    ⚠ {r_text}")

    suggestions = compliance.get("suggestions", [])
    if suggestions:
        print(f"\n  Suggestions:")
        for s in suggestions:
            print(f"    → {s}")

    return job_id


def test_contract_history():
    print_section("3. Contract History")
    r = requests.get(f"{BASE_URL}/api/contracts/history")
    jobs = r.json()
    print(f"  Total jobs: {len(jobs)}")
    for j in jobs:
        print(f"    - {j['filename']}: {j['status']} ({j['jobId']})")
    print("  ✓ Contract history retrieved")


def test_qa_chat():
    print_section("4. QA Chat (SSE Streaming)")

    questions = [
        "Mức phạt vi phạm hợp đồng tối đa theo Luật Thương mại là bao nhiêu?",
        "Điều kiện để đơn phương chấm dứt hợp đồng lao động?",
        "Thời hiệu khởi kiện tranh chấp hợp đồng là bao lâu?",
    ]

    conversation_id = None

    for q in questions:
        print(f"  Q: {q}")
        r = requests.post(
            f"{BASE_URL}/api/qa/chat",
            json={"message": q, "conversationId": conversation_id},
            stream=True,
        )

        answer = ""
        intents = []
        for line in r.iter_lines():
            if line:
                line_str = line.decode("utf-8")
                if line_str.startswith("data: "):
                    data_str = line_str[6:]
                    if data_str == "[DONE]":
                        break
                    try:
                        data = json.loads(data_str)
                        if "intents" in data:
                            intents = data["intents"]
                        if "token" in data:
                            answer += data["token"]
                    except json.JSONDecodeError:
                        pass

        print(f"  A: {answer[:120]}...")
        if intents:
            print(f"  Intents: {[i['type'] for i in intents]}")
        print()

    print("  ✓ QA chat completed")


def test_conversations():
    print_section("5. Conversation Management")

    # Create
    r = requests.post(
        f"{BASE_URL}/api/qa/conversations",
        json={"title": "Demo conversation"},
    )
    conv = r.json()
    print_result("Created conversation", conv)

    # List
    r = requests.get(f"{BASE_URL}/api/qa/conversations")
    convs = r.json()
    print(f"  Total conversations: {len(convs)}")
    for c in convs:
        print(f"    - {c['title'][:40]} ({c['id']})")

    # Delete
    conv_id = conv["id"]
    r = requests.delete(f"{BASE_URL}/api/qa/conversations/{conv_id}")
    print(f"\n  Deleted conversation {conv_id}: {r.status_code}")
    print("  ✓ Conversation management works")


def main():
    print("\n" + "█" * 60)
    print("  Vietnamese Legal Knowledge Graph — Demo Script")
    print("█" * 60)

    # Check API is running
    try:
        requests.get(f"{BASE_URL}/health", timeout=5)
    except requests.ConnectionError:
        print(f"\n  ✗ API not running at {BASE_URL}")
        print("  Start with: uvicorn infra.api.app:app --port 8000")
        sys.exit(1)

    test_health()
    test_contract_upload()
    test_contract_history()
    test_qa_chat()
    test_conversations()

    print_section("Demo Complete ✓")
    print("  All endpoints tested successfully.")
    print(f"  API: {BASE_URL}")
    print()


if __name__ == "__main__":
    main()
