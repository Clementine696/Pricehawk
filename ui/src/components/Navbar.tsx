'use client';

import { useAuth } from '@/context/AuthContext';

export default function Navbar() {
  const { user, logout } = useAuth();

  return (
    <nav className="navbar">
      <div className="navbar-brand">
        <h1>PriceHawk</h1>
      </div>
      <div className="navbar-menu">
        {user && (
          <>
            <span className="navbar-user">Welcome, {user.username}</span>
            <button className="navbar-logout" onClick={logout}>
              Logout
            </button>
          </>
        )}
      </div>
    </nav>
  );
}
