"""Tests for data models."""

import pytest
from datetime import datetime
from models import Repository, PullRequest, JiraTicket, Feature


def test_repository_creation():
    """Test Repository model creation."""
    repo = Repository(name="installer", owner="openshift")
    assert repo.name == "installer"
    assert repo.owner == "openshift"


def test_pull_request_creation():
    """Test PullRequest model creation."""
    pr = PullRequest(
        id=12345,
        number=100,
        title="Add new feature",
        description="This is a test PR",
        merged_at=datetime.now(),
        files_changed=[],
        jira_id="JIRA-123"
    )
    assert pr.number == 100
    assert pr.jira_id == "JIRA-123"
    assert isinstance(pr.files_changed, list)


def test_jira_ticket_creation():
    """Test JiraTicket model creation."""
    ticket = JiraTicket(
        id="10001",
        key="JIRA-123",
        title="Implement feature X",
        description="Detailed description",
        acceptance_criteria="Must do X, Y, Z",
        comments=["Comment 1", "Comment 2"]
    )
    assert ticket.key == "JIRA-123"
    assert len(ticket.comments) == 2


def test_feature_creation():
    """Test Feature model creation."""
    pr = PullRequest(
        id=1,
        number=1,
        title="Test",
        description="Test PR",
        merged_at=None,
        files_changed=[]
    )

    jira = JiraTicket(
        id="1",
        key="TEST-1",
        title="Test",
        description="Test ticket",
        acceptance_criteria="",
        comments=[]
    )

    feature = Feature(
        pr=pr,
        jira=jira,
        summary_context={"test": "data"}
    )

    assert feature.pr.number == 1
    assert feature.jira.key == "TEST-1"
    assert "test" in feature.summary_context
