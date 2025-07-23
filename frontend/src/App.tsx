import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Header } from './components/Header';
import { HomePage } from './pages/HomePage';
import { UploadPage } from './pages/UploadPage';
import { AuditPage } from './pages/AuditPage';
import { ResultsPage } from './pages/ResultsPage';
import { AuditProvider } from './context/AuditContext';
import './App.css';

function App() {
  return (
    <AuditProvider>
      <Router>
        <div className="min-h-screen bg-gray-50">
          <Header />
          <main className="container mx-auto px-4 py-8">
            <Routes>
              <Route path="/" element={<HomePage />} />
              <Route path="/upload" element={<UploadPage />} />
              <Route path="/audit" element={<AuditPage />} />
              <Route path="/results/:auditId" element={<ResultsPage />} />
            </Routes>
          </main>
        </div>
      </Router>
    </AuditProvider>
  );
}

export default App;