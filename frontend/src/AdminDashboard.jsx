import { useState, useEffect } from "react";
import axios from "axios";
import "./AdminDashboard.css";
import { API_URL } from "./config";

export default function AdminDashboard({ onBackToChat }) {
  const [analytics, setAnalytics] = useState(null);
  const [stats, setStats] = useState(null);
  const [users, setUsers] = useState(null);
  const [revenue, setRevenue] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("overview");

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [analyticsRes, statsRes, usersRes, revenueRes] = await Promise.all([
        axios.get(`${API_URL}/api/admin/analytics`),
        axios.get(`${API_URL}/api/admin/stats`),
        axios.get(`${API_URL}/api/admin/users`),
        axios.get(`${API_URL}/api/admin/revenue`),
      ]);

      setAnalytics(analyticsRes.data);
      setStats(statsRes.data);
      setUsers(usersRes.data);
      setRevenue(revenueRes.data);
    } catch (error) {
      console.error("Error loading admin data:", error);
    } finally {
      setLoading(false);
    }
  };

  if (loading && !analytics) {
    return (
      <div className="admin-dashboard">
        <div className="loading">Loading dashboard...</div>
      </div>
    );
  }

  return (
    <div className="admin-dashboard">
      <div className="admin-header">
        <h1>Admin Dashboard</h1>
        <div className="header-actions">
          {onBackToChat && (
            <button onClick={onBackToChat} className="back-btn">
              ← Back to Chat
            </button>
          )}
          <button onClick={loadData} className="refresh-btn">
            🔄 Refresh
          </button>
        </div>
      </div>

      <div className="admin-tabs">
        <button
          className={activeTab === "overview" ? "active" : ""}
          onClick={() => setActiveTab("overview")}
        >
          Overview
        </button>
        <button
          className={activeTab === "analytics" ? "active" : ""}
          onClick={() => setActiveTab("analytics")}
        >
          Analytics
        </button>
        <button
          className={activeTab === "users" ? "active" : ""}
          onClick={() => setActiveTab("users")}
        >
          Users
        </button>
        <button
          className={activeTab === "revenue" ? "active" : ""}
          onClick={() => setActiveTab("revenue")}
        >
          Revenue
        </button>
      </div>

      <div className="admin-content">
        {activeTab === "overview" && (
          <div className="overview-tab">
            <div className="stats-grid">
              <div className="stat-card">
                <h3>Total Page Views</h3>
                <p className="stat-value">{stats?.totalPageViews || 0}</p>
              </div>
              <div className="stat-card">
                <h3>Total Messages</h3>
                <p className="stat-value">{stats?.totalMessages || 0}</p>
              </div>
              <div className="stat-card">
                <h3>Unique Users</h3>
                <p className="stat-value">{stats?.uniqueUsers || 0}</p>
              </div>
              <div className="stat-card">
                <h3>Top Agents</h3>
                <div className="top-agents">
                  {stats?.topAgents?.slice(0, 3).map((agent, i) => (
                    <div key={i} className="agent-item">
                      <span className="agent-name">{agent.agentId}</span>
                      <span className="agent-count">{agent.count}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div className="recent-activity">
              <h2>Recent Activity</h2>
              <div className="activity-list">
                <div className="activity-section">
                  <h3>Recent Messages</h3>
                  {stats?.recentActivity?.messages?.map((msg, i) => (
                    <div key={i} className="activity-item">
                      <span className="activity-time">
                        {new Date(msg.timestamp).toLocaleTimeString()}
                      </span>
                      <span className="activity-text">
                        User: {msg.userId} → Agent: {msg.agentId}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === "analytics" && analytics && (
          <div className="analytics-tab">
            <div className="analytics-summary">
              <h2>Analytics Summary</h2>
              <div className="summary-grid">
                <div className="summary-item">
                  <label>Total Page Views</label>
                  <span>{analytics.summary?.totalPageViews || 0}</span>
                </div>
                <div className="summary-item">
                  <label>Total Messages</label>
                  <span>{analytics.summary?.totalMessages || 0}</span>
                </div>
                <div className="summary-item">
                  <label>Unique Users</label>
                  <span>{analytics.summary?.uniqueUsers || 0}</span>
                </div>
                <div className="summary-item">
                  <label>Avg Messages/User</label>
                  <span>
                    {analytics.summary?.averageMessagesPerUser?.toFixed(2) || 0}
                  </span>
                </div>
              </div>
            </div>

            <div className="top-agents-section">
              <h2>Top Agents</h2>
              <div className="agents-list">
                {analytics.summary?.topAgents?.map((agent, i) => (
                  <div key={i} className="agent-row">
                    <span className="agent-rank">#{i + 1}</span>
                    <span className="agent-name">{agent.agentId}</span>
                    <span className="agent-count">{agent.count} messages</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {activeTab === "users" && users && (
          <div className="users-tab">
            <h2>Users ({users.total})</h2>
            <div className="users-table">
              <div className="table-header">
                <span>User ID</span>
                <span>Messages</span>
                <span>Agents Used</span>
                <span>First Seen</span>
                <span>Last Seen</span>
              </div>
              {users.users?.map((user, i) => (
                <div key={i} className="table-row">
                  <span className="user-id">{user.userId}</span>
                  <span>{user.messageCount}</span>
                  <span>{user.agentsUsed?.length || 0}</span>
                  <span>{new Date(user.firstSeen).toLocaleDateString()}</span>
                  <span>{new Date(user.lastSeen).toLocaleDateString()}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {activeTab === "revenue" && revenue && (
          <div className="revenue-tab">
            <h2>Revenue</h2>
            <div className="revenue-summary">
              <div className="revenue-card">
                <h3>Total Revenue</h3>
                <p className="revenue-amount">
                  ${revenue.totalRevenue?.toFixed(2) || "0.00"}
                </p>
              </div>
              <div className="revenue-card">
                <h3>Total Transactions</h3>
                <p className="revenue-amount">{revenue.transactions || 0}</p>
              </div>
            </div>

            <div className="transactions-list">
              <h3>Recent Transactions</h3>
              {revenue.revenue?.length > 0 ? (
                revenue.revenue.map((tx, i) => (
                  <div key={i} className="transaction-item">
                    <span>${tx.amount?.toFixed(2) || "0.00"}</span>
                    <span>{new Date(tx.timestamp).toLocaleString()}</span>
                  </div>
                ))
              ) : (
                <p>No transactions yet</p>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

