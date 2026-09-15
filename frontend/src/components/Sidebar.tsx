import React from 'react'
import { NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import {
  LayoutDashboard, Building2, SlidersHorizontal,
  FileSpreadsheet, Clock, LogOut
} from 'lucide-react'

const NAV = [
  { to: '/',          icon: <LayoutDashboard size={16} />,    label: 'Overview'  },
  { to: '/companies', icon: <Building2 size={16} />,          label: 'Companies' },
  { to: '/filters',   icon: <SlidersHorizontal size={16} />,  label: 'Filters'   },
  { to: '/jobs',      icon: <FileSpreadsheet size={16} />,    label: 'Jobs'      },
  { to: '/runs',      icon: <Clock size={16} />,              label: 'Runs'      },
  { to: '/exports',   icon: <FileSpreadsheet size={16} />,    label: 'Exports'   },
]

export default function Sidebar() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <aside className="sidebar">
      {/* Logo */}
      <div className="sidebar-logo">
        <div className="logo-mark">
          <div className="logo-icon">🔍</div>
          <div>
            <div className="logo-text">Job Scraper</div>
            <div className="logo-sub">Enterprise</div>
          </div>
        </div>
      </div>

      {/* Nav */}
      <nav className="sidebar-nav">
        <div className="nav-section-label">Navigation</div>
        {NAV.map(({ to, icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`}
          >
            {icon}
            {label}
          </NavLink>
        ))}
      </nav>

      {/* User chip */}
      <div className="sidebar-footer">
        <div className="user-chip">
          <div className="user-avatar">
            {user?.email?.[0]?.toUpperCase() ?? 'A'}
          </div>
          <div className="user-info">
            <div className="user-email">{user?.email}</div>
            <div className="user-role">{user?.role}</div>
          </div>
          <button className="logout-btn" onClick={handleLogout} title="Sign out">
            <LogOut size={15} />
          </button>
        </div>
      </div>
    </aside>
  )
}
