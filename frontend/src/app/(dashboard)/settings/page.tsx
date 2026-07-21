/**
 * Settings page (admin-only) — manage team members and API keys.
 *
 * Two sections:
 * 1. Team Members — list users, update roles, deactivate accounts
 * 2. API Keys — configure BrightData, Prospeo, Vibe Prospecting, Instantly
 */

"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/lib/auth";
import { apiRequest } from "@/lib/api";
import { User, Setting, PaginatedResponse } from "@/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { formatDate } from "@/lib/utils";
import {
  Settings,
  Users,
  Key,
  Shield,
  ShieldOff,
  UserX,
  Save,
  Eye,
  EyeOff,
  Plus,
} from "lucide-react";
import { toast } from "sonner";

// Human-friendly labels for API key settings
const API_KEY_LABELS: Record<string, { name: string; description: string }> = {
  brightdata_api_key: {
    name: "BrightData",
    description: "Web scraping proxy for job posting discovery",
  },
  prospeo_api_key: {
    name: "Prospeo",
    description: "Email finder and verification service",
  },
  vibe_prospecting_api_key: {
    name: "Vibe Prospecting",
    description: "Contact enrichment and phone number lookup",
  },
  instantly_api_key: {
    name: "Instantly",
    description: "Cold email sending and sequence automation",
  },
};

export default function SettingsPage() {
  const { user: currentUser } = useAuth();

  // Team Members state
  const [users, setUsers] = useState<User[]>([]);
  const [usersLoading, setUsersLoading] = useState(true);

  // Invite form
  const [showInvite, setShowInvite] = useState(false);
  const [inviteEmail, setInviteEmail] = useState("");
  const [invitePassword, setInvitePassword] = useState("");
  const [inviteRole, setInviteRole] = useState("member");
  const [inviteError, setInviteError] = useState("");

  // API Keys state
  const [settings, setSettings] = useState<Setting[]>([]);
  const [settingsLoading, setSettingsLoading] = useState(true);
  const [editingKey, setEditingKey] = useState<string | null>(null);
  const [keyValue, setKeyValue] = useState("");
  const [savingKey, setSavingKey] = useState(false);

  // Fetch team members
  useEffect(() => {
    if (currentUser?.role !== "admin") return;
    async function fetchUsers() {
      try {
        const data = await apiRequest<PaginatedResponse<User>>("/api/users?page_size=50");
        setUsers(data.items);
      } catch (err) {
        console.error("Failed to fetch users:", err);
      } finally {
        setUsersLoading(false);
      }
    }
    fetchUsers();
  }, [currentUser]);

  // Fetch API key settings
  useEffect(() => {
    if (currentUser?.role !== "admin") return;
    async function fetchSettings() {
      try {
        const data = await apiRequest<Setting[]>("/api/settings");
        setSettings(data);
      } catch (err) {
        console.error("Failed to fetch settings:", err);
      } finally {
        setSettingsLoading(false);
      }
    }
    fetchSettings();
  }, [currentUser]);

  // Block non-admin users AFTER all hooks
  if (currentUser && currentUser.role !== "admin") {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="text-center text-slate-400">
          <Shield className="mx-auto mb-2 h-8 w-8" />
          <p className="font-medium">Admin access required</p>
          <p className="text-sm">Only admins can access settings</p>
        </div>
      </div>
    );
  }

  const handleInvite = async () => {
    if (!inviteEmail.trim() || !invitePassword.trim()) {
      setInviteError("Email and password are required");
      return;
    }
    setInviteError("");
    try {
      await apiRequest("/api/auth/register", {
        method: "POST",
        body: JSON.stringify({
          email: inviteEmail.trim(),
          password: invitePassword.trim(),
          role: inviteRole,
        }),
      });
      // Refresh users list
      const data = await apiRequest<PaginatedResponse<User>>("/api/users?page_size=50");
      setUsers(data.items);
      setShowInvite(false);
      setInviteEmail("");
      setInvitePassword("");
      toast.success("User invited successfully");
    } catch (err) {
      setInviteError(err instanceof Error ? err.message : "Failed to invite user");
      toast.error("Failed to invite user");
    }
  };

  const handleRoleChange = async (userId: string, newRole: string) => {
    try {
      await apiRequest(`/api/users/${userId}/role`, {
        method: "PATCH",
        body: JSON.stringify({ role: newRole }),
      });
      setUsers((prev) =>
        prev.map((u) => (u.id === userId ? { ...u, role: newRole as "admin" | "member" } : u))
      );
      toast.success("User role updated");
    } catch (err) {
      console.error("Failed to update role:", err);
      toast.error("Failed to update user role");
    }
  };

  const handleDeactivate = async (userId: string) => {
    if (!confirm("Deactivate this user? They will no longer be able to log in.")) return;
    try {
      await apiRequest(`/api/users/${userId}/deactivate`, { method: "PATCH" });
      setUsers((prev) =>
        prev.map((u) => (u.id === userId ? { ...u, is_active: false } : u))
      );
      toast.success("User deactivated");
    } catch (err) {
      console.error("Failed to deactivate user:", err);
      toast.error("Failed to deactivate user");
    }
  };

  const handleSaveKey = async (key: string) => {
    if (!keyValue.trim()) return;
    setSavingKey(true);
    try {
      await apiRequest(`/api/settings/${key}`, {
        method: "PUT",
        body: JSON.stringify({ value: keyValue.trim() }),
      });
      // Refresh settings
      const data = await apiRequest<Setting[]>("/api/settings");
      toast.success("Settings saved successfully");
      setSettings(data);
      setEditingKey(null);
      setKeyValue("");
    } catch (err) {
      console.error("Failed to save key:", err);
      toast.error("Failed to save settings");
    } finally {
      setSavingKey(false);
    }
  };

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-slate-900">Settings</h1>
        <p className="text-sm text-slate-500">Manage team members and API configuration</p>
      </div>

      {/* ===== TEAM MEMBERS SECTION ===== */}
      <Card className="mb-8">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <Users className="h-5 w-5 text-slate-500" />
              Team Members
            </CardTitle>
            <Button size="sm" onClick={() => setShowInvite(!showInvite)}>
              <Plus className="mr-1 h-4 w-4" />
              Invite Member
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {/* Invite Form */}
          {showInvite && (
            <div className="mb-4 rounded-lg border border-slate-200 bg-slate-50 p-4">
              <h3 className="mb-3 text-sm font-medium text-slate-700">Invite New Team Member</h3>
              {inviteError && (
                <div className="mb-2 text-sm text-red-600">{inviteError}</div>
              )}
              <div className="flex flex-wrap items-end gap-3">
                <div className="flex-1 min-w-[180px]">
                  <label className="mb-1 block text-xs text-slate-500">Email</label>
                  <Input
                    type="email"
                    value={inviteEmail}
                    onChange={(e) => setInviteEmail(e.target.value)}
                    placeholder="new@team.com"
                  />
                </div>
                <div className="flex-1 min-w-[150px]">
                  <label className="mb-1 block text-xs text-slate-500">Password</label>
                  <Input
                    type="password"
                    value={invitePassword}
                    onChange={(e) => setInvitePassword(e.target.value)}
                    placeholder="Initial password"
                  />
                </div>
                <div className="w-32">
                  <label className="mb-1 block text-xs text-slate-500">Role</label>
                  <select
                    value={inviteRole}
                    onChange={(e) => setInviteRole(e.target.value)}
                    className="h-9 w-full rounded-md border border-slate-200 bg-white px-3 text-sm"
                  >
                    <option value="member">Member</option>
                    <option value="admin">Admin</option>
                  </select>
                </div>
                <Button size="sm" onClick={handleInvite}>Invite</Button>
              </div>
            </div>
          )}

          {/* Users Table */}
          {usersLoading ? (
            <div className="flex h-24 items-center justify-center">
              <div className="h-5 w-5 animate-spin rounded-full border-2 border-slate-200 border-t-slate-900" />
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-100">
                    <th className="px-3 py-2 text-left font-medium text-slate-500">Email</th>
                    <th className="px-3 py-2 text-left font-medium text-slate-500">Role</th>
                    <th className="px-3 py-2 text-left font-medium text-slate-500">Status</th>
                    <th className="px-3 py-2 text-left font-medium text-slate-500">Joined</th>
                    <th className="px-3 py-2 text-right font-medium text-slate-500">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {users.map((user) => (
                    <tr key={user.id} className="border-b border-slate-50">
                      <td className="px-3 py-2 font-medium text-slate-900">
                        {user.email}
                        {user.id === currentUser?.id && (
                          <span className="ml-1 text-xs text-slate-400">(you)</span>
                        )}
                      </td>
                      <td className="px-3 py-2">
                        <Badge variant={user.role === "admin" ? "default" : "secondary"}>
                          {user.role === "admin" ? (
                            <><Shield className="mr-1 h-3 w-3" />Admin</>
                          ) : (
                            "Member"
                          )}
                        </Badge>
                      </td>
                      <td className="px-3 py-2">
                        <Badge variant={user.is_active ? "success" : "destructive"}>
                          {user.is_active ? "Active" : "Deactivated"}
                        </Badge>
                      </td>
                      <td className="px-3 py-2 text-slate-400">{formatDate(user.created_at)}</td>
                      <td className="px-3 py-2 text-right">
                        {user.id !== currentUser?.id && user.is_active && (
                          <div className="flex items-center justify-end gap-1">
                            <Button
                              variant="ghost"
                              size="sm"
                              className="text-xs"
                              onClick={() => handleRoleChange(
                                user.id,
                                user.role === "admin" ? "member" : "admin"
                              )}
                            >
                              {user.role === "admin" ? (
                                <><ShieldOff className="mr-1 h-3 w-3" />Demote</>
                              ) : (
                                <><Shield className="mr-1 h-3 w-3" />Promote</>
                              )}
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              className="text-xs text-red-500 hover:text-red-700"
                              onClick={() => handleDeactivate(user.id)}
                            >
                              <UserX className="mr-1 h-3 w-3" />Deactivate
                            </Button>
                          </div>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* ===== API KEYS SECTION ===== */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Key className="h-5 w-5 text-slate-500" />
            API Keys
          </CardTitle>
          <p className="text-xs text-slate-500">
            Configure API keys for external service integrations. Values are encrypted at rest.
          </p>
        </CardHeader>
        <CardContent>
          {settingsLoading ? (
            <div className="flex h-24 items-center justify-center">
              <div className="h-5 w-5 animate-spin rounded-full border-2 border-slate-200 border-t-slate-900" />
            </div>
          ) : (
            <div className="space-y-4">
              {settings.map((setting) => {
                const meta = API_KEY_LABELS[setting.key] || {
                  name: setting.key,
                  description: "",
                };
                const isEditing = editingKey === setting.key;

                return (
                  <div
                    key={setting.key}
                    className="flex items-center gap-4 rounded-lg border border-slate-100 p-4"
                  >
                    <div className="flex-1">
                      <p className="font-medium text-slate-900">{meta.name}</p>
                      <p className="text-xs text-slate-400">{meta.description}</p>
                      <p className="mt-1 font-mono text-sm text-slate-500">
                        {setting.masked_value}
                      </p>
                      {setting.updated_at && (
                        <p className="mt-0.5 text-xs text-slate-400">
                          Last updated: {formatDate(setting.updated_at)}
                        </p>
                      )}
                    </div>
                    <div className="flex items-center gap-2">
                      {isEditing ? (
                        <>
                          <Input
                            type="password"
                            value={keyValue}
                            onChange={(e) => setKeyValue(e.target.value)}
                            placeholder="Enter new API key"
                            className="w-64"
                          />
                          <Button
                            size="sm"
                            onClick={() => handleSaveKey(setting.key)}
                            disabled={savingKey}
                          >
                            <Save className="mr-1 h-3 w-3" />
                            {savingKey ? "Saving..." : "Save"}
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => { setEditingKey(null); setKeyValue(""); }}
                          >
                            Cancel
                          </Button>
                        </>
                      ) : (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => { setEditingKey(setting.key); setKeyValue(""); }}
                        >
                          {setting.masked_value === "Not configured" ? "Configure" : "Update"}
                        </Button>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
