// API Configuration
// Use environment variable or default to localhost
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ||
    import.meta.env.VITE_BACKEND_URL ||
    (import.meta.env.PROD ? '/api' : 'http://localhost:8001');

export const API_URL = API_BASE_URL;
export default API_URL;
