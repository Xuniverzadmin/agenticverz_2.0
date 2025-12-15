#!/usr/bin/env python3
"""
M12 Example: Parallel URL Scraper Pipeline

Demonstrates the multi-agent system capabilities:
- Job spawning with agent_spawn
- Parallel worker claiming
- Blackboard aggregation
- Credit tracking

Usage:
    PYTHONPATH=. python examples/m12_parallel_scrape.py

Environment:
    DATABASE_URL - PostgreSQL connection string
    REDIS_URL - Redis connection string
"""

import json
import os
import sys
import time
import uuid
from typing import Any, Dict, List

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.agents.services.job_service import JobService, JobConfig
from app.agents.services.worker_service import WorkerService
from app.agents.services.blackboard_service import BlackboardService
from app.agents.services.registry_service import RegistryService


def simulate_url_scrape(url: str) -> Dict[str, Any]:
    """Simulate scraping a URL (would use httpx/aiohttp in production)."""
    # Simulate network delay
    time.sleep(0.1)

    # Return mock data based on URL
    return {
        "url": url,
        "title": f"Page {url.split('/')[-1]}",
        "word_count": len(url) * 10,
        "links": 5,
        "status": 200
    }


def run_parallel_scrape_example():
    """Run the parallel scrape example."""
    print("=" * 60)
    print("M12 Example: Parallel URL Scraper")
    print("=" * 60)

    # Initialize services
    job_service = JobService()
    worker_service = WorkerService()
    blackboard_service = BlackboardService()
    registry_service = RegistryService()

    # Create sample URLs
    urls = [f"https://example.com/page/{i}" for i in range(20)]

    print(f"\nCreating job with {len(urls)} URLs to scrape...")

    # Create job configuration
    config = JobConfig(
        orchestrator_agent="scraper_orchestrator",
        worker_agent="scraper_worker",
        task="parallel_url_scrape",
        items=[{"url": url} for url in urls],
        parallelism=5,
        timeout_per_item=30,
        max_retries=2
    )

    # Spawn the job
    orchestrator_id = f"orchestrator-{uuid.uuid4().hex[:8]}"
    job = job_service.create_job(
        config=config,
        orchestrator_instance_id=orchestrator_id,
        tenant_id="demo-tenant"
    )

    job_id = str(job.id)
    print(f"\nJob created: {job_id}")
    print(f"  Total items: {job.progress.total}")
    print(f"  Parallelism: 5 workers")
    print(f"  Credits reserved: {job.credits.reserved}")

    # Initialize blackboard for aggregation
    results_key = f"job:{job_id}:results"
    total_words_key = f"job:{job_id}:total_words"
    blackboard_service.set(total_words_key, 0)

    print("\n" + "-" * 40)
    print("Starting workers...")

    # Simulate 5 parallel workers
    workers_completed = []

    def run_worker(worker_num: int):
        """Simulate a worker processing items."""
        worker_id = f"worker-{worker_num}-{uuid.uuid4().hex[:4]}"

        # Register worker
        registry_service.register(
            agent_id="scraper_worker",
            instance_id=worker_id,
            job_id=job_id,
            capabilities={"skills": ["http_scrape"]}
        )

        items_processed = 0

        while True:
            # Claim next item
            item = worker_service.claim_item(
                job_id=job_id,
                worker_instance_id=worker_id
            )

            if not item:
                break

            # Process the URL
            url = item.input.get("url")
            result = simulate_url_scrape(url)

            # Update blackboard (atomic increment)
            blackboard_service.increment(total_words_key, result["word_count"])

            # Store individual result
            result_key = f"{results_key}:{item.item_index}"
            blackboard_service.set(result_key, result)

            # Mark item complete
            worker_service.complete_item(
                item_id=str(item.id),
                output=result
            )

            items_processed += 1

            # Heartbeat
            registry_service.heartbeat(worker_id)

        # Deregister worker
        registry_service.deregister(worker_id)

        return items_processed

    # Run workers sequentially for demo (would be concurrent in production)
    total_processed = 0
    for i in range(5):
        processed = run_worker(i)
        total_processed += processed
        print(f"  Worker {i}: processed {processed} items")

    print(f"\nTotal items processed: {total_processed}")

    # Get final job status
    final_status = job_service.get_job(job_id)

    print("\n" + "-" * 40)
    print("Job Results:")
    print(f"  Status: {final_status.status}")
    print(f"  Completed: {final_status.progress.completed}/{final_status.progress.total}")
    print(f"  Failed: {final_status.progress.failed}")
    print(f"  Progress: {final_status.progress.progress_pct:.1f}%")

    # Get aggregated results from blackboard
    total_words = blackboard_service.get(total_words_key)

    print("\n" + "-" * 40)
    print("Aggregated Results (from Blackboard):")
    print(f"  Total word count: {total_words}")

    # Get individual results
    results = blackboard_service.scan_pattern(f"job:{job_id}:results:*")

    print(f"  Individual results stored: {len(results)}")

    if results:
        # Show sample results
        print("\n  Sample results:")
        for i, entry in enumerate(results[:3]):
            print(f"    [{i}] {entry.value}")

    # Credit summary
    print("\n" + "-" * 40)
    print("Credit Summary:")
    print(f"  Reserved: {job.credits.reserved}")
    print(f"  Spent: {final_status.credits.spent}")
    print(f"  Refunded: {final_status.credits.refunded}")

    # Cleanup blackboard keys
    print("\n" + "-" * 40)
    print("Cleaning up...")
    blackboard_service.delete(total_words_key)
    for entry in results:
        blackboard_service.delete(entry.key.replace(blackboard_service.key_prefix, ""))

    print("\nExample complete!")
    print("=" * 60)

    return {
        "job_id": job_id,
        "completed": final_status.progress.completed,
        "total_words": total_words,
        "status": "success" if final_status.progress.completed == len(urls) else "partial"
    }


if __name__ == "__main__":
    # Check for required environment variables
    if not os.getenv("DATABASE_URL"):
        print("ERROR: DATABASE_URL not set")
        sys.exit(1)

    if not os.getenv("REDIS_URL"):
        print("WARNING: REDIS_URL not set, using default localhost")
        os.environ["REDIS_URL"] = "redis://localhost:6379/0"

    result = run_parallel_scrape_example()
    print(f"\nFinal result: {json.dumps(result, indent=2)}")
