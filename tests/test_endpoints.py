import pytest
from starlette.testclient import TestClient
from main import app
from unittest.mock import patch, MagicMock
from settings import S3_LINK

class TestStories:

    @pytest.mark.asyncio
    async def test_get_story(self):
        """
        Test the '/story' endpoint for successful response and content.

        - Mocks the database response with a single instance of MockStory.
        - Verifies that the endpoint returns a 200 status code.
        - Validates the correctness of the JSON response content.
        """

        client = TestClient(app)

        class MockStory:
            pass

        async def mock_filter(*args, **kwargs):
            return [MockStory()]

        # Mock the database dependency
        with patch('database.models.Story',
                   **{'return_value.filter.side_effect': mock_filter}), \
                patch(
                    'database.models.Story_Pydantic.from_queryset') as mock_from_queryset:
            mock_instance = MagicMock(title="Test Title",
                                      description="Test Description",
                                      author="Test Author",
                                      patreonusername="Test Patreon")
            mock_from_queryset.return_value = [mock_instance]

            response = client.get("/story?storyGlobalId=test")

            assert response.status_code == 200

            expected_response = {
                "isFound": True,
                "title": "Test Title",
                "description": "Test Description",
                "author": "Test Author",
                "patreonusername": "Test Patreon",
                "cdn": S3_LINK,  # Replace with the expected CDN value
            }
            assert response.json() == expected_response
