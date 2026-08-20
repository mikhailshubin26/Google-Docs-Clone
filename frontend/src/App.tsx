// Корневой компонент

import { AuthProvider, useAuth } from "./context/AuthContext";
import { LoginPage } from "./pages/LoginPage";

function AppContent() {
  const { tokens } = useAuth();

  if (!tokens) {
    return <LoginPage />;
  }

  return <p>Logged in! Document list comming next.</p>
}

function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  )
}

export default App;