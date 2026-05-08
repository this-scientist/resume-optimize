import type { ReactNode } from "react";
import { Link, Navigate, Route, Routes } from "react-router-dom";
import { JobDetailPage } from "./pages/JobDetailPage";
import { JobsPage } from "./pages/JobsPage";
import { KnowledgePage } from "./pages/KnowledgePage";
import { ResumeEditPage } from "./pages/ResumeEditPage";
import { ResumeListPage } from "./pages/ResumeListPage";
import { SettingsPage } from "./pages/SettingsPage";

function Layout({ children }: { children: ReactNode }) {
  return (
    <>
      <nav className="nav">
        <Link to="/knowledge">面试知识</Link>
        <Link to="/resumes">简历</Link>
        <Link to="/jobs">岗位</Link>
        <Link to="/settings">设置</Link>
      </nav>
      {children}
    </>
  );
}

export default function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Navigate to="/resumes" replace />} />
        <Route path="/knowledge" element={<KnowledgePage />} />
        <Route path="/resumes" element={<ResumeListPage />} />
        <Route path="/resumes/:id" element={<ResumeEditPage />} />
        <Route path="/jobs" element={<JobsPage />} />
        <Route path="/jobs/:id" element={<JobDetailPage />} />
        <Route path="/settings" element={<SettingsPage />} />
      </Routes>
    </Layout>
  );
}
