import { Navigate, Route, Routes } from "react-router-dom";

import AppLayout from "@/components/layout/AppLayout";
import LoginPage from "@/pages/LoginPage";
import DashboardPage from "@/pages/DashboardPage";
import ReportsListPage from "@/pages/ReportsListPage";
import CreateReportPage from "@/pages/CreateReportPage";
import ReportDetailPage from "@/pages/ReportDetailPage";
import PatientsListPage from "@/pages/PatientsListPage";
import PatientCreatePage from "@/pages/PatientCreatePage";
import PatientDetailPage from "@/pages/PatientDetailPage";
import CatalogPage from "@/pages/CatalogPage";
import SettingsPage from "@/pages/SettingsPage";
import UsersPage from "@/pages/UsersPage";
import MyReportsPage from "@/pages/MyReportsPage";
import MyProfilePage from "@/pages/MyProfilePage";
import { useAuth } from "@/hooks/useAuth";

export default function App() {
  const { user } = useAuth();
  const isPatient = user?.role_code === "patient";

  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route element={<AppLayout />}>
        <Route
          index
          element={<Navigate to={isPatient ? "/my-reports" : "/dashboard"} replace />}
        />
        {isPatient ? (
          <>
            <Route path="/my-reports" element={<MyReportsPage />} />
            <Route path="/my-profile" element={<MyProfilePage />} />
            <Route path="*" element={<Navigate to="/my-reports" replace />} />
          </>
        ) : (
          <>
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/reports" element={<ReportsListPage />} />
            <Route path="/reports/new" element={<CreateReportPage />} />
            <Route path="/reports/:id" element={<ReportDetailPage />} />
            <Route path="/patients" element={<PatientsListPage />} />
            <Route path="/patients/new" element={<PatientCreatePage />} />
            <Route path="/patients/:id" element={<PatientDetailPage />} />
            <Route path="/catalog" element={<CatalogPage />} />
            <Route path="/users" element={<UsersPage />} />
            <Route path="/settings" element={<SettingsPage />} />
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </>
        )}
      </Route>
    </Routes>
  );
}
