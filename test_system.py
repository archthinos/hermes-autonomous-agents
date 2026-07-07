#!/usr/bin/env python3
"""
System Test Script

Tests all components without requiring full deployment.
"""

import os
import sys

def test_imports():
    """Test that all modules can be imported."""
    print("Testing imports...")

    try:
        from autonomous import (
            Orchestrator,
            GoalGenerator,
            PriorityQueue,
            AgentCommunications,
            KnowledgeBase,
            NoveltyDetector
        )
        print("✓ All autonomous modules imported successfully")
        return True
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return False


def test_config():
    """Test configuration file loading."""
    print("\nTesting configuration...")

    import yaml
    try:
        with open('cron_config.yaml', 'r') as f:
            config = yaml.safe_load(f)

        agents = [k for k in config.keys() if k not in ['global', 'timezone', 'logging']]
        print(f"✓ Config loaded: {len(agents)} agents configured")

        for agent in agents:
            schedules = config[agent].get('schedules', [])
            if not schedules and config[agent].get('schedule'):
                schedules = [{'schedule': config[agent]['schedule']}]
            print(f"  - {agent}: {len(schedules)} schedule(s)")

        return True
    except Exception as e:
        print(f"✗ Config test failed: {e}")
        return False


def test_database_connection():
    """Test database connection (if DATABASE_URL set)."""
    print("\nTesting database connection...")

    if not os.getenv('DATABASE_URL'):
        print("⚠ DATABASE_URL not set, skipping database test")
        return True

    try:
        from autonomous.knowledge_base import KnowledgeBase

        kb = KnowledgeBase()
        stats = kb.get_stats()
        print(f"✓ Database connected: {stats}")
        kb.close()
        return True
    except Exception as e:
        print(f"✗ Database test failed: {e}")
        return False


def test_redis_connection():
    """Test Redis connection (if REDIS_URL set)."""
    print("\nTesting Redis connection...")

    if not os.getenv('REDIS_URL'):
        print("⚠ REDIS_URL not set, skipping Redis test")
        return True

    try:
        from autonomous.agent_comms import AgentCommunications

        comms = AgentCommunications()
        stats = comms.get_stats()
        print(f"✓ Redis connected: {stats}")
        comms.close()
        return True
    except Exception as e:
        print(f"✗ Redis test failed: {e}")
        return False


def test_agent_profiles():
    """Test that all agent profiles exist."""
    print("\nTesting agent profiles...")

    agents = [
        'orchestrator',
        'ai_researcher',
        'software_dev',
        'crypto_agent',
        'productivity',
        'social_monitor',
        'web_researcher'
    ]

    all_good = True
    for agent in agents:
        path = f'agents/{agent}'
        files = ['SOUL.md', 'config.yaml', 'MEMORY.md', 'USER.md']

        missing = []
        for f in files:
            if not os.path.exists(f'{path}/{f}'):
                missing.append(f)

        if missing:
            print(f"✗ {agent}: missing {', '.join(missing)}")
            all_good = False
        else:
            print(f"✓ {agent}: all files present")

    return all_good


def test_skills():
    """Test that all skills exist."""
    print("\nTesting skills...")

    skills = [
        'ai-news-aggregator.md',
        'github-trending-analyzer.md',
        'crypto-market-digest.md',
        'productivity-daily-review.md',
        'tech-news-synthesizer.md'
    ]

    all_good = True
    for skill in skills:
        path = f'skills/{skill}'
        if os.path.exists(path):
            size = os.path.getsize(path)
            print(f"✓ {skill}: {size} bytes")
        else:
            print(f"✗ {skill}: not found")
            all_good = False

    return all_good


def test_docker():
    """Test Docker configuration."""
    print("\nTesting Docker configuration...")

    files = ['Dockerfile', 'docker-entrypoint.sh', 'requirements.txt']

    all_good = True
    for f in files:
        if os.path.exists(f):
            size = os.path.getsize(f)
            print(f"✓ {f}: {size} bytes")
        else:
            print(f"✗ {f}: not found")
            all_good = False

    return all_good


def run_all_tests():
    """Run all tests."""
    print("=" * 60)
    print("HERMES AUTONOMOUS AGENT SYSTEM - SYSTEM TEST")
    print("=" * 60)

    tests = [
        ("Imports", test_imports),
        ("Configuration", test_config),
        ("Database", test_database_connection),
        ("Redis", test_redis_connection),
        ("Agent Profiles", test_agent_profiles),
        ("Skills", test_skills),
        ("Docker", test_docker)
    ]

    results = []

    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n✗ {name} test crashed: {e}")
            results.append((name, False))

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, r in results if r)
    total = len(results)

    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status} - {name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed! System is ready for deployment.")
        return 0
    else:
        print(f"\n⚠ {total - passed} test(s) failed. Fix issues before deploying.")
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
