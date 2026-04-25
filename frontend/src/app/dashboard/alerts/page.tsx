"use client";

import { useEffect, useState } from "react";

interface AlertRule {
  id: string;
  name: string;
  emotion: string;
  threshold: number;
  page_url: string | null;
  time_window: string;
  channel: string;
  is_active: boolean;
  last_triggered_at: string | null;
  created_at: string;
}

interface AlertHistoryItem {
  id: string;
  alert_rule_id: string;
  rule_name: string;
  triggered_at: string;
  trigger_value: number;
  page_url: string;
  status: string;
  message: string | null;
}

const EMOTIONS = [
  { value: "frustration", label: "Frustrated", color: "#EF4444" },
  { value: "confusion", label: "Confused", color: "#F59E0B" },
  { value: "anxiety", label: "Anxious", color: "#F97316" },
  { value: "hesitation", label: "Hesitating", color: "#8B5CF6" },
  { value: "satisfaction", label: "Satisfied", color: "#10B981" },
  { value: "delight", label: "Delighted", color: "#059669" },
  { value: "boredom", label: "Bored", color: "#6B7280" },
  { value: "focus", label: "Focused", color: "#3B82F6" },
];

const TIME_WINDOWS = [
  { value: "1h", label: "1 hour" },
  { value: "24h", label: "24 hours" },
  { value: "7d", label: "7 days" },
];

const CHANNELS = [
  { value: "email", label: "Email" },
  { value: "webhook", label: "Webhook" },
];

export default function AlertsPage() {
  const [rules, setRules] = useState<AlertRule[]>([]);
  const [history, setHistory] = useState<AlertHistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateForm, setShowCreateForm] = useState(false);
  // Pending feature: Sidebar badge for unresolved alerts (Playbook Prompt 32)
  const [unresolvedCount, setUnresolvedCount] = useState(0);

  // Form state
  const [formData, setFormData] = useState({
    name: "",
    emotion: "frustration",
    threshold: 30,
    page_url: "",
    time_window: "24h",
    channel: "email",
    webhook_url: "",
    cooldown_hours: 6,
  });

  // Fetch data
  const fetchData = async () => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "";
      const [rulesRes, historyRes, countRes] = await Promise.all([
        fetch(`${apiUrl}/api/v1/alerts`, { credentials: "include" }),
        fetch(`${apiUrl}/api/v1/alerts/history/list?limit=10`, { credentials: "include" }),
        fetch(`${apiUrl}/api/v1/alerts/unresolved-count`, { credentials: "include" }),
      ]);

      if (rulesRes.ok) {
        const rulesData = await rulesRes.json();
        setRules(rulesData.rules || []);
      }
      if (historyRes.ok) {
        const historyData = await historyRes.json();
        setHistory(historyData || []);
      }
      if (countRes.ok) {
        const countData = await countRes.json();
        setUnresolvedCount(countData.count || 0);
      }
    } catch (err) {
      // Error silently handled - UI shows empty state
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  // Create alert
  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "";
      const res = await fetch(`${apiUrl}/api/v1/alerts`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          ...formData,
          page_url: formData.page_url || null,
          webhook_url: formData.channel === "webhook" ? formData.webhook_url : null,
        }),
      });

      if (res.ok) {
        setShowCreateForm(false);
        setFormData({
          name: "",
          emotion: "frustration",
          threshold: 30,
          page_url: "",
          time_window: "24h",
          channel: "email",
          webhook_url: "",
          cooldown_hours: 6,
        });
        fetchData();
      }
    } catch (err) {
      // Error silently handled - user can retry
    }
  };

  // Delete alert
  const handleDelete = async (id: string) => {
    if (!confirm("Are you sure you want to delete this alert?")) return;
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "";
      const res = await fetch(`${apiUrl}/api/v1/alerts/${id}`, {
        method: "DELETE",
        credentials: "include",
      });
      if (res.ok) {
        fetchData();
      }
    } catch (err) {
      // Error silently handled - user can retry
    }
  };

  // Toggle active
  const handleToggle = async (rule: AlertRule) => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "";
      const res = await fetch(`${apiUrl}/api/v1/alerts/${rule.id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ is_active: !rule.is_active }),
      });
      if (res.ok) {
        fetchData();
      }
    } catch (err) {
      // Error silently handled - user can retry
    }
  };

  const getEmotionColor = (emotion: string) => {
    const e = EMOTIONS.find((e) => e.value === emotion);
    return e?.color || "#6B7280";
  };

  const getTimeAgo = (dateStr: string | null) => {
    if (!dateStr) return "Never";
    const date = new Date(dateStr);
    const now = new Date();
    const seconds = Math.floor((now.getTime() - date.getTime()) / 1000);
    if (seconds < 60) return "Just now";
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
    return `${Math.floor(seconds / 86400)}d ago`;
  };

  if (loading) {
    return (
      <div className="p-8">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-200 rounded w-48" />
          <div className="h-64 bg-gray-200 rounded" />
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto p-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Alerts</h1>
          <p className="text-sm text-gray-500 mt-1">
            Get notified when emotions spike on your site
          </p>
        </div>
        <button
          onClick={() => setShowCreateForm(!showCreateForm)}
          className="px-4 py-2 bg-[#007BFF] text-white rounded-lg font-semibold hover:bg-[#0056b3] transition-colors"
        >
          {showCreateForm ? "Cancel" : "Create Alert"}
        </button>
      </div>

      {/* Create Form */}
      {showCreateForm && (
        <div className="bg-white rounded-xl border border-gray-200 p-6 mb-6">
          <h2 className="text-lg font-semibold mb-4">Create New Alert</h2>
          <form onSubmit={handleCreate} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Alert Name</label>
                <input
                  type="text"
                  required
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="e.g., High Frustration on Checkout"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#007BFF]"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">When</label>
                <div className="flex gap-2">
                  <select
                    value={formData.emotion}
                    onChange={(e) => setFormData({ ...formData, emotion: e.target.value })}
                    className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#007BFF]"
                  >
                    {EMOTIONS.map((e) => (
                      <option key={e.value} value={e.value}>{e.label}</option>
                    ))}
                  </select>
                  <span className="self-center text-gray-500">is above</span>
                  <input
                    type="number"
                    min="1"
                    max="100"
                    value={formData.threshold}
                    onChange={(e) => setFormData({ ...formData, threshold: parseInt(e.target.value) })}
                    className="w-20 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#007BFF]"
                  />
                  <span className="self-center text-gray-500">%</span>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">On Page (optional)</label>
                <input
                  type="text"
                  value={formData.page_url}
                  onChange={(e) => setFormData({ ...formData, page_url: e.target.value })}
                  placeholder="e.g., /checkout or leave empty for any page"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#007BFF]"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Time Window</label>
                <select
                  value={formData.time_window}
                  onChange={(e) => setFormData({ ...formData, time_window: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#007BFF]"
                >
                  {TIME_WINDOWS.map((w) => (
                    <option key={w.value} value={w.value}>{w.label}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Notify Via</label>
                <select
                  value={formData.channel}
                  onChange={(e) => setFormData({ ...formData, channel: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#007BFF]"
                >
                  {CHANNELS.map((c) => (
                    <option key={c.value} value={c.value}>{c.label}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Cool-down</label>
                <select
                  value={formData.cooldown_hours}
                  onChange={(e) => setFormData({ ...formData, cooldown_hours: parseInt(e.target.value) })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#007BFF]"
                >
                  <option value="1">1 hour</option>
                  <option value="6">6 hours</option>
                  <option value="24">24 hours</option>
                </select>
              </div>

              {formData.channel === "webhook" && (
                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-1">Webhook URL</label>
                  <input
                    type="url"
                    required={formData.channel === "webhook"}
                    value={formData.webhook_url}
                    onChange={(e) => setFormData({ ...formData, webhook_url: e.target.value })}
                    placeholder="https://your-site.com/webhook"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#007BFF]"
                  />
                </div>
              )}
            </div>

            <div className="flex justify-end gap-3 mt-6">
              <button
                type="button"
                onClick={() => setShowCreateForm(false)}
                className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-2 bg-[#007BFF] text-white rounded-lg font-semibold hover:bg-[#0056b3] transition-colors"
              >
                Create Alert
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Alert Rules Table */}
      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden mb-8">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold">Alert Rules</h2>
        </div>
        {rules.length === 0 ? (
          <div className="p-8 text-center">
            <p className="text-gray-500 mb-4">No alerts configured yet.</p>
            <p className="text-sm text-gray-400">Create your first alert to get notified when emotions spike.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Name</th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Condition</th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Page</th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Channel</th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Status</th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Last Triggered</th>
                  <th className="px-6 py-3 text-right text-xs font-semibold text-gray-500 uppercase">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {rules.map((rule) => (
                  <tr key={rule.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 font-medium text-gray-900">{rule.name}</td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2">
                        <span
                          className="w-2 h-2 rounded-full"
                          style={{ backgroundColor: getEmotionColor(rule.emotion) }}
                        />
                        <span className="capitalize">{rule.emotion}</span>
                        <span className="text-gray-400">&gt;</span>
                        <span className="font-semibold">{rule.threshold}%</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-600">
                      {rule.page_url || <span className="text-gray-400">Any page</span>}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-600 capitalize">{rule.channel}</td>
                    <td className="px-6 py-4">
                      <button
                        onClick={() => handleToggle(rule)}
                        className={`px-2 py-1 rounded-full text-xs font-semibold ${
                          rule.is_active
                            ? "bg-green-100 text-green-700"
                            : "bg-gray-100 text-gray-600"
                        }`}
                      >
                        {rule.is_active ? "Active" : "Paused"}
                      </button>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-600">{getTimeAgo(rule.last_triggered_at)}</td>
                    <td className="px-6 py-4 text-right">
                      <button
                        onClick={() => handleDelete(rule.id)}
                        className="text-red-600 hover:text-red-800 text-sm font-medium"
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Alert History */}
      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold">Recent Alerts</h2>
        </div>
        {history.length === 0 ? (
          <div className="p-8 text-center text-gray-500">
            No alerts have fired yet.
          </div>
        ) : (
          <div className="divide-y divide-gray-200">
            {history.map((item) => (
              <div
                key={item.id}
                className="px-6 py-4 flex items-center justify-between hover:bg-gray-50 cursor-pointer"
                onClick={() => window.location.href = "/dashboard/diagnosis"}
              >
                <div className="flex-1">
                  <p className="text-sm font-medium text-gray-900">{item.rule_name}</p>
                  <p className="text-sm text-gray-600 mt-0.5">
                    {item.page_url === "all pages" ? "All pages" : item.page_url}
                  </p>
                  <p className="text-xs text-gray-400 mt-1">
                    {item.status === "fired" ? "🔴" : "🟢"} {getTimeAgo(item.triggered_at)}
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-sm font-semibold text-gray-900">{item.trigger_value}%</p>
                  <p className="text-xs text-gray-500 capitalize">{item.status}</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
