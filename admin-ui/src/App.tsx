import { useEffect, useState } from "react";

interface ProviderHealth {
  name: string;
  healthy: boolean;
  latency_ms: number;
}

function App() {
  const [providers, setProviders] = useState<ProviderHealth[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch("/v1/admin/providers/health")
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then((data) => {
        setProviders(data.providers || []);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, []);

  return (
    <div style={{ padding: "2rem" }}>
      <h1>AI Inference Gateway Admin</h1>
      <section className="card">
        <h2>Provider Health</h2>
        {loading && <p>Loading...</p>}
        {error && <p style={{ color: "#f87171" }}>Error: {error}</p>}
        <div className="grid">
          {providers.map((provider) => (
            <div key={provider.name} className="card">
              <h3>{provider.name}</h3>
              <p>
                Status:{" "}
                <span
                  className={
                    provider.healthy ? "status-healthy" : "status-unhealthy"
                  }
                >
                  {provider.healthy ? "Healthy" : "Unhealthy"}
                </span>
              </p>
              <p>Latency: {provider.latency_ms} ms</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}

export default App;
