"""Stage 1 orchestrator — discovers candidate topics for the post pipeline."""

import sys
from pathlib import Path

# Resolve project root so `app` imports work regardless of how the process is started.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.stage_1.search_for_trending_piece.search_topic import search_for_topics

import json

from datetime import datetime


def start_stage_1():
    """Run Stage 1: fetch candidate topics and persist a dated snapshot."""
    print("stage 1")

    # Discover topics from the configured external source.
    raw_topics = search_for_topics()

    # Record when this topic batch was collected.
    current_date = datetime.now().strftime("%Y-%m-%d")

    data = {'date_updated':current_date, 'topics': raw_topics}


    with open("data/json/latest_topics.json", 'w') as file:
        json.dump(data, file)

    return raw_topics

