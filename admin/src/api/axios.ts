import axios from 'axios';

const instance = axios.create({
  baseURL: 'http://localhost:8000', // Replace with your actual FastAPI backend URL
  headers: {
    'Content-Type': 'application/json',
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET,PUT,POST,DELETE,PATCH,OPTIONS"
  },
});

export default instance;
