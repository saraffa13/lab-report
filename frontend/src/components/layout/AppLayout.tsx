import { useState } from "react";
import { Navigate, Outlet, Link, useLocation, NavLink } from "react-router-dom";
import { useAuth } from "@/hooks/useAuth";
import { Icon } from "@/components/ui/Icon";

const STAFF_NAV = [
  { to: "/dashboard", label: "Dashboard" },
  { to: "/reports", label: "Reports" },
  { to: "/patients", label: "Patients" },
  { to: "/catalog", label: "Catalog" },
  { to: "/users", label: "Users" },
  { to: "/settings", label: "Settings" },
];

const PATIENT_NAV = [
  { to: "/my-reports", label: "My Reports" },
  { to: "/my-profile", label: "My Profile" },
];

export default function AppLayout() {
  const { user, isAuthenticated, signOut } = useAuth();
  const location = useLocation();
  const [menuOpen, setMenuOpen] = useState(false);

  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  const isPatient = user?.role_code === "patient";
  const NAV = isPatient ? PATIENT_NAV : STAFF_NAV;
  const homeLink = isPatient ? "/my-reports" : "/dashboard";

  return (
    <div className="min-h-screen bg-surface text-on-surface flex flex-col">
      <header className="bg-surface sticky top-0 z-50 shadow-nav">
        <div className="flex justify-between items-center w-full px-6 lg:px-8 h-16 max-w-[1920px] mx-auto">
          <div className="flex items-center gap-8">
            <Link
              to={homeLink}
              className="text-[15px] font-black tracking-tighter text-primary-container uppercase leading-none"
            >
              K S Ganga Medical Clinic
            </Link>
            <nav className="hidden md:flex items-center gap-6">
              {NAV.map((n) => (
                <NavLink
                  key={n.to}
                  to={n.to}
                  className={({ isActive }) =>
                    isActive
                      ? "text-primary-container font-bold border-b-2 border-primary-container pb-1 text-sm transition-all"
                      : "text-on-surface-variant font-medium hover:text-primary-container text-sm transition-colors pb-1"
                  }
                >
                  {n.label}
                </NavLink>
              ))}
            </nav>
          </div>

          <div className="flex items-center gap-3">
            {!isPatient && (
              <>
                <div className="hidden lg:flex items-center bg-surface-container-lowest ring-1 ring-outline-variant/20 rounded-full px-4 py-1.5 focus-within:ring-secondary transition-all">
                  <Icon name="search" size={16} className="text-on-surface-variant mr-2" />
                  <input
                    className="bg-transparent border-none focus:ring-0 text-sm outline-none w-48 text-on-surface placeholder-on-surface-variant/50"
                    placeholder="Search accession, patient..."
                  />
                </div>
                <button className="hidden md:inline-flex text-primary-container hover:bg-surface-container-low p-2 rounded-full transition-all">
                  <Icon name="notifications" size={20} />
                </button>
                <button className="hidden md:inline-flex text-primary-container hover:bg-surface-container-low p-2 rounded-full transition-all">
                  <Icon name="help_outline" size={20} />
                </button>
              </>
            )}

            <div className="relative">
              <button
                onClick={() => setMenuOpen((v) => !v)}
                className="flex items-center gap-2 rounded-full p-1 pr-3 hover:bg-surface-container-low transition-colors"
              >
                <div className="w-8 h-8 rounded-full bg-primary-container text-on-primary flex items-center justify-center text-xs font-bold">
                  {(user?.email ?? "U").slice(0, 2).toUpperCase()}
                </div>
                <Icon name="expand_more" size={16} className="text-on-surface-variant" />
              </button>
              {menuOpen && (
                <div className="absolute right-0 mt-2 w-64 bg-surface-container-lowest rounded-xl ring-1 ring-outline-variant/20 shadow-dossier overflow-hidden">
                  <div className="p-4 border-b border-outline-variant/10">
                    <div className="text-sm font-semibold text-on-surface">{user?.email}</div>
                    {user?.lab && (
                      <div className="text-xs text-on-surface-variant mt-0.5">{user.lab.name}</div>
                    )}
                  </div>
                  <button
                    onClick={signOut}
                    className="w-full text-left px-4 py-2.5 text-sm text-on-surface hover:bg-surface-container-low flex items-center gap-2"
                  >
                    <Icon name="logout" size={16} />
                    Sign out
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      </header>

      <main className="flex-grow w-full max-w-[1920px] mx-auto p-6 lg:p-8">
        <Outlet />
      </main>
    </div>
  );
}
