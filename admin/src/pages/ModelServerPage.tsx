import React, { useEffect, useState } from 'react';
import axios from '../api/axios';

interface ModelServer {
  id?: string;
  name: string;
  provider_name: string;
  model_name: string;
  endpoint_url: string;
  token?: string;
  created_by?: string;
}

export default function ModelServerPage() {
  const [servers, setServers] = useState<ModelServer[]>([]);
  const [form, setForm] = useState<ModelServer>({ name: '', provider_name: '', model_name: '', endpoint_url: '', token: '' });

  useEffect(() => {
    fetchServers();
  }, []);

  const fetchServers = async () => {
    const res = await axios.get('/model_servers');
    setServers(res.data);
  };

  const handleSubmit = async () => {
    if (form.id) {
      await axios.put(`/model_servers/${form.id}`, form);
    } else {
      await axios.post('/model_servers', form);
    }
    setForm({ name: '', provider_name: '', model_name: '', endpoint_url: '', token: '' });
    fetchServers();
  };

  const handleDelete = async (id: string) => {
    await axios.delete(`/model_servers/${id}`);
    fetchServers();
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      <h1 className="text-2xl font-bold mb-4">Model Servers</h1>

      <div className="bg-white shadow rounded p-4 space-y-3 mb-6">
        <input className="w-full border p-2 rounded" placeholder="Name" value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} />
        <input className="w-full border p-2 rounded" placeholder="Provider Name" value={form.provider_name} onChange={e => setForm({ ...form, provider_name: e.target.value })} />
        <input className="w-full border p-2 rounded" placeholder="Model Name" value={form.model_name} onChange={e => setForm({ ...form, model_name: e.target.value })} />
        <input className="w-full border p-2 rounded" placeholder="Endpoint URL" value={form.endpoint_url} onChange={e => setForm({ ...form, endpoint_url: e.target.value })} />
        <input className="w-full border p-2 rounded" placeholder="Token" value={form.token} onChange={e => setForm({ ...form, token: e.target.value })} />
        <button onClick={handleSubmit} className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700">{form.id ? 'Update' : 'Create'}</button>
      </div>

      <ul className="space-y-3">
        {servers.map(server => (
          <li key={server.id} className="bg-white p-4 rounded shadow-sm border flex justify-between items-center">
            <div>
              <strong>{server.name}</strong> — <span className="text-sm text-gray-600">{server.model_name}</span>
              <p className="text-sm text-gray-500">Provider: {server.provider_name}</p>
              <p className="text-sm text-gray-500">Endpoint: {server.endpoint_url}</p>
              <p className="text-sm text-gray-400">Token: {server.token ? '••••••••' : 'N/A'}</p>
            </div>
            <div className="space-x-2">
              <button onClick={() => setForm(server)} className="text-yellow-600 hover:underline">Edit</button>
              <button onClick={() => handleDelete(server.id!)} className="text-red-600 hover:underline">Delete</button>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
