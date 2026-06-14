from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone

from app.utils.datetime import utc_now


def seed_database(connection: sqlite3.Connection) -> None:
    customers = [
        ("Anika Rao", "Northstar Retail", "anika.rao@northstar.example", "+91 98765 10234", "Enterprise"),
        ("Marcus Hill", "BluePeak Logistics", "marcus.hill@bluepeak.example", "+1 415 555 0137", "Business"),
        ("Nora Singh", "Greenline Foods", "nora.singh@greenline.example", "+91 98123 45678", "Standard"),
        ("Priya Menon", "OrbitPay", "priya.menon@orbitpay.example", "+91 90000 45123", "Enterprise"),
        ("Leo Carter", "StudioVale", "leo.carter@studiovale.example", "+1 212 555 0173", "Business"),
    ]

    agents = [
        ("Sam Wilson", "sam.wilson@crm.example", "Support Lead"),
        ("Maya Chen", "maya.chen@crm.example", "Technical Support"),
        ("Ishaan Verma", "ishaan.verma@crm.example", "Billing Specialist"),
        ("Elena Park", "elena.park@crm.example", "Customer Success"),
    ]

    connection.executemany(
        """
        INSERT INTO customers (name, company, email, phone, tier)
        VALUES (?, ?, ?, ?, ?)
        """,
        customers,
    )
    connection.executemany(
        """
        INSERT INTO agents (name, email, role)
        VALUES (?, ?, ?)
        """,
        agents,
    )

    now = datetime.now(timezone.utc).replace(microsecond=0)
    tickets = [
        (
            "Invoice download fails for March statement",
            "Customer gets a blank PDF when downloading the March invoice from the billing portal.",
            "Open",
            "High",
            "Billing",
            "Portal",
            4,
            3,
            now + timedelta(days=1),
            now - timedelta(hours=6),
        ),
        (
            "Need onboarding checklist for new branches",
            "Retail team is opening three branches and asked for the setup checklist and admin access plan.",
            "In Progress",
            "Medium",
            "Onboarding",
            "Email",
            1,
            4,
            now + timedelta(days=3),
            now - timedelta(days=1, hours=4),
        ),
        (
            "Webhook retries are delayed",
            "Operations dashboard shows delayed retry events after failed shipment status webhooks.",
            "Pending Customer",
            "Urgent",
            "Integrations",
            "Phone",
            2,
            2,
            now + timedelta(hours=8),
            now - timedelta(hours=18),
        ),
        (
            "Change account owner",
            "Customer requested account ownership transfer after an internal team change.",
            "Resolved",
            "Low",
            "Account",
            "Portal",
            3,
            1,
            now - timedelta(days=1),
            now - timedelta(days=3),
        ),
        (
            "Campaign export CSV has missing columns",
            "CSV export is missing source and attribution columns for campaigns created this week.",
            "Open",
            "Medium",
            "Reporting",
            "Chat",
            5,
            2,
            now + timedelta(days=2),
            now - timedelta(hours=3),
        ),
        (
            "SSO certificate rotation support",
            "Enterprise customer needs support rotating their SSO certificate before it expires.",
            "In Progress",
            "High",
            "Security",
            "Email",
            1,
            2,
            now + timedelta(days=5),
            now - timedelta(days=2, hours=2),
        ),
    ]

    for subject, description, status, priority, category, source, customer_id, agent_id, due_at, created_at in tickets:
        connection.execute(
            """
            INSERT INTO tickets (
                subject, description, status, priority, category, source,
                customer_id, agent_id, due_at, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                subject,
                description,
                status,
                priority,
                category,
                source,
                customer_id,
                agent_id,
                due_at.isoformat(),
                created_at.isoformat(),
                created_at.isoformat(),
            ),
        )

    comments = [
        (1, "Ishaan Verma", "Reproduced the issue and confirmed billing API returns the document metadata."),
        (2, "Elena Park", "Shared draft checklist and waiting for branch manager names."),
        (3, "Maya Chen", "Asked customer for webhook delivery IDs to compare retry timestamps."),
        (4, "Sam Wilson", "Ownership changed and confirmation sent."),
        (5, "Maya Chen", "Export job logs show the new attribution fields are not included in the serializer."),
        (6, "Maya Chen", "Scheduled working session with customer IT admin."),
    ]

    connection.executemany(
        """
        INSERT INTO comments (ticket_id, author, body, created_at)
        VALUES (?, ?, ?, ?)
        """,
        [(ticket_id, author, body, utc_now()) for ticket_id, author, body in comments],
    )
