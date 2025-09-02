import os
import sys
import asyncio
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from pr_agent.tools.ticket_pr_compliance_check import extract_tickets
from pr_agent.config_loader import get_settings


class DummyProvider:
    """Minimal git provider with PR description."""

    def get_user_description(self):
        return "Implements https://jira.example.com/browse/PROJ-123"


def test_extract_tickets_from_jira():
    settings = get_settings()
    settings.set('jira', {
        'jira_api_email': 'user@example.com',
        'jira_api_token': 'secret',
    })

    issue_data = {
        'fields': {
            'summary': 'Test issue',
            'description': 'Issue body',
            'labels': ['bug', 'urgent'],
        }
    }

    mock_jira = MagicMock()
    mock_jira.issue.return_value = issue_data

    async def run():
        with patch('pr_agent.tools.ticket_pr_compliance_check.Jira', return_value=mock_jira):
            result = await extract_tickets(DummyProvider())
        assert result
        ticket = result[0]
        assert ticket['ticket_id'] == 'PROJ-123'
        assert ticket['title'] == 'Test issue'
        assert ticket['body'] == 'Issue body'
        assert 'bug' in ticket['labels']

    asyncio.run(run())

