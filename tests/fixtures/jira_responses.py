"""Fixtures for Jira API responses."""

# Sample Jira API responses for testing
SAMPLE_PROJECT_RESPONSE = {
    "id": "10000",
    "key": "DEMO",
    "name": "Demo Project",
    "projectTypeKey": "software"
}

SAMPLE_ISSUE_TYPES_RESPONSE = {
    "projects": [{
        "id": "10000", 
        "key": "DEMO",
        "issuetypes": [
            {
                "id": "10001",
                "name": "Story",
                "subtask": False
            },
            {
                "id": "10002", 
                "name": "Subtarea",
                "subtask": True
            },
            {
                "id": "10003",
                "name": "Feature", 
                "subtask": False
            }
        ]
    }]
}

SAMPLE_CREATE_ISSUE_RESPONSE = {
    "id": "10001",
    "key": "DEMO-123",
    "self": "https://demo.atlassian.net/rest/api/3/issue/10001"
}

SAMPLE_ISSUE_RESPONSE = {
    "id": "10001",
    "key": "DEMO-123",
    "fields": {
        "summary": "Test Story",
        "description": {
            "type": "doc",
            "version": 1,
            "content": [{
                "type": "paragraph",
                "content": [{"type": "text", "text": "Test description"}]
            }]
        },
        "issuetype": {"name": "Story"},
        "project": {"key": "DEMO"}
    }
}

SAMPLE_MYSELF_RESPONSE = {
    "self": "https://demo.atlassian.net/rest/api/3/user?accountId=123",
    "accountId": "123",
    "emailAddress": "test@example.com",
    "displayName": "Test User"
}

SAMPLE_FEATURE_FIELDS_RESPONSE = {
    "projects": [{
        "id": "10000",
        "key": "DEMO", 
        "issuetypes": [{
            "id": "10003",
            "name": "Feature",
            "fields": {
                "summary": {"required": True, "name": "Summary"},
                "description": {"required": False, "name": "Description"},
                "project": {"required": True, "name": "Project"},
                "issuetype": {"required": True, "name": "Issue Type"},
                "customfield_10001": {
                    "required": True,
                    "name": "Epic Name",
                    "custom": True
                },
                "customfield_10002": {
                    "required": True,
                    "name": "Priority",
                    "allowedValues": [
                        {"id": "1", "value": "High"},
                        {"id": "2", "value": "Medium"},
                        {"id": "3", "value": "Low"}
                    ]
                }
            }
        }]
    }]
}