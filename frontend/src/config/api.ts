const baseUrl = (import.meta.env.VITE_API_BASE_URL as string) || ''; // fallback to '' for relative paths in prod

export default baseUrl;

export const LLMS_API_ENDPOINT = '/api/llama_stack/llms';
export const EMBEDDING_MODELS_API_ENDPOINT = '/api/llama_stack/embedding_models';
export const PROVIDERS_API_ENDPOINT = '/api/llama_stack/providers';
export const KNOWLEDGE_BASES_API_ENDPOINT = '/api/knowledge_bases/';
export const TOOLS_API_ENDPOINT = '/api/tools/';
export const AGENTS_API_ENDPOINT = '/api/virtual_assistants/';
