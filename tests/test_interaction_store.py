import time

from app.services.interaction_store import (
    get_interaction_stats,
    init_interaction_db,
    interaction_db_stats,
    record_interaction_event,
    stop_interaction_writer,
)


def test_interaction_store_records_event(tmp_path):
    # Stop any app-level writer that may have been started by another test,
    # then start a writer bound to this test's temporary database.
    stop_interaction_writer()
    db_path = str(tmp_path / "interaction.db")
    init_interaction_db(db_path)

    try:
        record_interaction_event(
            request_id="req-test",
            executed_at="2026-01-01T00:00:00+00:00",
            api_key="sas_test_key",
            user_id=1,
            plan="pro",
            conversation_turns=2,
            assistant_turns=1,
            summary={
                "final_dominant_state": "Ambivalent",
                "final_dominant_probability": 0.55,
                "final_omega_t": 0.42,
                "final_sigma": 0.31,
                "demand_peak": 1.0,
                "alerts": {
                    "threshold_crossed": True,
                    "stability_below_kappa": True,
                    "high_uncertainty": False,
                },
            },
            input_hash="inputhash",
            content_fingerprint="fingerprint",
            latency_ms=12.3,
        )

        for _ in range(20):
            stats = interaction_db_stats(db_path)
            if stats.get("total_events", 0) >= 1:
                break
            time.sleep(0.2)

        stats = interaction_db_stats(db_path)
        assert stats["ok"] is True
        assert stats["total_events"] >= 1

        public = get_interaction_stats(days=7, db_path=db_path)
        assert public["status"] == "ok"
        assert public["total_analyses"] >= 1
        assert public["privacy"]["raw_text_stored"] is False
        assert "Ambivalent" in public["dominant_states_distribution"]
    finally:
        stop_interaction_writer()
