"use client";
import { useState, useEffect } from "react";
import axios from "axios";
import { toast } from "sonner";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

interface ModelSettings {
  provider: "anthropic" | "openai";
  base_url: string;
  api_key: string;
  model_name: string;
}

interface Provider {
  id: string;
  label: string;
  base_url: string;
  models: string[];
}

const PRESET_PROVIDERS: Provider[] = [
  {
    id: "anthropic",
    label: "Anthropic (Claude)",
    base_url: "https://api.anthropic.com",
    models: ["claude-sonnet-4-6", "claude-opus-4-6", "claude-haiku-4-5-20251001"],
  },
  {
    id: "openai",
    label: "OpenAI",
    base_url: "https://api.openai.com/v1",
    models: ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"],
  },
  {
    id: "openai",
    label: "DeepSeek",
    base_url: "https://api.deepseek.com/v1",
    models: ["deepseek-chat", "deepseek-coder"],
  },
  {
    id: "openai",
    label: "Ollama (local)",
    base_url: "http://localhost:11434/v1",
    models: ["llama3", "qwen2.5", "mistral"],
  },
  {
    id: "openai",
    label: "Custom endpoint",
    base_url: "",
    models: [],
  },
];

export default function SettingsPage() {
  const [form, setForm] = useState<ModelSettings>({
    provider: "anthropic",
    base_url: "https://api.anthropic.com",
    api_key: "",
    model_name: "claude-sonnet-4-6",
  });
  const [customModel, setCustomModel] = useState("");
  const [saving, setSaving] = useState(false);
  const [loaded, setLoaded] = useState(false);
  const [selectedPreset, setSelectedPreset] = useState(0);

  useEffect(() => {
    axios.get(`${BASE_URL}/api/settings/model`).then((r) => {
      setForm(r.data);
      setLoaded(true);
    }).catch(() => setLoaded(true));
  }, []);

  function applyPreset(idx: number) {
    const p = PRESET_PROVIDERS[idx];
    setSelectedPreset(idx);
    setForm((prev) => ({
      ...prev,
      provider: p.id as "anthropic" | "openai",
      base_url: p.base_url,
      model_name: p.models[0] ?? prev.model_name,
    }));
  }

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    const payload = { ...form, model_name: customModel || form.model_name };
    setSaving(true);
    try {
      await axios.put(`${BASE_URL}/api/settings/model`, payload);
      toast.success("Settings saved!");
    } catch (err: any) {
      toast.error(err?.response?.data?.detail ?? "Failed to save settings");
    } finally {
      setSaving(false);
    }
  }

  const currentPreset = PRESET_PROVIDERS[selectedPreset];

  return (
    <div className="max-w-2xl mx-auto space-y-8">
      <div>
        <h1 className="text-xl font-bold text-gray-900">Model Settings</h1>
        <p className="text-sm text-gray-500 mt-1">
          Configure which AI provider and model powers the analysis.
        </p>
      </div>

      {/* Provider presets */}
      <div>
        <p className="text-sm font-medium text-gray-700 mb-3">Provider</p>
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
          {PRESET_PROVIDERS.map((p, i) => (
            <button
              key={i}
              type="button"
              onClick={() => applyPreset(i)}
              className={`rounded-lg border px-3 py-2.5 text-sm text-left transition ${
                selectedPreset === i
                  ? "border-blue-500 bg-blue-50 text-blue-700 font-medium"
                  : "border-gray-200 bg-white text-gray-600 hover:border-gray-300"
              }`}
            >
              {p.label}
            </button>
          ))}
        </div>
      </div>

      {loaded && (
        <form onSubmit={handleSave} className="bg-white rounded-2xl border p-6 space-y-5">

          {/* Base URL */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">
              API Base URL
            </label>
            <input
              type="url"
              value={form.base_url}
              onChange={(e) => setForm((p) => ({ ...p, base_url: e.target.value }))}
              placeholder="https://api.anthropic.com"
              className="w-full border rounded-lg px-3 py-2.5 text-sm outline-none focus:ring-2 focus:ring-blue-500 font-mono"
            />
            <p className="text-xs text-gray-400 mt-1">
              Any OpenAI-compatible endpoint works (DeepSeek, Ollama, Azure, etc.)
            </p>
          </div>

          {/* API Key */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">
              API Key
            </label>
            <input
              type="password"
              value={form.api_key}
              onChange={(e) => setForm((p) => ({ ...p, api_key: e.target.value }))}
              placeholder="sk-ant-... / sk-... / (empty for Ollama)"
              className="w-full border rounded-lg px-3 py-2.5 text-sm outline-none focus:ring-2 focus:ring-blue-500 font-mono"
            />
            <p className="text-xs text-gray-400 mt-1">Stored in Redis, never exposed in full after saving.</p>
          </div>

          {/* Model name */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">
              Model
            </label>
            {currentPreset.models.length > 0 ? (
              <div className="space-y-2">
                <div className="flex flex-wrap gap-2">
                  {currentPreset.models.map((m) => (
                    <button
                      key={m}
                      type="button"
                      onClick={() => setForm((p) => ({ ...p, model_name: m }))}
                      className={`text-xs px-3 py-1.5 rounded-full border transition ${
                        form.model_name === m
                          ? "border-blue-500 bg-blue-50 text-blue-700 font-medium"
                          : "border-gray-200 text-gray-600 hover:border-gray-300"
                      }`}
                    >
                      {m}
                    </button>
                  ))}
                </div>
                <p className="text-xs text-gray-400">Or type a custom model name below:</p>
              </div>
            ) : null}
            <input
              type="text"
              value={customModel || (currentPreset.models.includes(form.model_name) ? "" : form.model_name)}
              onChange={(e) => {
                setCustomModel(e.target.value);
                setForm((p) => ({ ...p, model_name: e.target.value }));
              }}
              placeholder={form.model_name || "e.g. claude-sonnet-4-6"}
              className="mt-2 w-full border rounded-lg px-3 py-2.5 text-sm outline-none focus:ring-2 focus:ring-blue-500 font-mono"
            />
          </div>

          {/* Provider (hidden, auto-set from preset) */}
          <div className="bg-gray-50 rounded-lg p-3 text-xs text-gray-500 flex justify-between">
            <span>Protocol</span>
            <span className="font-mono font-medium text-gray-700">{form.provider}</span>
          </div>

          <button
            type="submit"
            disabled={saving}
            className="w-full bg-blue-600 text-white rounded-lg py-3 font-medium text-sm hover:bg-blue-700 disabled:opacity-50"
          >
            {saving ? "Saving..." : "Save Settings"}
          </button>
        </form>
      )}

      {/* CDP proxy status */}
      <div className="bg-white rounded-xl border p-5 space-y-3">
        <h3 className="font-semibold text-gray-900 text-sm">Browser (CDP) Proxy</h3>
        <p className="text-xs text-gray-500">
          web-access CDP proxy enables real-browser crawling (JS rendering, login state, anti-scrape bypass).
          Requires Chrome + Node.js 22+ running locally.
        </p>
        <div className="bg-gray-900 rounded-lg p-3 text-xs font-mono text-green-400 space-y-1">
          <p># 1. Enable remote debugging in Chrome</p>
          <p className="text-gray-400"># chrome://inspect/#remote-debugging → Allow</p>
          <p className="mt-1"># 2. Start CDP proxy</p>
          <p>node ~/.claude/skills/web-access/scripts/check-deps.mjs</p>
          <p className="text-blue-400"># Proxy starts at http://localhost:3456</p>
        </div>
        <CDPStatus />
      </div>
    </div>
  );
}

function CDPStatus() {
  const [status, setStatus] = useState<"checking" | "online" | "offline">("checking");

  useEffect(() => {
    fetch(`${BASE_URL}/api/settings/cdp-status`)
      .then((r) => r.json())
      .then((d) => setStatus(d.available ? "online" : "offline"))
      .catch(() => setStatus("offline"));
  }, []);

  return (
    <div className={`flex items-center gap-2 text-sm ${
      status === "online" ? "text-green-600" :
      status === "offline" ? "text-gray-400" : "text-yellow-600"
    }`}>
      <span className={`w-2 h-2 rounded-full ${
        status === "online" ? "bg-green-500" :
        status === "offline" ? "bg-gray-300" : "bg-yellow-400 animate-pulse"
      }`} />
      {status === "online" ? "CDP proxy online — real browser crawling active" :
       status === "offline" ? "CDP proxy offline — falling back to web_search" :
       "Checking CDP proxy..."}
    </div>
  );
}
