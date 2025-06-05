from __future__ import annotations

from typing import List, Type, cast, Any
import httpx
import logging

from llama_stack_client._types import NOT_GIVEN, Body, Query, Headers, NotGiven
from llama_stack_client._base_client import make_request_options
from llama_stack_client.resources.agents.session import SessionResource

log = logging.getLogger(__name__)

class EnhancedSessionResource(SessionResource):
    
    def list(
        self,
        agent_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> Any:
        """List all sessions for a specific agent"""
        if not agent_id:
            raise ValueError(f"Expected a non-empty value for `agent_id` but received {agent_id!r}")
        
        log.info(f"Making request to: /v1/agents/{agent_id}/sessions")
        
        try:
            # First try with simple response handling
            response = self._get(
                f"/v1/agents/{agent_id}/sessions",
                options=make_request_options(
                    extra_headers=extra_headers,
                    extra_query=extra_query,
                    extra_body=extra_body,
                    timeout=timeout,
                ),
                cast_to=object,  # Use generic object to see what we get
            )
            log.info(f"Session list response type: {type(response)}")
            log.info(f"Session list response value: {response}")
            return response
            
        except Exception as e:
            log.error(f"Session list request failed: {e}")
            log.error(f"Exception type: {type(e)}")
            # Check if it's a 404 - endpoint might not exist
            if hasattr(e, 'status_code'):
                log.error(f"HTTP status code: {e.status_code}")
            raise