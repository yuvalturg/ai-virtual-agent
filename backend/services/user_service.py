"""
User service for agent management and cloning operations.

This service handles user-specific agent operations including:
- Agent cloning with unique naming
- Duplicate detection and prevention
- Agent assignment management
"""

import logging
from typing import List, Optional

from fastapi import HTTPException

from backend.virtual_agents.agent_resource import EnhancedAgentResource

from ..api.llamastack import client

log = logging.getLogger(__name__)


class UserService:
    """Service for user-related agent operations"""

    @staticmethod
    def generate_unique_agent_name(original_name: str, username: str) -> str:
        """
        Generate a unique agent name by combining original name with username.

        Args:
            original_name: The original agent name
            username: The username to include in the new name

        Returns:
            A unique agent name in format: "{original_name} - {username}"
        """
        # Clean the username to avoid special characters
        clean_username = username.replace(" ", "_").replace("@", "_at_")
        return f"{original_name} - {clean_username}"

    @staticmethod
    def agent_configs_are_similar(config1: dict, config2: dict) -> bool:
        """
        Check if two agent configs are similar enough to be considered duplicates.

        Compares key configuration fields excluding the name to detect duplicates.

        Args:
            config1: First agent configuration dictionary
            config2: Second agent configuration dictionary

        Returns:
            True if configurations are similar, False otherwise
        """
        # Compare key fields that define agent behavior (excluding name)
        key_fields = [
            "model",
            "instructions",
            "tools",
            "input_shields",
            "output_shields",
        ]

        for field in key_fields:
            if config1.get(field) != config2.get(field):
                return False

        return True

    @staticmethod
    async def clone_agent_for_user(agent_id: str, username: str) -> str:
        """
        Clone an existing agent from LlamaStack with a user-specific name.

        Args:
            agent_id: The ID of the agent to clone
            username: The username to include in the cloned agent name

        Returns:
            The ID of the newly created cloned agent

        Raises:
            HTTPException: If the original agent doesn't exist or cloning fails
        """
        try:
            # Retrieve the original agent
            original_agent = client.agents.retrieve(agent_id=agent_id)  # type: ignore
            log.info(f"Retrieved original agent: {agent_id}")

            # Get the original agent config
            original_config = original_agent.agent_config
            if isinstance(original_config, dict):
                config_dict = original_config
            else:
                # Convert to dict if it's an object
                config_dict = (
                    original_config.__dict__
                    if hasattr(original_config, "__dict__")
                    else {}
                )

            # Generate unique name for the cloned agent
            original_name = config_dict.get("name", f"Agent-{agent_id[:8]}")
            unique_name = UserService.generate_unique_agent_name(
                original_name, username
            )

            # Create new agent config with unique name
            new_config = config_dict.copy()
            new_config["name"] = unique_name

            # Create the cloned agent
            clone_response = client.agents.create(
                agent_config=new_config  # type: ignore
            )
            cloned_agent_id = clone_response.agent_id

            log.info(
                f"Cloned agent {agent_id} -> {cloned_agent_id} for user {username}"
            )
            return cloned_agent_id

        except Exception as e:
            log.error(f"Failed to clone agent {agent_id} for user {username}: {str(e)}")
            raise HTTPException(
                status_code=500, detail=f"Failed to clone agent {agent_id}: {str(e)}"
            )

    @staticmethod
    async def check_for_duplicate_agents(
        user_agent_ids: List[str], new_agent_config: dict
    ) -> Optional[str]:
        """
        Check if the user already has an agent with similar configuration.

        Args:
            user_agent_ids: List of agent IDs currently assigned to the user
            new_agent_config: Configuration of the new agent to check for duplicates

        Returns:
            Agent ID if duplicate found, None otherwise
        """
        for existing_agent_id in user_agent_ids:
            try:
                enhanced_agent = EnhancedAgentResource(client).retrieve(
                    agent_id=existing_agent_id
                )  # type:ignore
                existing_config = enhanced_agent.agent_config

                # Convert to dict if needed
                if not isinstance(existing_config, dict):
                    existing_config = (
                        existing_config.__dict__
                        if hasattr(existing_config, "__dict__")
                        else {}
                    )

                # Check if configurations are similar
                if UserService.agent_configs_are_similar(
                    dict(existing_config), dict(new_agent_config)
                ):
                    log.info(f"Found duplicate agent: {existing_agent_id}")
                    return existing_agent_id

            except Exception as e:
                log.warning(
                    f"Error checking agent {existing_agent_id} for duplicates: {str(e)}"
                )
                continue

        return None

    @staticmethod
    async def clone_and_assign_agents(
        user_agent_ids: List[str], username: str, requested_agent_ids: List[str]
    ) -> List[str]:
        """
        Clone requested agents and return list of cloned agent IDs, preventing
        duplicates.

        Args:
            user_agent_ids: List of agent IDs currently assigned to the user
            username: Username for generating unique agent names
            requested_agent_ids: List of agent IDs to clone and assign

        Returns:
            List of cloned agent IDs (including existing duplicates)

        Raises:
            HTTPException: If any agent doesn't exist or cloning fails
        """
        new_cloned_agent_ids = []

        # Process each agent ID in the assignment request
        for agent_id in requested_agent_ids:
            try:
                # Verify the agent exists in LlamaStack
                oagent = client.agents.retrieve(agent_id=agent_id)  # type:ignore
                log.info(f"Verified agent exists: {agent_id}")

                # Get the original agent config for duplicate checking
                original_config = oagent.agent_config
                if not isinstance(original_config, dict):
                    original_config = (
                        original_config.__dict__
                        if hasattr(original_config, "__dict__")
                        else {}
                    )

                # Check if user already has a similar agent (prevent duplicates)
                duplicate_agent_id = await UserService.check_for_duplicate_agents(
                    user_agent_ids, original_config
                )
                if duplicate_agent_id:
                    # Double log lines to accommodate linters 88 character limit
                    log.info(f"User {username} has similar agent: {duplicate_agent_id}")
                    log.info(f"Skipping clone of {agent_id}")
                    # Add the existing duplicate to the new list instead of creating
                    # another clone
                    if duplicate_agent_id not in new_cloned_agent_ids:
                        new_cloned_agent_ids.append(duplicate_agent_id)
                    continue

                # Clone the agent with user-specific name
                cloned_agent_id = await UserService.clone_agent_for_user(
                    agent_id, username
                )
                new_cloned_agent_ids.append(cloned_agent_id)

            except HTTPException:
                # Re-raise HTTP exceptions (like 404 for non-existent agents)
                raise
            except Exception as e:
                log.error(f"Error processing agent {agent_id}: {str(e)}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to process agent {agent_id}: {str(e)}",
                )

        return new_cloned_agent_ids

    @staticmethod
    def is_cloned_agent(agent_name: str, username: str) -> bool:
        """
        Check if an agent is a cloned agent belonging to a specific user.

        Cloned agents have names in format: "{original_name} - {username}"

        Args:
            agent_name: The name of the agent to check
            username: The username to check ownership for

        Returns:
            True if the agent is a cloned agent belonging to the user
        """
        clean_username = username.replace(" ", "_").replace("@", "_at_")
        return agent_name.endswith(f" - {clean_username}")

    @staticmethod
    async def get_orphaned_agents(
        removed_agent_ids: List[str], username: str
    ) -> List[str]:
        """
        Identify orphaned cloned agents that should be deleted from LlamaStack.

        An agent is considered orphaned if:
        1. It's a cloned agent (name contains " - username")
        2. It's being removed from the user
        3. No other users have this agent assigned

        Args:
            removed_agent_ids: List of agent IDs being removed from user
            username: Username to check for cloned agent ownership

        Returns:
            List of agent IDs that are orphaned and should be deleted
        """
        orphaned_agents = []

        for agent_id in removed_agent_ids:
            try:
                # Get the agent from LlamaStack
                agent = client.agents.retrieve(agent_id=agent_id)  # type: ignore
                agent_config = agent.agent_config

                # Convert to dict if needed
                if not isinstance(agent_config, dict):
                    agent_config = (
                        agent_config.__dict__
                        if hasattr(agent_config, "__dict__")
                        else {}
                    )

                agent_name = agent_config.get("name", "")

                # Check if this is a cloned agent belonging to this user
                if UserService.is_cloned_agent(agent_name, username):
                    # Currently, we assume cloned agents are user-specific.
                    orphaned_agents.append(agent_id)
                    log.info(f"Agent {agent_id} ({agent_name}) marked as orphaned")

            except Exception as e:
                log.warning(
                    f"Error checking agent {agent_id} for orphan status: {str(e)}"
                )
                continue

        return orphaned_agents

    @staticmethod
    async def cleanup_orphaned_agents(orphaned_agent_ids: List[str]) -> None:
        """
        Delete orphaned cloned agents from LlamaStack.

        Args:
            orphaned_agent_ids: List of agent IDs to delete from LlamaStack
        """
        for agent_id in orphaned_agent_ids:
            try:
                client.agents.delete(agent_id=agent_id)  # type: ignore
                log.info(f"Successfully deleted orphaned agent: {agent_id}")
            except Exception as e:
                log.error(f"Failed to delete orphaned agent {agent_id}: {str(e)}")

    @staticmethod
    async def remove_agents_from_user(
        current_agent_ids: List[str], username: str, agents_to_remove: List[str]
    ) -> List[str]:
        """
        Remove specified agents from user and cleanup orphaned cloned agents.

        Args:
            current_agent_ids: List of agent IDs currently assigned to user
            username: Username for identifying cloned agents
            agents_to_remove: List of agent IDs to remove from user

        Returns:
            List of remaining agent IDs after removal

        Raises:
            HTTPException: If any agent removal fails
        """
        try:
            # Calculate remaining agents
            remaining_agent_ids = [
                agent_id
                for agent_id in current_agent_ids
                if agent_id not in agents_to_remove
            ]

            # Identify orphaned cloned agents
            orphaned_agents = await UserService.get_orphaned_agents(
                agents_to_remove, username
            )

            # Cleanup orphaned agents from LlamaStack
            if orphaned_agents:
                await UserService.cleanup_orphaned_agents(orphaned_agents)
                log.info(
                    f"Cleaned up {len(orphaned_agents)} orphaned agents for {username}"
                )

            log.info(f"Removed {len(agents_to_remove)} agents from user {username}")
            return remaining_agent_ids

        except Exception as e:
            log.error(f"Error removing agents from user {username}: {str(e)}")
            raise HTTPException(
                status_code=500, detail=f"Failed to remove agents: {str(e)}"
            )
