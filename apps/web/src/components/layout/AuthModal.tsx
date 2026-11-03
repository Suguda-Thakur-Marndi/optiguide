import React, { useState, useEffect } from 'react';
import { apiClient, UserSessionAudit } from '../../services/apiClient';
import { UserProfile, UserRole } from '@optiguide/shared';
import { setCurrentUser } from '../../services/storage';

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
  currentUser: UserProfile | null;
  onAuthSuccess: (user: UserProfile) => void;
  onLogoutSuccess: () => void;
}

export const AuthModal: React.FC<AuthModalProps> = ({
  isOpen,
  onClose,
  currentUser,
  onAuthSuccess,
  onLogoutSuccess,
}) => {
  const [tab, setTab] = useState<'login' | 'register' | 'profile'>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [phoneNumber, setPhoneNumber] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [sessions, setSessions] = useState<UserSessionAudit[]>([]);

  const isAuthenticated = Boolean(
    apiClient.getAccessToken() && currentUser && !currentUser.id.startsWith('usr-guest')
  );

  useEffect(() => {
    if (isAuthenticated) {
      setTab('profile');
      loadProfileAndSessions();
    } else {
      setTab('login');
    }
    setError(null);
    setSuccessMsg(null);
  }, [isOpen, isAuthenticated]);

  const loadProfileAndSessions = async () => {
    try {
      setLoading(true);
      const [me, userSessions] = await Promise.all([
        apiClient.getMe(),
        apiClient.getUserSessions().catch(() => []),
      ]);
      setFullName(me.full_name || '');
      setPhoneNumber(me.phone_number || '');
      setSessions(userSessions);
    } catch (err: any) {
      setError(err?.message || 'Failed to load user profile');
    } finally {
      setLoading(false);
    }
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const res = await apiClient.login({ email, password });
      const userProfile: UserProfile = {
        id: res.user.id,
        email: res.user.email,
        fullName: res.user.full_name,
        role: (res.user.role as UserRole) || 'individual',
        preferredLanguage: 'en',
        createdAt: res.user.created_at || new Date().toISOString(),
        updatedAt: res.user.updated_at || new Date().toISOString(),
      };
      setCurrentUser(userProfile);
      onAuthSuccess(userProfile);
      setSuccessMsg('Successfully signed in.');
      setPassword('');
    } catch (err: any) {
      setError(err?.message || 'Authentication failed. Check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const res = await apiClient.register({ email, password, full_name: fullName });
      const userProfile: UserProfile = {
        id: res.user.id,
        email: res.user.email,
        fullName: res.user.full_name,
        role: (res.user.role as UserRole) || 'individual',
        preferredLanguage: 'en',
        createdAt: res.user.created_at || new Date().toISOString(),
        updatedAt: res.user.updated_at || new Date().toISOString(),
      };
      setCurrentUser(userProfile);
      onAuthSuccess(userProfile);
      setSuccessMsg('Account registered successfully.');
      setPassword('');
    } catch (err: any) {
      setError(err?.message || 'Registration failed. Password must meet complexity requirements.');
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccessMsg(null);
    setLoading(true);
    try {
      const updated = await apiClient.updateProfile({
        full_name: fullName,
        phone_number: phoneNumber || undefined,
      });
      const userProfile: UserProfile = {
        id: updated.id,
        email: updated.email,
        fullName: updated.full_name,
        role: (updated.role as UserRole) || 'individual',
        preferredLanguage: 'en',
        createdAt: updated.created_at || new Date().toISOString(),
        updatedAt: updated.updated_at || new Date().toISOString(),
      };
      setCurrentUser(userProfile);
      onAuthSuccess(userProfile);
      setSuccessMsg('Profile updated successfully.');
    } catch (err: any) {
      setError(err?.message || 'Failed to update profile.');
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = async () => {
    setLoading(true);
    try {
      await apiClient.logout();
      onLogoutSuccess();
      onClose();
    } catch (err: any) {
      setError(err?.message || 'Logout encountered an issue.');
    } finally {
      setLoading(false);
    }
  };

  const handleLogoutAll = async () => {
    setLoading(true);
    try {
      await apiClient.logoutAll();
      onLogoutSuccess();
      onClose();
    } catch (err: any) {
      setError(err?.message || 'Logout all encountered an issue.');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(7, 63, 53, 0.65)',
        backdropFilter: 'blur(3px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 1000,
        padding: '20px',
      }}
      onClick={onClose}
    >
      <div
        style={{
          backgroundColor: '#F7F4EC',
          border: '1px solid #D7D2C4',
          borderRadius: '10px',
          maxWidth: '520px',
          width: '100%',
          maxHeight: '90vh',
          overflowY: 'auto',
          boxShadow: '0 20px 40px rgba(0,0,0,0.2)',
          padding: '28px',
          position: 'relative',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <div>
            <span style={{ fontSize: '0.75rem', color: '#4F8278', fontWeight: 600, textTransform: 'uppercase' }}>
              OptiGuide Account
            </span>
            <h3 style={{ fontSize: '1.375rem', color: '#073F35', margin: '2px 0 0' }}>
              {isAuthenticated ? 'User Profile & Sessions' : tab === 'login' ? 'Sign In to OptiGuide' : 'Create New Account'}
            </h3>
          </div>
          <button
            onClick={onClose}
            aria-label="Close dialog"
            style={{
              background: '#E9E5DA',
              border: '1px solid #D7D2C4',
              borderRadius: '50%',
              width: '32px',
              height: '32px',
              fontSize: '1rem',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#202823',
            }}
          >
            ✕
          </button>
        </div>

        {/* Tab Switcher if not authenticated */}
        {!isAuthenticated && (
          <div style={{ display: 'flex', gap: '8px', marginBottom: '20px', borderBottom: '1px solid #D7D2C4', paddingBottom: '12px' }}>
            <button
              onClick={() => { setTab('login'); setError(null); }}
              style={{
                flex: 1,
                padding: '8px',
                border: tab === 'login' ? '2px solid #073F35' : '1px solid #D7D2C4',
                backgroundColor: tab === 'login' ? '#073F35' : '#E9E5DA',
                color: tab === 'login' ? '#F7F4EC' : '#202823',
                borderRadius: '6px',
                fontWeight: 600,
                cursor: 'pointer',
              }}
            >
              Sign In
            </button>
            <button
              onClick={() => { setTab('register'); setError(null); }}
              style={{
                flex: 1,
                padding: '8px',
                border: tab === 'register' ? '2px solid #073F35' : '1px solid #D7D2C4',
                backgroundColor: tab === 'register' ? '#073F35' : '#E9E5DA',
                color: tab === 'register' ? '#F7F4EC' : '#202823',
                borderRadius: '6px',
                fontWeight: 600,
                cursor: 'pointer',
              }}
            >
              Register
            </button>
          </div>
        )}

        {/* Error / Success Alerts */}
        {error && (
          <div
            style={{
              backgroundColor: '#FDEDEC',
              border: '1px solid #F5B7B1',
              borderRadius: '6px',
              padding: '12px',
              color: '#A9473E',
              fontSize: '0.875rem',
              marginBottom: '16px',
            }}
          >
            ⚠️ {error}
          </div>
        )}

        {successMsg && (
          <div
            style={{
              backgroundColor: '#EDF7ED',
              border: '1px solid #A9DFBF',
              borderRadius: '6px',
              padding: '12px',
              color: '#28734F',
              fontSize: '0.875rem',
              marginBottom: '16px',
            }}
          >
            ✓ {successMsg}
          </div>
        )}

        {/* ================= LOGIN FORM ================= */}
        {!isAuthenticated && tab === 'login' && (
          <form onSubmit={handleLogin}>
            <div style={{ marginBottom: '16px' }}>
              <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#202823', marginBottom: '6px' }}>
                Email Address
              </label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="user@example.com"
                style={{
                  width: '100%',
                  padding: '10px 14px',
                  borderRadius: '6px',
                  border: '1px solid #D7D2C4',
                  backgroundColor: '#FFFFFF',
                  fontSize: '0.9375rem',
                  boxSizing: 'border-box',
                }}
              />
            </div>

            <div style={{ marginBottom: '20px' }}>
              <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#202823', marginBottom: '6px' }}>
                Password
              </label>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                style={{
                  width: '100%',
                  padding: '10px 14px',
                  borderRadius: '6px',
                  border: '1px solid #D7D2C4',
                  backgroundColor: '#FFFFFF',
                  fontSize: '0.9375rem',
                  boxSizing: 'border-box',
                }}
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              style={{
                width: '100%',
                backgroundColor: '#073F35',
                color: '#F7F4EC',
                border: 'none',
                borderRadius: '6px',
                padding: '12px',
                fontSize: '1rem',
                fontWeight: 600,
                cursor: loading ? 'not-allowed' : 'pointer',
              }}
            >
              {loading ? 'Authenticating...' : 'Sign In'}
            </button>
          </form>
        )}

        {/* ================= REGISTER FORM ================= */}
        {!isAuthenticated && tab === 'register' && (
          <form onSubmit={handleRegister}>
            <div style={{ marginBottom: '14px' }}>
              <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#202823', marginBottom: '6px' }}>
                Full Name
              </label>
              <input
                type="text"
                required
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="Anandita Panda"
                style={{
                  width: '100%',
                  padding: '10px 14px',
                  borderRadius: '6px',
                  border: '1px solid #D7D2C4',
                  backgroundColor: '#FFFFFF',
                  fontSize: '0.9375rem',
                  boxSizing: 'border-box',
                }}
              />
            </div>

            <div style={{ marginBottom: '14px' }}>
              <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#202823', marginBottom: '6px' }}>
                Email Address
              </label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="citizen@example.com"
                style={{
                  width: '100%',
                  padding: '10px 14px',
                  borderRadius: '6px',
                  border: '1px solid #D7D2C4',
                  backgroundColor: '#FFFFFF',
                  fontSize: '0.9375rem',
                  boxSizing: 'border-box',
                }}
              />
            </div>

            <div style={{ marginBottom: '20px' }}>
              <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#202823', marginBottom: '6px' }}>
                Password (min 8 chars, 1 uppercase, 1 number, 1 special)
              </label>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="StrongPassword123!"
                style={{
                  width: '100%',
                  padding: '10px 14px',
                  borderRadius: '6px',
                  border: '1px solid #D7D2C4',
                  backgroundColor: '#FFFFFF',
                  fontSize: '0.9375rem',
                  boxSizing: 'border-box',
                }}
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              style={{
                width: '100%',
                backgroundColor: '#073F35',
                color: '#F7F4EC',
                border: 'none',
                borderRadius: '6px',
                padding: '12px',
                fontSize: '1rem',
                fontWeight: 600,
                cursor: loading ? 'not-allowed' : 'pointer',
              }}
            >
              {loading ? 'Creating Account...' : 'Register Account'}
            </button>
          </form>
        )}

        {/* ================= PROFILE & SESSIONS ================= */}
        {isAuthenticated && (
          <div>
            <div style={{ backgroundColor: '#E9E5DA', borderRadius: '6px', padding: '14px', marginBottom: '20px' }}>
              <div style={{ fontSize: '0.8125rem', color: '#686F69', textTransform: 'uppercase' }}>Current Account</div>
              <div style={{ fontSize: '1.125rem', fontWeight: 700, color: '#073F35' }}>{currentUser?.fullName}</div>
              <div style={{ fontSize: '0.875rem', color: '#202823' }}>{currentUser?.email}</div>
              <div style={{ marginTop: '6px', display: 'inline-block', backgroundColor: '#073F35', color: '#F7F4EC', padding: '2px 8px', borderRadius: '4px', fontSize: '0.75rem', fontWeight: 600, textTransform: 'uppercase' }}>
                Role: {currentUser?.role}
              </div>
            </div>

            {/* Profile Update Form */}
            <form onSubmit={handleUpdateProfile} style={{ marginBottom: '24px' }}>
              <h4 style={{ fontSize: '0.9375rem', color: '#073F35', marginBottom: '12px' }}>Update Profile Details</h4>
              <div style={{ marginBottom: '12px' }}>
                <label style={{ display: 'block', fontSize: '0.8125rem', color: '#686F69', marginBottom: '4px' }}>Full Name</label>
                <input
                  type="text"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  style={{ width: '100%', padding: '8px 12px', borderRadius: '6px', border: '1px solid #D7D2C4', boxSizing: 'border-box' }}
                />
              </div>
              <div style={{ marginBottom: '14px' }}>
                <label style={{ display: 'block', fontSize: '0.8125rem', color: '#686F69', marginBottom: '4px' }}>Phone Number</label>
                <input
                  type="text"
                  value={phoneNumber}
                  onChange={(e) => setPhoneNumber(e.target.value)}
                  placeholder="+91 94371 88204"
                  style={{ width: '100%', padding: '8px 12px', borderRadius: '6px', border: '1px solid #D7D2C4', boxSizing: 'border-box' }}
                />
              </div>
              <button
                type="submit"
                disabled={loading}
                style={{
                  backgroundColor: '#E9E5DA',
                  border: '1px solid #D7D2C4',
                  color: '#073F35',
                  padding: '8px 16px',
                  borderRadius: '6px',
                  fontWeight: 600,
                  cursor: 'pointer',
                }}
              >
                Save Profile Changes
              </button>
            </form>

            {/* Active Sessions Audit */}
            <div style={{ marginBottom: '24px' }}>
              <h4 style={{ fontSize: '0.9375rem', color: '#073F35', marginBottom: '10px' }}>Active Session History ({sessions.length})</h4>
              <div style={{ maxHeight: '160px', overflowY: 'auto', border: '1px solid #D7D2C4', borderRadius: '6px', backgroundColor: '#FFFFFF' }}>
                {sessions.length === 0 ? (
                  <div style={{ padding: '12px', fontSize: '0.8125rem', color: '#686F69' }}>No session audit records found.</div>
                ) : (
                  sessions.map((s, idx) => (
                    <div key={s.id} style={{ padding: '10px 12px', borderBottom: idx < sessions.length - 1 ? '1px solid #E4DFD3' : 'none', fontSize: '0.8125rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <div>
                        <div>Session #{idx + 1} ({s.id.slice(0, 8)}...)</div>
                        <div style={{ fontSize: '0.75rem', color: '#686F69' }}>Created: {new Date(s.created_at).toLocaleString()}</div>
                      </div>
                      <span style={{ color: s.is_revoked ? '#A9473E' : '#28734F', fontWeight: 600 }}>
                        {s.is_revoked ? 'Revoked' : 'Active'}
                      </span>
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* Sign Out Actions */}
            <div style={{ display: 'flex', gap: '10px' }}>
              <button
                type="button"
                onClick={handleLogout}
                disabled={loading}
                style={{
                  flex: 1,
                  backgroundColor: '#E9E5DA',
                  border: '1px solid #D7D2C4',
                  color: '#A9473E',
                  padding: '10px',
                  borderRadius: '6px',
                  fontWeight: 600,
                  cursor: 'pointer',
                }}
              >
                Sign Out (This Device)
              </button>
              <button
                type="button"
                onClick={handleLogoutAll}
                disabled={loading}
                style={{
                  flex: 1,
                  backgroundColor: '#A9473E',
                  border: 'none',
                  color: '#F7F4EC',
                  padding: '10px',
                  borderRadius: '6px',
                  fontWeight: 600,
                  cursor: 'pointer',
                }}
              >
                Sign Out Everywhere
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
