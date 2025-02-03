import Footer from "@/components/Footer/Footer";
import { Navbar } from "@/components/Navbar/Navbar";
import { Toaster } from "@/components/ui/sonner";
import { lazy, Suspense } from "react";
import { BrowserRouter, Route, Routes } from "react-router-dom";

const HomePage = lazy(() => import("@/pages/Home/HomePage"));
const FaqPage = lazy(() => import("@/pages/FAQ/FaqPage"));
const GlossaryPage = lazy(() => import("@/pages/Glossary/GlossaryPage"));
const StakePage = lazy(() => import("@/pages/Stake/StakePage"));
const LearnNodePage = lazy(() => import("@/pages/LearnNode/LearnNodePage"));
const DashboardPage = lazy(() => import("@/pages/Dashboard/Dashboard"));

export const AppRouter = () => {
  return (
    <BrowserRouter>
      <Suspense fallback={<div>Loading...</div>}>
        <div className="flex min-h-screen flex-col">
          <Navbar />
          <div className="flex-grow">
            <Routes>
              <Route path="/" element={<HomePage />} />
              <Route path="/faq" element={<FaqPage />} />
              <Route path="/glossary" element={<GlossaryPage />} />
              <Route path="/stake" element={<StakePage />} />
              <Route path="/dashboard" element={<DashboardPage />} />
              <Route path="/learn-node" element={<LearnNodePage />} />
            </Routes>
          </div>
          <Toaster />
          <Footer />
        </div>
      </Suspense>
    </BrowserRouter>
  );
};
