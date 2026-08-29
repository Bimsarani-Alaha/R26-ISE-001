import io

from rich.console import Console

from app.services.terminal_progress import PipelineProgress, new_request_id


def make_console() -> Console:
    return Console(file=io.StringIO(), width=120, legacy_windows=False)


def test_new_request_id_is_8_hex_chars():
    rid = new_request_id()
    assert len(rid) == 8
    int(rid, 16)


def test_stage_sets_description_and_advances_bar():
    progress = PipelineProgress("Rec test1", total_stages=3, console=make_console())
    with progress.stage("Analyzing requirements"):
        pass
    task = progress._progress.tasks[0]
    assert progress.history == ["Analyzing requirements"]
    assert task.completed == 1
    assert "Analyzing requirements" in task.description
    progress.close()


def test_stage_does_not_advance_on_exception():
    progress = PipelineProgress("Rec test2", total_stages=2, console=make_console())
    try:
        with progress.stage("Analyzing"):
            raise ValueError("boom")
    except ValueError:
        pass
    task = progress._progress.tasks[0]
    assert task.completed == 0
    progress.close()


def test_finish_completes_all_stages_and_is_idempotent():
    progress = PipelineProgress("Rec test3", total_stages=2, console=make_console())
    with progress.stage("A"):
        pass
    with progress.stage("B"):
        pass
    progress.finish()
    progress.finish()
    task = progress._progress.tasks[0]
    assert task.finished
    assert task.completed == 2
    assert "Done" in task.description
    progress.close()


def test_fail_marks_row_failed_and_is_idempotent():
    progress = PipelineProgress("Rec test4", total_stages=3, console=make_console())
    try:
        with progress.stage("A"):
            raise RuntimeError("llm down")
    except RuntimeError:
        progress.fail()
    progress.fail()
    task = progress._progress.tasks[0]
    assert "Failed" in task.description
    assert task.completed == 0
    progress.close()


def test_rows_track_tasks_independently():
    # Note: each instance gets its OWN console — rich permits only one
    # live display per console at a time.
    p1 = PipelineProgress("Rec aaa", total_stages=1, console=make_console())
    p2 = PipelineProgress("Stylist bbb", total_stages=2, console=make_console())
    with p1.stage("Only stage"):
        pass
    with p2.stage("First"):
        pass
    assert p1._progress.tasks[0].completed == 1
    assert p2._progress.tasks[0].completed == 1
    assert p1.history == ["Only stage"]
    assert p2.history == ["First"]
    p1.close()
    p2.close()
