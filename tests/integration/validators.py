"""
Custom validators for Tavern integration tests.

This module provides custom validation functions for testing API responses
that require more complex validation than Tavern's built-in capabilities.
"""


def validate_exact_text(response, expected_text):
    import json

    # Get response body as text
    if hasattr(response, "text"):
        body_text = response.text
    elif hasattr(response, "content"):
        body_text = (
            response.content.decode("utf-8")
            if isinstance(response.content, bytes)
            else str(response.content)
        )
    else:
        body_text = str(response)

    # For SSE responses, extract and combine all text content
    combined_text = ""
    sse_lines = body_text.split("\n")

    for line in sse_lines:
        if line.startswith("data: ") and line != "data: [DONE]":
            try:
                # Remove 'data: ' prefix and parse JSON
                json_data = json.loads(line[6:])  # Remove 'data: ' (6 chars)
                if answer := json_data.get("answer"):
                    combined_text += str(answer)
                elif (
                    json_data.get("type") in ["text", "content"]
                    and "content" in json_data
                ):
                    combined_text += json_data["content"]
            except (json.JSONDecodeError, KeyError):
                # Skip lines that aren't valid JSON or don't have expected
                # structure
                continue

    # Check if expected text is contained in the combined text or raw response
    if expected_text in combined_text:
        return True

    raise AssertionError(
        f"Expected text '{expected_text}' not found in response. "
        f"Combined text from SSE chunks: '{combined_text}' "
        f"Raw response body: {body_text[:500]}..."  # Show first 500 chars
    )


def validate_users_list_contains_admin(response):
    """
    Validate that the users list response contains an admin user.

    Args:
        response: HTTP response object

    Returns:
        True if validation passes

    Raises:
        AssertionError: If admin user not found or has wrong role
    """
    import json

    # Parse JSON response
    if hasattr(response, "json"):
        users = response.json()
    else:
        users = json.loads(response.text)

    # Check that response is a list
    if not isinstance(users, list):
        raise AssertionError(f"Expected list, got {type(users)}")

    # Find admin user
    admin_user = None
    for user in users:
        if user.get("username") == "admin" and user.get("email") == "admin@example.com":
            admin_user = user
            break

    # Validate admin user exists
    if not admin_user:
        usernames = [u.get("username") for u in users]
        raise AssertionError(f"Admin user not found. Available users: {usernames}")

    # Validate admin user has admin role
    if admin_user.get("role") != "admin":
        raise AssertionError(
            f"Admin user has role '{admin_user.get('role')}', expected 'admin'"
        )

    return True


def parse_sse_response(response_text: str) -> dict:
    """
    Parse Server-Sent Events response text and extract JSON data.

    Args:
        response_text: Raw SSE response text

    Returns:
        Dict containing parsed SSE data with response_id, content, etc.

    Raises:
        ValueError: If no valid JSON data found in SSE stream
    """
    import json

    lines = response_text.strip().split("\n")
    json_data = {}

    for line in lines:
        line = line.strip()
        if line.startswith("data: "):
            data_content = line[6:]  # Remove "data: " prefix

            # Skip [DONE] marker
            if data_content == "[DONE]":
                continue

            try:
                parsed = json.loads(data_content)
                # Collect all data from the stream
                json_data.update(parsed)

                # If we find a response_id, prioritize it
                if "response_id" in parsed:
                    json_data["response_id"] = parsed["response_id"]

            except json.JSONDecodeError:
                # Skip non-JSON lines
                continue

    if not json_data:
        raise ValueError("No valid JSON data found in SSE response")

    return json_data


def validate_sse_response_id(response):
    """
    Validate that SSE response contains a valid response_id and content.

    This validator checks for successful chat responses that should contain
    both a response_id (for chaining) and content (the actual response).

    Args:
        response: Tavern response object

    Returns:
        bool: True if validation passes

    Raises:
        AssertionError: If validation fails
    """
    try:
        response_data = parse_sse_response(response.text)

        # Check for response_id
        assert "response_id" in response_data, "Response missing 'response_id' field"
        assert response_data["response_id"], "Response ID is empty"
        assert response_data["response_id"].startswith(
            "resp-"
        ), f"Invalid response ID format: {response_data['response_id']}"

        # Check for content (successful response)
        assert "content" in response_data, "Response missing 'content' field"
        assert response_data["content"], "Response content is empty"

        # Ensure it's not an error response
        assert (
            "type" not in response_data or response_data["type"] != "error"
        ), f"Unexpected error in response: {response_data.get('content', 'Unknown error')}"

        print(f"✓ Valid response with ID: {response_data['response_id']}")
        return True

    except Exception as e:
        print(f"✗ Response validation failed: {str(e)}")
        print(f"Response text: {response.text[:500]}...")
        raise


def validate_sse_error(response, expected_error: str):
    """
    Validate that SSE response contains the expected error message.

    This validator checks for error responses that should contain specific
    error messages, such as "Response with id X not found".

    Args:
        response: Tavern response object
        expected_error: Expected error message substring

    Returns:
        bool: True if validation passes

    Raises:
        AssertionError: If validation fails
    """
    try:
        response_text = response.text

        # Check that the expected error message is present
        assert (
            expected_error in response_text
        ), f"Expected error '{expected_error}' not found in response: {response_text}"

        # Parse JSON if possible to get structured error
        try:
            response_data = parse_sse_response(response_text)

            # Check for error type
            if "type" in response_data:
                assert (
                    response_data["type"] == "error"
                ), f"Expected error type, got: {response_data['type']}"

            print(f"✓ Expected error found: {expected_error}")

        except ValueError:
            # If we can't parse JSON, just check that error text is present
            print(f"✓ Expected error found in text: {expected_error}")

        return True

    except Exception as e:
        print(f"✗ Error validation failed: {str(e)}")
        print(f"Response text: {response.text[:500]}...")
        raise


def validate_stored_responses_list(response, expected_count: int = None):
    """
    Validate that responses list API returns expected structure and count.

    Args:
        response: Tavern response object
        expected_count: Expected number of responses in the list

    Returns:
        bool: True if validation passes

    Raises:
        AssertionError: If validation fails
    """
    try:
        # Parse JSON response
        if hasattr(response, "json"):
            data = response.json()
        else:
            import json

            data = json.loads(response.text)

        # Check that data field exists
        assert "data" in data, "Response missing 'data' field"
        responses = data["data"]

        # Check count if specified
        if expected_count is not None:
            assert (
                len(responses) >= expected_count
            ), f"Expected at least {expected_count} responses, got {len(responses)}"

        # Validate response structure
        for i, resp in enumerate(responses):
            assert "id" in resp, f"Response {i} missing 'id' field"
            assert resp["id"].startswith(
                "resp-"
            ), f"Response {i} has invalid ID format: {resp['id']}"

        print(f"✓ Stored responses validation passed: {len(responses)} responses")
        return True

    except Exception as e:
        print(f"✗ Stored responses validation failed: {str(e)}")
        print(f"Response text: {response.text[:500]}...")
        raise


def validate_session_messages(
    response,
    expected_message_count: int = None,
    expected_user_messages: list = None,
    expected_first_message: str = None,
):
    """
    Validate session messages response structure and content.

    This validator checks that session messages are properly formatted and
    contain the expected content for session switching tests.

    Args:
        response: Tavern response object
        expected_message_count: Expected number of messages in response
        expected_user_messages: List of expected user message texts
        expected_first_message: Expected text of the first message

    Returns:
        bool: True if validation passes

    Raises:
        AssertionError: If validation fails
    """
    try:
        # Parse JSON response
        if hasattr(response, "json"):
            session_data = response.json()
        else:
            import json

            session_data = json.loads(response.text)

        # Check that messages field exists
        assert "messages" in session_data, "Response missing 'messages' field"
        messages = session_data["messages"]

        # Check message count if specified
        if expected_message_count is not None:
            assert (
                len(messages) == expected_message_count
            ), f"Expected {expected_message_count} messages, got {len(messages)}"

        # Check specific user messages if specified
        if expected_user_messages:
            user_messages = [msg for msg in messages if msg.get("role") == "user"]
            user_texts = []
            for msg in user_messages:
                for content_item in msg.get("content", []):
                    if content_item.get("type") == "input_text":
                        user_texts.append(content_item.get("text", ""))

            for expected_text in expected_user_messages:
                assert (
                    expected_text in user_texts
                ), f"Expected user message '{expected_text}' not found in {user_texts}"

        # Check first message if specified
        if expected_first_message and messages:
            first_message = messages[0]
            if first_message.get("role") == "user":
                first_text = ""
                for content_item in first_message.get("content", []):
                    if content_item.get("type") == "input_text":
                        first_text = content_item.get("text", "")
                        break
                assert (
                    first_text == expected_first_message
                ), f"Expected first message '{expected_first_message}', got '{first_text}'"

        # Validate message structure
        for i, msg in enumerate(messages):
            assert "role" in msg, f"Message {i} missing 'role' field"
            assert "content" in msg, f"Message {i} missing 'content' field"
            assert isinstance(
                msg["content"], list
            ), f"Message {i} content must be a list"

            for j, content_item in enumerate(msg["content"]):
                assert (
                    "type" in content_item
                ), f"Message {i} content item {j} missing 'type' field"
                if content_item["type"] == "text":
                    assert (
                        "text" in content_item
                    ), f"Message {i} content item {j} missing 'text' field"
                elif content_item["type"] == "image":
                    assert (
                        "image" in content_item
                    ), f"Message {i} content item {j} missing 'image' field"

        print(f"✓ Session messages validation passed: {len(messages)} messages")
        return True

    except Exception as e:
        print(f"✗ Session messages validation failed: {str(e)}")
        print(f"Response text: {response.text[:500]}...")
        raise


def validate_message_chronological_order(response, expected_sequence: list):
    """
    Validate that messages appear in the correct chronological order.

    Args:
        response: Tavern response object
        expected_sequence: List of expected message texts in chronological order
                          Format: ["user_msg1", "assistant_msg1", "user_msg2", "assistant_msg2"]

    Returns:
        bool: True if validation passes

    Raises:
        AssertionError: If validation fails
    """
    try:
        # Parse response data
        if hasattr(response, "json"):
            session_data = response.json()
        else:
            import json

            session_data = json.loads(response.text)

        # Check that messages field exists
        assert "messages" in session_data, "Response missing 'messages' field"
        messages = session_data["messages"]

        # Extract all message texts in order
        actual_sequence = []
        for msg in messages:
            for content_item in msg.get("content", []):
                if content_item.get("type") in ["input_text", "output_text"]:
                    actual_sequence.append(content_item.get("text", ""))

        # Check that we have the expected number of messages
        assert len(actual_sequence) == len(
            expected_sequence
        ), f"Expected {len(expected_sequence)} messages, got {len(actual_sequence)}"

        # Check each message in order
        for i, (actual, expected) in enumerate(zip(actual_sequence, expected_sequence)):
            assert (
                actual == expected
            ), f"Message {i+1}: expected '{expected}', got '{actual}'"

        print(
            f"✓ Message chronological order validation passed: {len(actual_sequence)} messages in correct order"
        )
        return True

    except Exception as e:
        print(f"✗ Message chronological order validation failed: {str(e)}")
        print(f"Response text: {response.text[:500]}...")
        raise


def extract_response_id(response) -> dict:
    """
    Extract response_id from SSE response for use in subsequent requests.

    This function is used with Tavern's $ext mechanism to save response IDs
    that can be referenced in later test stages.

    Args:
        response: Tavern response object

    Returns:
        Dict with response_id key for Tavern to save

    Raises:
        ValueError: If no response_id found
    """
    try:
        response_data = parse_sse_response(response.text)

        if "response_id" not in response_data:
            raise ValueError("No response_id found in SSE response")

        response_id = response_data["response_id"]
        print(f"✓ Extracted response ID: {response_id}")

        return {"response_id": response_id}

    except Exception as e:
        print(f"✗ Failed to extract response ID: {str(e)}")
        print(f"Response text: {response.text[:500]}...")
        raise


def validate_list_not_empty(response):
    """
    Validate that the response contains a non-empty list.

    Args:
        response: Tavern response object

    Returns:
        bool: True if validation passes

    Raises:
        AssertionError: If validation fails
    """
    try:
        if hasattr(response, "json"):
            data = response.json()
        else:
            import json

            data = json.loads(response.text)

        assert isinstance(data, list), f"Expected list, got {type(data)}"
        assert len(data) > 0, "Expected non-empty list"

        print(f"✓ List validation passed: {len(data)} items")
        return True

    except Exception as e:
        print(f"✗ List validation failed: {str(e)}")
        print(f"Response text: {response.text[:500]}...")
        raise


def validate_agent_has_template_metadata(
    response, agent_id: str, expected_template_id: str
):
    """
    Validate that an agent in the list has correct template metadata.

    Args:
        response: Tavern response object
        agent_id: ID of the agent to check
        expected_template_id: Expected template ID

    Returns:
        bool: True if validation passes

    Raises:
        AssertionError: If validation fails
    """
    try:
        if hasattr(response, "json"):
            agents = response.json()
        else:
            import json

            agents = json.loads(response.text)

        # Find the agent
        target_agent = None
        for agent in agents:
            if agent.get("id") == agent_id:
                target_agent = agent
                break

        assert target_agent is not None, f"Agent {agent_id} not found in response"

        # Check template metadata
        assert (
            target_agent.get("template_id") == expected_template_id
        ), f"Expected template_id {expected_template_id}, got {target_agent.get('template_id')}"

        assert (
            target_agent.get("template_name") is not None
        ), "template_name should not be null"
        assert target_agent.get("suite_id") is not None, "suite_id should not be null"
        assert (
            target_agent.get("suite_name") is not None
        ), "suite_name should not be null"
        assert target_agent.get("category") is not None, "category should not be null"

        print(f"✓ Agent template metadata validation passed for {agent_id}")
        return True

    except Exception as e:
        print(f"✗ Agent template metadata validation failed: {str(e)}")
        print(f"Response text: {response.text[:500]}...")
        raise


def validate_suite_deployment_results(response, expected_count: int):
    """
    Validate that suite deployment results contain expected number of agents.

    Args:
        response: Tavern response object
        expected_count: Expected number of deployment results

    Returns:
        bool: True if validation passes

    Raises:
        AssertionError: If validation fails
    """
    try:
        if hasattr(response, "json"):
            results = response.json()
        else:
            import json

            results = json.loads(response.text)

        assert isinstance(results, list), f"Expected list, got {type(results)}"
        assert len(results) == int(
            expected_count
        ), f"Expected {expected_count} deployment results, got {len(results)}"

        # Check that each result has required fields
        for i, result in enumerate(results):
            assert "status" in result, f"Result {i} missing status"
            assert "agent_name" in result, f"Result {i} missing agent_name"
            assert result["status"] in [
                "success",
                "skipped",
                "error",
            ], f"Result {i} has invalid status: {result['status']}"

        success_count = sum(1 for r in results if r["status"] == "success")
        print(
            f"✓ Suite deployment validation passed: {success_count}/{len(results)} successful"
        )
        return True

    except Exception as e:
        print(f"✗ Suite deployment validation failed: {str(e)}")
        print(f"Response text: {response.text[:500]}...")
        raise


def validate_agents_grouped_by_suite(response, expected_suite_id: str):
    """
    Validate that agents are properly grouped by suite.

    Args:
        response: Tavern response object
        expected_suite_id: Expected suite ID to find agents for

    Returns:
        bool: True if validation passes

    Raises:
        AssertionError: If validation fails
    """
    try:
        if hasattr(response, "json"):
            agents = response.json()
        else:
            import json

            agents = json.loads(response.text)

        # Find agents with the expected suite_id
        suite_agents = [
            agent for agent in agents if agent.get("suite_id") == expected_suite_id
        ]

        assert (
            len(suite_agents) > 0
        ), f"No agents found with suite_id {expected_suite_id}"

        # Check that all agents in this suite have consistent metadata
        for agent in suite_agents:
            assert (
                agent.get("suite_id") == expected_suite_id
            ), f"Agent {agent.get('id')} has incorrect suite_id"
            assert (
                agent.get("suite_name") is not None
            ), f"Agent {agent.get('id')} missing suite_name"
            assert (
                agent.get("category") is not None
            ), f"Agent {agent.get('id')} missing category"

        print(
            f"✓ Suite grouping validation passed: {len(suite_agents)} agents in suite {expected_suite_id}"
        )
        return True

    except Exception as e:
        print(f"✗ Suite grouping validation failed: {str(e)}")
        print(f"Response text: {response.text[:500]}...")
        raise


def validate_categories_structure(response):
    """
    Validate that suites by category response has correct structure.

    Args:
        response: Tavern response object

    Returns:
        bool: True if validation passes

    Raises:
        AssertionError: If validation fails
    """
    try:
        if hasattr(response, "json"):
            categories = response.json()
        else:
            import json

            categories = json.loads(response.text)

        assert isinstance(categories, dict), f"Expected dict, got {type(categories)}"

        # Each category should have a list of suite IDs
        for category, suite_ids in categories.items():
            assert isinstance(
                suite_ids, list
            ), f"Category {category} should have list of suite IDs, got {type(suite_ids)}"
            assert len(suite_ids) > 0, f"Category {category} has no suites"

        print(f"✓ Categories structure validation passed: {len(categories)} categories")
        return True

    except Exception as e:
        print(f"✗ Categories structure validation failed: {str(e)}")
        print(f"Response text: {response.text[:500]}...")
        raise


def validate_categories_info_structure(response):
    """
    Validate that categories info response has correct structure.

    Args:
        response: Tavern response object

    Returns:
        bool: True if validation passes

    Raises:
        AssertionError: If validation fails
    """
    try:
        if hasattr(response, "json"):
            categories_info = response.json()
        else:
            import json

            categories_info = json.loads(response.text)

        assert isinstance(
            categories_info, dict
        ), f"Expected dict, got {type(categories_info)}"

        # Each category should have name, description, icon, suite_count
        for category, info in categories_info.items():
            assert isinstance(
                info, dict
            ), f"Category {category} info should be dict, got {type(info)}"

            required_fields = ["name", "description", "icon", "suite_count"]
            for field in required_fields:
                assert field in info, f"Category {category} missing field {field}"

            assert isinstance(
                info["suite_count"], int
            ), f"Category {category} suite_count should be int, got {type(info['suite_count'])}"
            assert (
                info["suite_count"] > 0
            ), f"Category {category} should have positive suite_count"

        print(
            f"✓ Categories info structure validation passed: {len(categories_info)} categories"
        )
        return True

    except Exception as e:
        print(f"✗ Categories info structure validation failed: {str(e)}")
        print(f"Response text: {response.text[:500]}...")
        raise


def validate_template_demo_questions(response):
    """
    Validate that template demo questions are properly structured and meaningful.

    Args:
        response: Tavern response object

    Returns:
        bool: True if validation passes

    Raises:
        AssertionError: If validation fails
    """
    try:
        if hasattr(response, "json"):
            template = response.json()
        else:
            import json

            template = json.loads(response.text)

        # Check that demo_questions exists
        assert "demo_questions" in template, "Template missing demo_questions field"

        demo_questions = template["demo_questions"]

        # Demo questions can be None or a list
        if demo_questions is not None:
            assert isinstance(
                demo_questions, list
            ), f"demo_questions should be list or None, got {type(demo_questions)}"

            if len(demo_questions) > 0:
                # Each demo question should be a non-empty string
                for i, question in enumerate(demo_questions):
                    assert isinstance(
                        question, str
                    ), f"Demo question {i} should be string, got {type(question)}"
                    assert (
                        len(question.strip()) > 0
                    ), f"Demo question {i} should not be empty"
                    assert question.endswith(
                        "?"
                    ), f"Demo question {i} should end with question mark: '{question}'"
                    assert (
                        len(question) > 10
                    ), f"Demo question {i} should be meaningful (>10 chars): '{question}'"

                print(
                    f"✓ Demo questions validation passed: {len(demo_questions)} questions"
                )
            else:
                print("✓ Demo questions validation passed: empty list (acceptable)")
        else:
            print("✓ Demo questions validation passed: None (acceptable)")

        return True

    except Exception as e:
        print(f"✗ Demo questions validation failed: {str(e)}")
        print(f"Response text: {response.text[:500]}...")
        raise


def validate_template_agent_exists(response, template_id: str, agent_name: str):
    """
    Validate that an agent with the given template_id and name exists in the list.

    This is used when deployment may return "skipped" status but we still want to
    verify the agent exists with proper template metadata.

    Args:
        response: Tavern response object
        template_id: Expected template ID
        agent_name: Expected agent name

    Returns:
        bool: True if validation passes

    Raises:
        AssertionError: If validation fails
    """
    try:
        if hasattr(response, "json"):
            agents = response.json()
        else:
            import json

            agents = json.loads(response.text)

        # Find the agent with matching template_id and name
        target_agent = None
        for agent in agents:
            if (
                agent.get("template_id") == template_id
                and agent.get("name") == agent_name
            ):
                target_agent = agent
                break

        assert (
            target_agent is not None
        ), f"Agent with template_id '{template_id}' and name '{agent_name}' not found"

        # Validate template metadata
        assert (
            target_agent.get("template_id") == template_id
        ), f"Expected template_id {template_id}, got {target_agent.get('template_id')}"

        assert (
            target_agent.get("template_name") is not None
        ), "template_name should not be null"
        assert target_agent.get("suite_id") is not None, "suite_id should not be null"
        assert (
            target_agent.get("suite_name") is not None
        ), "suite_name should not be null"
        assert target_agent.get("category") is not None, "category should not be null"

        print(
            f"✓ Template agent validation passed for '{agent_name}' with template '{template_id}'"
        )
        return True

    except Exception as e:
        print(f"✗ Template agent validation failed: {str(e)}")
        print(f"Response text: {response.text[:500]}...")
        raise
