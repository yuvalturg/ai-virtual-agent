from __future__ import annotations

import asyncio
import logging
import os
from typing import List

import httpx
from fastapi import HTTPException
from llama_stack_client._types import NOT_GIVEN, Body, Headers, NotGiven, Query
from llama_stack_client.resources.agents.session import AsyncSessionResource

logger = logging.getLogger(__name__)


class EnhancedSessionResource(AsyncSessionResource):
    async def list(
        self,
        agent_id: str,
        *,
        _extra_headers: Headers | None = None,
        _extra_query: Query | None = None,
        _extra_body: Body | None = None,
        _timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> List[dict]:  # Return List[dict] instead of List[Session]
        """List all accessible sessions for a specific agent"""
        if not agent_id:
            raise ValueError(
                f"Expected a non-empty value for `agent_id` but received "
                f"{agent_id!r}"
            )

        logger.info(f"Making request to: /v1/agents/{agent_id}/sessions")

        try:
            logger.info("About to call self._get()...")

            import httpx

            # Use direct HTTP request to avoid client parsing issues
            async with httpx.AsyncClient() as http_client:
                llamastack_url = os.getenv("LLAMASTACK_URL", "http://localhost:8321")
                response = await http_client.get(
                    f"{llamastack_url}/v1/agents/{agent_id}/sessions",
                    headers=self._client.default_headers,
                    timeout=30.0,
                )
                response.raise_for_status()
                data = response.json()

            logger.info("Successfully got response from self._get()")
            logger.info(f"Response type: {type(response)}")

            # Extract sessions data
            sessions_data = data.get("data", [])
            logger.info(f"Found {len(sessions_data)} sessions in response")

            # Check "get" permission on each session
            allowed_sessions = []

            async with httpx.AsyncClient() as http_client:
                tasks = []
                for session in sessions_data:
                    session_id = session.get("session_id")
                    if not session_id:
                        continue
                    task = http_client.get(
                        f"{llamastack_url}/v1/agents/{agent_id}/session/"
                        f"{session_id}",
                        headers=self._client.default_headers,
                        timeout=10.0,
                    )
                    tasks.append((session, task))

                responses = await asyncio.gather(
                    *[task for _, task in tasks], return_exceptions=True
                )

                for (session, _), resp in zip(tasks, responses):
                    if isinstance(resp, Exception):
                        logger.warning(
                            f"Failed to check session \
                                {session.get('session_id')}: {resp}"
                        )
                        continue
                    if resp.status_code == 200:
                        allowed_sessions.append(session)
                    else:
                        logger.info(
                            f"Session {session.get('session_id')} not \
                                accessible (status {resp.status_code})"
                        )

            logger.info(f"{len(allowed_sessions)} sessions have 'get' permission")

            return allowed_sessions

        except Exception as e:
            logger.error(f"Error in session list: {e}")
            logger.error(f"Exception type: {type(e)}")
            import traceback

            logger.error(f"Full traceback: {traceback.format_exc()}")
            raise HTTPException(
                status_code=500, detail=f"Failed to fetch sessions: {str(e)}"
            )

    async def delete(
        self,
        session_id: str,
        agent_id: str,
        *,
        _extra_headers: Headers | None = None,
        _extra_query: Query | None = None,
        _extra_body: Body | None = None,
        _timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> dict:
        """Delete a session for a specific agent"""
        if not agent_id:
            raise ValueError(
                f"Expected a non-empty value for `agent_id` but received "
                f"{agent_id!r}"
            )
        if not session_id:
            raise ValueError(
                "Expected a non-empty value for `session_id` but received "
                f"{session_id!r}"
            )

        logger.info(
            "Making DELETE request to: /v1/agents/{agent_id}/session/{session_id}"
        )

        try:
            import httpx

            # Use direct HTTP request to delete session
            async with httpx.AsyncClient() as http_client:
                llamastack_url = os.getenv("LLAMASTACK_URL", "http://localhost:8321")
                response = await http_client.delete(
                    f"{llamastack_url}/v1/agents/{agent_id}/session/{session_id}",
                    headers=self._client.default_headers,
                    timeout=30.0,
                )
                response.raise_for_status()

                logger.info(
                    f"Successfully deleted session {session_id} for agent "
                    f"{agent_id}"
                )
                return {"message": "Session deleted successfully"}

        except httpx.HTTPStatusError as e:
            logger.error(
                "HTTP error deleting session: "
                f"{e.response.status_code} - {e.response.text}"
            )
            if e.response.status_code == 404:
                raise HTTPException(
                    status_code=404,
                    detail=f"Session {session_id} not found for agent {agent_id}",
                )
            else:
                raise HTTPException(
                    status_code=e.response.status_code,
                    detail=f"Failed to delete session: {e.response.text}",
                )
        except Exception as e:
            logger.error(f"Error deleting session: {e}")
            logger.error(f"Exception type: {type(e)}")
            import traceback

            logger.error(f"Full traceback: {traceback.format_exc()}")
            raise HTTPException(
                status_code=500, detail=f"Failed to delete session: {str(e)}"
            )
