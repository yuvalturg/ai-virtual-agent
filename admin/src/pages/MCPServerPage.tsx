import React, { useEffect, useState } from 'react';
import axios from '../api/axios';

interface MCPServer {
  id?: string;
  name: string;
  title: string;
  description?: string;
  endpoint_url: string;
  configuration?: string;
  created_by?: string;
}

export default function MCPServerPage() {
  const [servers, setServers] = useState<MCPServer[]>([]);
  const [form, setForm] = useState<MCPServer>({ name: '', title: '', description: '', endpoint_url: '', configuration:'{}' });

  useEffect(() => {
    fetchServers();
  }, []);

  const fetchServers = async () => {
    const res = await axios.get('/mcp_servers');
    res.data.configuration = JSON.stringify(res.data.configuration)
    setServers(res.data);
  };

  const handleSubmit = async () => {
    try{
      const parsedConfig = JSON.parse(form.configuration || '{}');
      const payload = { ...form, configuration: parsedConfig };
      if (form.id) {
        await axios.put(`/mcp_servers/${form.id}`, payload);
      } else {
        await axios.post('/mcp_servers', payload);
      }
      setForm({ name: '', title: '', endpoint_url: '', description: '', configuration: '{}'});
      fetchServers();
    } catch (err) {
      console.log(err);
      alert('Invalid JSON in configuration field.');
    }
  };

  const handleDelete = async (id: string) => {
    await axios.delete(`/mcp_servers/${id}`);
    fetchServers();
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      <h1 className="text-2xl font-bold mb-4">MCP Servers</h1>

      <div className="bg-white shadow rounded p-4 space-y-3 mb-6">
        <input className="w-full border p-2 rounded" placeholder="Name" value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} />
        <input className="w-full border p-2 rounded" placeholder="Title" value={form.title} onChange={e => setForm({ ...form, title: e.target.value })} />
        <input className="w-full border p-2 rounded" placeholder="Description" value={form.description} onChange={e => setForm({ ...form, description: e.target.value })} />
        <input className="w-full border p-2 rounded" placeholder="Endpoint URL" value={form.endpoint_url} onChange={e => setForm({ ...form, endpoint_url: e.target.value })} />
        <textarea className="w-full border p-2 rounded" placeholder="Configuration (JSON format)" value={form.configuration} onChange={e => setForm({ ...form, configuration: e.target.value })} rows={4} />
        <button onClick={handleSubmit} className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700">{form.id ? 'Update' : 'Create'}</button>
      </div>

      <ul className="space-y-3">
        {servers.map(server => (
          <li key={server.id} className="bg-white p-4 rounded shadow-sm border flex justify-between items-center">
            <div>
              <strong>{server.name}</strong> — <span className="text-sm text-gray-600">{server.title}</span>
              <p className="text-sm text-gray-500">{server.description}</p>
              <p className="text-sm text-gray-500">{server.endpoint_url}</p>
              <pre className="text-xs text-gray-500 whitespace-pre-wrap">{JSON.stringify(server.configuration, null, 2)}</pre>
            </div>
            <div className="space-x-2">
              <button onClick={() => setForm({ ...server, configuration: JSON.stringify(server.configuration, null, 2) })} className="text-yellow-600 hover:underline">Edit</button>
              <button onClick={() => handleDelete(server.id!)} className="text-red-600 hover:underline">Delete</button>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
