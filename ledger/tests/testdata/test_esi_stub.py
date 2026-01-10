"""
Example tests demonstrating usage of the ESI OpenAPI stub system.
"""

# Standard Library
from unittest.mock import patch

# Third Party
# AA TaxSystem
# AA Taxsystem
from taxsystem.tests import NoSocketsTestCase
from taxsystem.tests.testdata.esi_stub_openapi import (
    EsiEndpoint,
    create_esi_client_stub,
)

# Alliance Auth
from esi.exceptions import HTTPClientError, HTTPNotModified, HTTPServerError

# Example test data configuration
EXAMPLE_TEST_DATA = {
    "Skills": {
        "GetCharactersCharacterIdSkills": {
            "skills": [
                {"skill_id": 12345, "trained_skill_level": 5, "active_skill_level": 5},
                {"skill_id": 67890, "trained_skill_level": 3, "active_skill_level": 3},
            ],
            "total_sp": 50000000,
            "unallocated_sp": 100000,
        },
        "GetCharactersCharacterIdSkillqueue": [
            {
                "skill_id": 11111,
                "finished_level": 4,
                "queue_position": 0,
                "finish_date": "2025-12-31T23:59:59Z",
                "start_date": "2025-12-01T00:00:00Z",
                "training_start_sp": 100000,
                "level_start_sp": 50000,
                "level_end_sp": 150000,
            },
            {
                "skill_id": 22222,
                "finished_level": 5,
                "queue_position": 1,
                "finish_date": "2026-01-15T12:00:00Z",
                "start_date": "2025-12-31T23:59:59Z",
                "training_start_sp": 200000,
                "level_start_sp": 150000,
                "level_end_sp": 300000,
            },
        ],
    },
    "Character": {
        "GetCharactersCharacterId": {
            "character_id": 12345678,
            "name": "Test Character",
            "corporation_id": 98765432,
            "birthday": "2015-03-24T11:37:00Z",
        },
    },
}

# Example endpoints for basic tests
EXAMPLE_ENDPOINTS = [
    EsiEndpoint("Character", "GetCharactersCharacterId", "character_id"),
    EsiEndpoint("Skills", "GetCharactersCharacterIdSkills", "character_id"),
    EsiEndpoint("Skills", "GetCharactersCharacterIdSkillqueue", "character_id"),
]


class TestEsiStubUsage(NoSocketsTestCase):
    """Example tests showing how to use the ESI stub system."""

    def test_should_return_single_result(self):
        """
        Test should return single result using result() method.
        """
        # Create a stub with example data and endpoints
        stub = create_esi_client_stub(EXAMPLE_TEST_DATA, endpoints=EXAMPLE_ENDPOINTS)
        # Simulate an ESI call that returns a single result
        operation = stub.Character.GetCharactersCharacterId(character_id=12345678)
        result = operation.result()
        # Verify the data - now using attributes instead of dict keys
        self.assertEqual(result.character_id, 12345678)
        self.assertEqual(result.name, "Test Character")
        self.assertEqual(result.corporation_id, 98765432)

    def test_should_return_list(self):
        """
        Test should return list of results using results() method.
        """
        # Create a stub with example data and endpoints
        stub = create_esi_client_stub(EXAMPLE_TEST_DATA, endpoints=EXAMPLE_ENDPOINTS)
        # Simulate an ESI call that returns a list of results
        operation = stub.Skills.GetCharactersCharacterIdSkillqueue(
            character_id=12345678
        )
        results = operation.results()
        # Verify the data - now using attributes
        self.assertIsInstance(results, list)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].skill_id, 11111)
        self.assertEqual(results[1].skill_id, 22222)

    def test_should_create_stub_with_custom_data(self):
        """
        Test should create stub with custom test data and return custom values.
        """
        # Define custom test data
        custom_data = {
            "Skills": {
                "GetCharactersCharacterIdSkills": {
                    "skills": [
                        {
                            "skill_id": 99999,
                            "trained_skill_level": 5,
                            "active_skill_level": 5,
                        }
                    ],
                    "total_sp": 1000000,
                    "unallocated_sp": 0,
                }
            }
        }
        # Define endpoints
        endpoints = [
            EsiEndpoint("Skills", "GetCharactersCharacterIdSkills", "character_id"),
        ]
        # Create stub with custom data and endpoints
        stub = create_esi_client_stub(custom_data, endpoints=endpoints)
        # Use the stub
        operation = stub.Skills.GetCharactersCharacterIdSkills(character_id=12345)
        result = operation.result()
        # Verify custom data is returned - using attributes
        self.assertEqual(result.total_sp, 1000000)
        self.assertEqual(len(result.skills), 1)
        self.assertEqual(result.skills[0].skill_id, 99999)

    @patch("taxsystem.providers.esi")
    def test_should_mock_esi(self, mock_esi):
        """
        Test should mock esi provider to return the stub client.
        """
        # Create a stub with endpoints
        stub = create_esi_client_stub(EXAMPLE_TEST_DATA, endpoints=EXAMPLE_ENDPOINTS)
        # Make mock.client return our stub
        type(mock_esi).client = property(lambda self: stub)
        # Now when code calls esi.client, it will get our stub - Verify it works
        self.assertEqual(mock_esi.client, stub)

    def test_should_handle_nested_data_structures(self):
        """
        Test should handle stub with nested data structures correctly.
        """
        # Create stub with example data and endpoints
        stub = create_esi_client_stub(EXAMPLE_TEST_DATA, endpoints=EXAMPLE_ENDPOINTS)
        # Simulate an ESI call that returns nested data
        operation = stub.Skills.GetCharactersCharacterIdSkills(character_id=12345)
        result = operation.result()
        # Verify nested structure - using attributes
        self.assertTrue(hasattr(result, "skills"))
        self.assertIsInstance(result.skills, list)
        self.assertEqual(result.skills[0].skill_id, 12345)

    def test_should_support_dynamic_callable_data(self):
        """
        Test should support callable/dynamic test data based on input parameters.
        """

        def dynamic_skill_data(**kwargs):
            """Return dynamic data based on skill_points parameter."""
            skill_points = kwargs.get("skill_points", 0)
            return {
                "total_sp": skill_points,  # SP based on input parameter
                "skills": [],
                "unallocated_sp": skill_points // 10,  # 10% unallocated
            }

        # Create stub with callable data - using a custom parameter
        custom_data = {
            "Skills": {
                "GetCharactersCharacterIdSkills": dynamic_skill_data,
            }
        }
        endpoints = [
            EsiEndpoint("Skills", "GetCharactersCharacterIdSkills", "skill_points"),
        ]
        stub = create_esi_client_stub(custom_data, endpoints=endpoints)
        # Call with different skill_points values
        op1 = stub.Skills.GetCharactersCharacterIdSkills(skill_points=1000000)
        result1 = op1.result()
        op2 = stub.Skills.GetCharactersCharacterIdSkills(skill_points=2000000)
        result2 = op2.result()
        # Verify dynamic data works - using attributes
        self.assertEqual(result1.total_sp, 1000000)
        self.assertEqual(result1.unallocated_sp, 100000)
        self.assertEqual(result2.total_sp, 2000000)
        self.assertEqual(result2.unallocated_sp, 200000)

    def test_should_raise_attribute_error_for_unregistered_method(self):
        """
        Test should raise AttributeError when calling unregistered method.
        """
        endpoints = [
            EsiEndpoint("Skills", "GetCharactersCharacterIdSkills", "character_id"),
        ]
        stub = create_esi_client_stub({"Skills": {}}, endpoints=endpoints)
        # Call a method that isn't registered should raise AttributeError
        with self.assertRaises(AttributeError) as context:
            stub.Skills.SomeUnconfiguredMethod(character_id=12345)
        self.assertIn("not registered", str(context.exception))

    def test_should_wrap_single_item_in_list(self):
        """
        Test should wrap single items in a list when using results() method.
        """
        custom_data = {
            "Test": {
                "SingleItemMethod": {"id": 1, "name": "single"},
            }
        }
        endpoints = [
            EsiEndpoint("Test", "SingleItemMethod", "id"),
        ]
        stub = create_esi_client_stub(custom_data, endpoints=endpoints)

        operation = stub.Test.SingleItemMethod()
        results = operation.results()

        # Single item should be wrapped in list - using attributes
        self.assertIsInstance(results, list)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].id, 1)

    def test_should_return_tuple_with_response_on_result(self):
        """
        Test should return tuple with data and response when return_response=True for result() method.
        """

        stub = create_esi_client_stub(EXAMPLE_TEST_DATA, endpoints=EXAMPLE_ENDPOINTS)

        operation = stub.Character.GetCharactersCharacterId(character_id=12345678)
        data, response = operation.result(return_response=True)

        self.assertEqual(data.character_id, 12345678)
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.headers, dict)

    def test_should_return_tuple_with_response_on_results(self):
        """
        Test should return tuple with list data and response for results() method.
        """

        stub = create_esi_client_stub(EXAMPLE_TEST_DATA, endpoints=EXAMPLE_ENDPOINTS)

        operation = stub.Skills.GetCharactersCharacterIdSkillqueue(
            character_id=12345678
        )
        data, response = operation.results(return_response=True)

        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 2)
        self.assertEqual(response.status_code, 200)

    def test_should_raise_http_not_modified_exception(self):
        """
        Test should raise HTTPNotModified exception via side_effect parameter.
        """
        # Define endpoints with side effects
        _endpoints = [
            EsiEndpoint(
                "Character",
                "GetCharactersCharacterId",
                "character_id",
                side_effect=HTTPNotModified(304, {}),
            ),
        ]
        test_data = {
            "Character": {
                "GetCharactersCharacterId": {"character_id": 12345, "name": "Test"}
            }
        }
        stub = create_esi_client_stub(test_data, endpoints=_endpoints)
        operation = stub.Character.GetCharactersCharacterId(character_id=12345)
        with self.assertRaises(HTTPNotModified):
            operation.result()

    def test_should_raise_http_client_error_exception(self):
        """
        Test should raise HTTPClientError exception via side_effect parameter.
        """
        _endpoints = [
            EsiEndpoint(
                "Skills",
                "GetCharactersCharacterIdSkills",
                "character_id",
                side_effect=HTTPClientError(404, {}, b"Not Found"),
            ),
        ]
        test_data = {
            "Skills": {"GetCharactersCharacterIdSkills": {"total_sp": 0, "skills": []}}
        }
        stub = create_esi_client_stub(test_data, endpoints=_endpoints)
        operation = stub.Skills.GetCharactersCharacterIdSkills(character_id=12345)
        with self.assertRaises(HTTPClientError):
            operation.result()

    def test_should_raise_http_server_error_exception(self):
        """
        Test should raise HTTPServerError exception via side_effect parameter.
        """
        _endpoints = [
            EsiEndpoint(
                "Skills",
                "GetCharactersCharacterIdSkillqueue",
                "character_id",
                side_effect=HTTPServerError(500, {}, b"Server Error"),
            ),
        ]
        test_data = {"Skills": {"GetCharactersCharacterIdSkillqueue": []}}
        stub = create_esi_client_stub(test_data, endpoints=_endpoints)
        operation = stub.Skills.GetCharactersCharacterIdSkillqueue(character_id=12345)
        with self.assertRaises(HTTPServerError):
            operation.results()

    def test_side_effect_os_error(self):
        """
        Test that OSError exception can be simulated via endpoints.
        """
        _endpoints = [
            EsiEndpoint(
                "Character",
                "GetCharactersCharacterId",
                "character_id",
                side_effect=OSError("Connection timeout"),
            ),
        ]

        test_data = {"Character": {"GetCharactersCharacterId": {"character_id": 12345}}}

        stub = create_esi_client_stub(test_data, endpoints=_endpoints)
        operation = stub.Character.GetCharactersCharacterId(character_id=12345)

        # Should raise OSError
        with self.assertRaises(OSError):
            operation.result()

    def test_endpoints_restrict_available_methods(self):
        """
        Test that only registered endpoints are available when endpoints are provided.
        """
        _endpoints = [
            EsiEndpoint(
                "Character",
                "GetCharactersCharacterId",
                "character_id",
            ),
        ]

        test_data = {
            "Character": {
                "GetCharactersCharacterId": {"character_id": 12345, "name": "Test"},
                "GetCharactersCharacterIdRoles": {"roles": []},  # Not registered
            }
        }

        stub = create_esi_client_stub(test_data, endpoints=_endpoints)

        # Registered endpoint should work
        operation = stub.Character.GetCharactersCharacterId(character_id=12345)
        result = operation.result()
        self.assertEqual(result.character_id, 12345)

        # Non-registered endpoint should raise AttributeError
        with self.assertRaises(AttributeError) as context:
            stub.Character.GetCharactersCharacterIdRoles(character_id=12345)

        self.assertIn("not registered", str(context.exception))

    def test_endpoints_restrict_available_categories(self):
        """
        Test that only categories with registered endpoints are available.
        """
        _endpoints = [
            EsiEndpoint(
                "Character",
                "GetCharactersCharacterId",
                "character_id",
            ),
        ]

        test_data = {
            "Character": {
                "GetCharactersCharacterId": {"character_id": 12345, "name": "Test"}
            },
            "Skills": {
                "GetCharactersCharacterIdSkills": {
                    "total_sp": 0
                }  # Category not registered
            },
        }

        stub = create_esi_client_stub(test_data, endpoints=_endpoints)

        # Registered category should work
        operation = stub.Character.GetCharactersCharacterId(character_id=12345)
        result = operation.result()
        self.assertEqual(result.name, "Test")

        # Non-registered category should raise AttributeError
        with self.assertRaises(AttributeError) as context:
            stub.Skills.GetCharactersCharacterIdSkills(character_id=12345)

        self.assertIn("not registered", str(context.exception))

    def test_endpoints_are_required(self):
        """
        Test that endpoints parameter is required.
        """
        test_data = {
            "Character": {
                "GetCharactersCharacterId": {"character_id": 12345, "name": "Test"}
            }
        }

        # Should raise ValueError when no endpoints provided
        with self.assertRaises(ValueError) as context:
            create_esi_client_stub(test_data)

        self.assertIn("endpoints parameter is required", str(context.exception))

    def test_multiple_endpoints_mixed(self):
        """
        Test multiple endpoints with and without side effects.
        """
        _endpoints = [
            EsiEndpoint(
                "Character",
                "GetCharactersCharacterId",
                "character_id",
                side_effect=HTTPNotModified(304, {}),
            ),
            EsiEndpoint(
                "Skills",
                "GetCharactersCharacterIdSkills",
                "character_id",
            ),
        ]

        test_data = {
            "Character": {"GetCharactersCharacterId": {"character_id": 12345}},
            "Skills": {
                "GetCharactersCharacterIdSkills": {"total_sp": 5000000, "skills": []}
            },
        }

        stub = create_esi_client_stub(test_data, endpoints=_endpoints)

        # Character endpoint should raise exception
        char_op = stub.Character.GetCharactersCharacterId(character_id=12345)
        with self.assertRaises(HTTPNotModified):
            char_op.result()

        # Skills endpoint should return normal data
        skills_op = stub.Skills.GetCharactersCharacterIdSkills(character_id=12345)
        skills_result = skills_op.result()
        self.assertEqual(skills_result.total_sp, 5000000)
