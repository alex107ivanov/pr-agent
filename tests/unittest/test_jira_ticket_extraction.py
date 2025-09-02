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


def test_extract_tickets_from_jira_token_auth():
    settings = get_settings()
    settings.set('jira', {})
    settings.set('jira', {
        'jira_token': 'secret',
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
        with patch('pr_agent.tools.ticket_pr_compliance_check.Jira', return_value=mock_jira) as jira_cls:
            result = await extract_tickets(DummyProvider())
            jira_cls.assert_called_with(
                url='https://jira.example.com',
                token='secret',
                verify_ssl=True,
            )
        assert result
        ticket = result[0]
        assert ticket['ticket_id'] == 'PROJ-123'
        assert ticket['title'] == 'Test issue'
        assert ticket['body'] == 'Issue body'
        assert 'bug' in ticket['labels']

    asyncio.run(run())


def test_extract_tickets_from_jira_user_password_self_signed():
    settings = get_settings()
    settings.set('jira', {})
    settings.set('jira', {
        'jira_user': 'user@example.com',
        'jira_password': 'secret',
        'jira_allow_self_signed': True,
        'jira_token': '',
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
        with patch('pr_agent.tools.ticket_pr_compliance_check.Jira', return_value=mock_jira) as jira_cls:
            await extract_tickets(DummyProvider())
            jira_cls.assert_called_with(
                url='https://jira.example.com',
                username='user@example.com',
                password='secret',
                verify_ssl=False,
            )

    asyncio.run(run())

