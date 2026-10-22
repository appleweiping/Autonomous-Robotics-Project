"""Check how the survey nodes turn (simulated) sensor readings into task files."""

import json

import pytest
import rclpy

from agri_robots import navigator_node, repeated_navigator


@pytest.fixture
def ros():
    rclpy.init()
    yield
    rclpy.shutdown()


@pytest.fixture
def files(tmp_path, monkeypatch):
    anomalies = tmp_path / 'anomalies.json'
    seeding = tmp_path / 'seeding_points.json'
    for module in (navigator_node, repeated_navigator):
        monkeypatch.setattr(module, 'ANOMALY_FILE', str(anomalies))
        monkeypatch.setattr(module, 'SEEDING_FILE', str(seeding))
    return anomalies, seeding


def fake_reading(monkeypatch, ph, moisture):
    monkeypatch.setattr(navigator_node.random, 'uniform', lambda lo, hi: ph)
    monkeypatch.setattr(navigator_node.random, 'randint', lambda lo, hi: moisture)


def read(path):
    with open(path) as f:
        return json.load(f)


def test_node_creates_empty_task_files(ros, files):
    anomalies, seeding = files
    node = navigator_node.NavigatorNode()
    assert read(anomalies) == {'ph_anomalies': [], 'moisture_anomalies': []}
    assert read(seeding) == []
    node.destroy_node()


def test_acidic_and_dry_reading_is_logged_for_both_bots(ros, files, monkeypatch):
    anomalies, seeding = files
    node = navigator_node.NavigatorNode()
    fake_reading(monkeypatch, ph=4.2, moisture=12)
    node.simulate_sensor(1.33, 0.962)
    assert read(anomalies) == {
        'ph_anomalies': [{'x': 1.33, 'y': 0.962, 'ph': 4.2}],
        'moisture_anomalies': [{'x': 1.33, 'y': 0.962, 'moisture': 12}],
    }
    assert read(seeding) == []
    node.destroy_node()


def test_normal_wet_reading_becomes_a_seeding_point(ros, files, monkeypatch):
    anomalies, seeding = files
    node = navigator_node.NavigatorNode()
    fake_reading(monkeypatch, ph=6.5, moisture=90)
    node.simulate_sensor(0.0207, 0.505)
    assert read(anomalies) == {'ph_anomalies': [], 'moisture_anomalies': []}
    assert read(seeding) == [{'x': 0.0207, 'y': 0.505, 'moisture': 90}]
    node.destroy_node()


def test_repeated_navigator_works_without_existing_files(ros, files, monkeypatch):
    anomalies, seeding = files
    node = repeated_navigator.RepeatedNavigator()
    fake_reading(monkeypatch, ph=8.0, moisture=50)
    node.simulate_sensor(1.45, -0.0149)
    assert read(anomalies)['ph_anomalies'] == [{'x': 1.45, 'y': -0.0149, 'ph': 8.0}]
    node.destroy_node()
