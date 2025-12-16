#!/usr/bin/env python3
"""Migration script: convert old single-instance reports to multi-instance format.

Old format: SK = REPORT#{type} (e.g., REPORT#compatibility_pro)
New format: SK = REPORT#{type}#{instance_id} (e.g., REPORT#compatibility_pro#abc12345)

This applies to: compatibility_pro, name_selection, year_forecast, date_calendar

Usage:
    python scripts/migrate_reports.py           # dry run
    python scripts/migrate_reports.py --apply   # apply changes
"""

import argparse
import uuid
from datetime import datetime

import boto3
from boto3.dynamodb.conditions import Key

# Report types that need migration
MULTI_INSTANCE_REPORTS = {"compatibility_pro", "name_selection", "year_forecast", "date_calendar"}


def migrate_reports(dry_run: bool = True):
    """Migrate old format reports to new multi-instance format."""
    dynamodb = boto3.resource("dynamodb", region_name="eu-central-1")

    # Get table name from environment or use default
    import os
    table_name = os.environ.get("DYNAMODB_TABLE_REPORTS", "numerolog-reports")

    reports_table = dynamodb.Table(table_name)

    print(f"Scanning table: {table_name}")
    print(f"Dry run: {dry_run}\n")

    # Scan for all report items
    response = reports_table.scan()
    items = response.get("Items", [])

    # Handle pagination
    while "LastEvaluatedKey" in response:
        response = reports_table.scan(ExclusiveStartKey=response["LastEvaluatedKey"])
        items.extend(response.get("Items", []))

    print(f"Found {len(items)} total report items\n")

    migrated = 0
    skipped = 0

    for item in items:
        pk = item.get("PK", "")
        sk = item.get("SK", "")

        # Check if this is an old format multi-instance report
        if not sk.startswith("REPORT#"):
            continue

        # Parse SK to get report type
        sk_parts = sk.split("#")
        if len(sk_parts) != 2:
            # Already has instance_id (3 parts: REPORT, type, instance_id)
            skipped += 1
            continue

        report_type = sk_parts[1]

        if report_type not in MULTI_INSTANCE_REPORTS:
            # Not a multi-instance report type
            skipped += 1
            continue

        # This needs migration
        instance_id = uuid.uuid4().hex[:8]
        new_sk = f"REPORT#{report_type}#{instance_id}"

        # Build context based on report type
        context = {}
        if report_type == "compatibility_pro":
            context = {"partner_name": "Unknown", "migrated": True}
        elif report_type == "name_selection":
            context = {"purpose": "unknown", "migrated": True}
        elif report_type == "year_forecast":
            # Try to extract year from content if possible
            context = {"year": datetime.now().year, "migrated": True}
        elif report_type == "date_calendar":
            context = {"month": datetime.now().month, "year": datetime.now().year, "migrated": True}

        print(f"Migrating: {pk} | {sk} -> {new_sk}")
        print(f"  Context: {context}")

        if not dry_run:
            # Create new item with instance_id
            new_item = {
                "PK": pk,
                "SK": new_sk,
                "content": item.get("content", ""),
                "context": context,
                "created_at": item.get("created_at", datetime.now().isoformat()),
            }

            reports_table.put_item(Item=new_item)

            # Delete old item
            reports_table.delete_item(Key={"PK": pk, "SK": sk})

            print("  ✓ Migrated")
        else:
            print("  (dry run - no changes)")

        migrated += 1
        print()

    print("=" * 50)
    print(f"Total items scanned: {len(items)}")
    print(f"Migrated: {migrated}")
    print(f"Skipped (already migrated or not multi-instance): {skipped}")

    if dry_run and migrated > 0:
        print("\nRun with --apply to apply changes")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Migrate reports to multi-instance format")
    parser.add_argument("--apply", action="store_true", help="Apply changes (default is dry run)")
    args = parser.parse_args()

    migrate_reports(dry_run=not args.apply)
