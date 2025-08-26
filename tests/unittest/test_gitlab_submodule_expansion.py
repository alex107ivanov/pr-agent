from unittest.mock import MagicMock, patch

import pytest

from pr_agent.git_providers.gitlab_provider import GitLabProvider


@pytest.fixture
def gitlab_provider():
    mock_gl = MagicMock()
    with patch('pr_agent.git_providers.gitlab_provider.gitlab.Gitlab', return_value=mock_gl), \
         patch('pr_agent.git_providers.gitlab_provider.get_settings') as settings_mock, \
         patch.object(GitLabProvider, '_set_merge_request'):
        settings_mock.return_value.get.side_effect = lambda key, default=None: {
            "GITLAB.URL": "https://gitlab.com",
            "GITLAB.PERSONAL_ACCESS_TOKEN": "token",
            "GITLAB.EXPAND_SUBMODULE_DIFFS": True,
        }.get(key, default)
        provider = GitLabProvider("https://gitlab.com/group/repo/-/merge_requests/1")
        provider.gl = mock_gl
        provider.id_project = "group/repo"
        return provider


def _base_change():
    return [{
        "new_path": "libs/sub",
        "diff": "-Subproject commit 1111111\n+Subproject commit 2222222",
    }]


def test_host_mismatch(gitlab_provider):
    proj = MagicMock()
    proj.path_with_namespace = "group/sub"
    proj.web_url = "https://gitlab.com/group/sub"
    changes = _base_change()
    with patch.object(gitlab_provider, '_get_gitmodules_map', return_value={"libs/sub": "https://evil.com/group/sub.git"}), \
         patch.object(gitlab_provider, '_project_by_path', return_value=proj), \
         patch.object(gitlab_provider, '_compare_submodule') as cmp_mock:
        result = gitlab_provider._expand_submodule_changes(changes)
    assert result == changes
    cmp_mock.assert_not_called()


def test_namespace_mismatch(gitlab_provider):
    proj = MagicMock()
    proj.path_with_namespace = "group/other"
    proj.web_url = "https://gitlab.com/group/other"
    changes = _base_change()
    with patch.object(gitlab_provider, '_get_gitmodules_map', return_value={"libs/sub": "https://gitlab.com/group/sub.git"}), \
         patch.object(gitlab_provider, '_project_by_path', return_value=proj), \
         patch.object(gitlab_provider, '_compare_submodule') as cmp_mock:
        result = gitlab_provider._expand_submodule_changes(changes)
    assert result == changes
    cmp_mock.assert_not_called()
