import { useState, useEffect } from "react";
import { invoke } from "@tauri-apps/api/core";
import { motion, AnimatePresence } from "framer-motion";
import { ThemeProvider } from "styled-components";
import styled from "styled-components";
import Sidebar from "./components/Sidebar";
import SettingsPanel from "./components/SettingsPanel";
import Toast from "./components/Toast";
import { useSettings } from "./hooks/useSettings";
import { theme } from "./styles/theme";
import { GlobalStyles } from "./styles/GlobalStyles";

interface ToastMessage {
  id: number;
  message: string;
  type: "success" | "error" | "info";
}

interface HotkeyContext {
  position: { x: number; y: number };
  selected_text: string;
  has_screenshot: boolean;
  timestamp: number;
}

const AppContainer = styled.div`
  display: flex;
  flex-direction: column;
  height: 100vh;
  width: 100vw;
  background: ${({ theme }) => theme.colors.primaryLight};
`;

const TopBar = styled.div`
  background: ${({ theme }) => theme.colors.primaryLight};
  border-bottom: 1px solid ${({ theme }) => theme.colors.tertiaryLight};
  display: flex;
  flex-direction: column;
  padding: ${({ theme }) => theme.spacing.lg} ${({ theme }) => theme.spacing.xl};
  box-shadow: ${({ theme }) => theme.shadow.sm};
  z-index: 100;
`;

const TopRow = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: ${({ theme }) => theme.spacing.sm};
`;

const BottomRow = styled.div`
  display: flex;
  align-items: center;
  justify-content: flex-end;
`;

const Logo = styled.div`
  display: flex;
  align-items: center;
  gap: ${({ theme }) => theme.spacing.md};
  font-size: 24px;
  font-weight: 700;
  color: ${({ theme }) => theme.colors.textDark};
`;

const PoweredBy = styled.div`
  display: flex;
  align-items: center;
  gap: ${({ theme }) => theme.spacing.sm};
  font-size: 14px;
  color: ${({ theme }) => theme.colors.textGray};
`;

const Highlight = styled.span`
  color: ${({ theme }) => theme.colors.accentBlue};
  font-weight: 600;
`;

const ConnectionStatus = styled.div`
  display: flex;
  align-items: center;
  gap: ${({ theme }) => theme.spacing.sm};
`;

const StatusDot = styled.div<{ $isActive: boolean }>`
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: ${({ theme, $isActive }) =>
    $isActive ? theme.colors.successGreen : theme.colors.errorRed};
  animation: ${({ $isActive }) => ($isActive ? "pulse 2s infinite" : "none")};
`;

const MainContent = styled.div`
  display: flex;
  flex: 1;
  overflow: hidden;
`;

const ToastContainer = styled.div`
  position: fixed;
  bottom: ${({ theme }) => theme.spacing.xl};
  right: ${({ theme }) => theme.spacing.xl};
  z-index: 2000;
  display: flex;
  flex-direction: column;
  gap: ${({ theme }) => theme.spacing.sm};
`;

function App() {
  const [activeModule, setActiveModule] = useState("general");
  const [toasts, setToasts] = useState<ToastMessage[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const { settings, updateSettings } = useSettings();

  useEffect(() => {
    let ws: WebSocket | null = null;
    let reconnectTimeout: ReturnType<typeof setTimeout> | null = null;
    let reconnectAttempts = 0;
    const maxReconnectAttempts = 10;

    const connect = () => {
      try {
        console.log("🔌 Attempting to connect to backend...");
        ws = new WebSocket("ws://127.0.0.1:8765/ws");

        ws.onopen = () => {
          console.log("✅ Connected to Pointer backend");
          setIsConnected(true);
          reconnectAttempts = 0;
          showToast("Connected to Pointer backend", "success");
        };

        ws.onmessage = (event) => {
          try {
            const message = JSON.parse(event.data);
            console.log("🎯 FRONTEND RECEIVED MESSAGE:", message);
            console.log("Message type:", message.type);
            console.log("Message data:", message.data);

            if (message.type === "hotkey-pressed") {
              console.log(
                "✅ Hotkey message detected, calling handleHotkeyPress..."
              );
              handleHotkeyPress(message.data);
            } else {
              console.log("⚠️ Unknown message type:", message.type);
            }
          } catch (error) {
            console.error("❌ Error parsing message:", error);
          }
        };

        ws.onerror = (error) => {
          console.error("❌ WebSocket error:", error);
          setIsConnected(false);
        };

        ws.onclose = (event) => {
          console.log("🔌 WebSocket closed:", event.code);
          setIsConnected(false);

          if (event.code !== 1000 && reconnectAttempts < maxReconnectAttempts) {
            reconnectAttempts++;
            reconnectTimeout = setTimeout(connect, 2000);
          } else if (reconnectAttempts >= maxReconnectAttempts) {
            showToast("Failed to connect to backend", "error");
          }
        };
      } catch (error) {
        console.error("Failed to create WebSocket:", error);
        setIsConnected(false);
      }
    };

    const initialTimeout = setTimeout(connect, 500);

    return () => {
      clearTimeout(initialTimeout);
      if (reconnectTimeout) clearTimeout(reconnectTimeout);
      if (ws) ws.close(1000, "Component unmounting");
    };
  }, []);

  const handleHotkeyPress = async (context: HotkeyContext) => {
    console.log("🔥 Hotkey pressed, showing system-wide overlay:", context);

    try {
      // Show overlay window at cursor position
      await invoke("show_overlay", {
        x: context.position.x,
        y: context.position.y,
        context: {
          selected_text: context.selected_text,
          has_screenshot: context.has_screenshot,
        },
      });
    } catch (error) {
      console.error("Failed to show overlay:", error);
      showToast("Failed to show overlay", "error");
    }
  };

  const showToast = (message: string, type: ToastMessage["type"]) => {
    const id = Date.now();
    setToasts((prev) => [...prev, { id, message, type }]);
  };

  const removeToast = (id: number) => {
    setToasts((prev) => prev.filter((toast) => toast.id !== id));
  };

  return (
    <ThemeProvider theme={theme}>
      <GlobalStyles />
      <AppContainer>
        <TopBar>
          <TopRow>
            <Logo>
              <svg width="28" height="28" viewBox="0 0 24 24" fill="none">
                <path
                  d="M12 2L2 7L12 12L22 7L12 2Z"
                  fill={theme.colors.accentBlue}
                />
                <path
                  d="M2 17L12 22L22 17"
                  stroke={theme.colors.accentBlue}
                  strokeWidth="2"
                />
              </svg>
              <span>Pointer Settings</span>
            </Logo>
            <ConnectionStatus>
              <StatusDot $isActive={isConnected} />
              <span>{isConnected ? "Connected" : "Disconnected"}</span>
            </ConnectionStatus>
          </TopRow>
          <BottomRow>
            <PoweredBy>
              <span>Powered by</span>
              <Highlight>FetchAI and Gemini</Highlight>
            </PoweredBy>
          </BottomRow>
        </TopBar>

        <MainContent>
          <Sidebar
            activeModule={activeModule}
            onModuleChange={setActiveModule}
          />
          <SettingsPanel
            activeModule={activeModule}
            settings={settings}
            onSettingsChange={updateSettings}
          />
        </MainContent>

        <ToastContainer>
          <AnimatePresence>
            {toasts.map((toast) => (
              <Toast
                key={toast.id}
                message={toast.message}
                type={toast.type}
                onClose={() => removeToast(toast.id)}
              />
            ))}
          </AnimatePresence>
        </ToastContainer>
      </AppContainer>
    </ThemeProvider>
  );
}

export default App;
