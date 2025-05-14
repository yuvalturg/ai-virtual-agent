const baseUrl =
  import.meta.env.VITE_API_BASE_URL || ''; // fallback to '' for relative paths in prod

export default baseUrl;