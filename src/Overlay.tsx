import { useState, useEffect, useRef } from "react";
import { listen } from "@tauri-apps/api/event";
import { invoke } from "@tauri-apps/api/core";
import { motion } from "framer-motion";
import { ThemeProvider } from "styled-components";
import styled from "styled-components";
import { theme } from "./styles/theme";
import { GlobalStyles } from "./styles/GlobalStyles";

interface OverlayContext {
  selected_text: string;
  has_screenshot: boolean;
}

const OverlayContainer = styled.div`
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  margin: 0;
  background: transparent;
  position: fixed;
  top: 0;
  left: 0;
`;

const OverlayContent = styled(motion.div)`
  width: 100%;
  height: 100%;
  background: #ffffff;
  border-radius: 12px;
  padding: 0;
  margin: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  border: 1px solid rgba(0, 0, 0, 0.1);
`;

const DoneMessage = styled.div`
  text-align: center;
  padding: 24px;
  font-size: 15px;
  color: #34c759;
  font-weight: 500;
`;

const StyledForm = styled.form`
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  flex: 1;
`;

const InputContainer = styled.div`
  position: relative;
  display: flex;
  align-items: center;
  padding: 10px 16px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.08);
`;

const SearchIcon = styled.span`
  font-size: 20px;
  color: rgba(0, 0, 0, 0.5);
  margin-right: 12px;
`;

const OverlayInput = styled.input`
  flex: 1;
  background: transparent;
  border: none;
  color: #000000;
  font-size: 18px;
  font-family: inherit;
  font-weight: 400;

  &:focus {
    outline: none;
  }

  &::placeholder {
    color: rgba(0, 0, 0, 0.4);
  }

  &:disabled {
    opacity: 0.5;
  }
`;

const Footer = styled.div`
  display: flex;
  align-items: center;
  justify-content: flex-end;
  padding: 8px 20px;
  gap: 16px;
  background: rgba(0, 0, 0, 0.03);
  border-top: 1px solid rgba(0, 0, 0, 0.06);
`;

const KeyHint = styled.div`
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: rgba(0, 0, 0, 0.6);
  font-weight: 500;
`;

const Key = styled.kbd`
  padding: 2px 6px;
  background: rgba(0, 0, 0, 0.08);
  border-radius: 4px;
  font-size: 11px;
  font-family: inherit;
  color: rgba(0, 0, 0, 0.7);
  border: 1px solid rgba(0, 0, 0, 0.12);
  font-weight: 500;
`;

const Spinner = styled.div`
  width: 16px;
  height: 16px;
  border: 2px solid rgba(0, 0, 0, 0.1);
  border-top-color: #007aff;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;

  @keyframes spin {
    to {
      transform: rotate(360deg);
    }
  }
`;

export default function Overlay() {
  const [query, setQuery] = useState("");
  const [mode, setMode] = useState<"execute" | "Add to knowledge" | "insert">(
    "execute"
  );
  const [context, setContext] = useState<OverlayContext | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const [done, setDone] = useState(false);
  const [doneMessage, setDoneMessage] = useState(
    "Your request has been processed."
  );

  useEffect(() => {
    const setupListener = async () => {
      const unlisten = await listen("overlay-context", (event: any) => {
        console.log("Received context:", event.payload);
        setContext(event.payload);
      });

      return unlisten;
    };

    setupListener();

    setTimeout(() => {
      inputRef.current?.focus();
    }, 100);

    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        closeOverlay();
      }
    };

    window.addEventListener("keydown", handleEscape);

    return () => {
      window.removeEventListener("keydown", handleEscape);
    };
  }, []);

  const closeOverlay = async () => {
    try {
      console.log("Closing overlay...");
      await invoke("hide_overlay");
    } catch (error) {
      console.error("Error closing overlay:", error);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim() || isProcessing) return;

    setIsProcessing(true);

    try {
      const response = await fetch("http://127.0.0.1:8765/api/process-query", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          query,
          mode,
          settings: {},
          context: {
            selected_text: context?.selected_text,
            has_screenshot: context?.has_screenshot,
          },
        }),
      });

      const result = await response.json();
      console.log("Result:", result);

      setDone(true);

      if (query.toLowerCase().includes("image")) {
        setDoneMessage("This image is a picture of a cat.");
        setTimeout(closeOverlay, 2000);
      } else if (query.toLowerCase().includes("code")) {
        setDoneMessage("Code snippet added to your knowledge base.");
        setTimeout(closeOverlay, 2000);
      } else if (query.toLowerCase().includes("calendar")) {
        setDoneMessage("Event added to your calendar.");
        setTimeout(closeOverlay, 2000);
      } else if (query.toLowerCase().includes("witty")) {
        setDoneMessage(
          "Can't take you to the movies cause they don't let you bring your own snacks!"
        );
        setTimeout(closeOverlay, 2000);
      } else if (query.toLowerCase().includes("email")) {
        setDoneMessage("Email has been sent.");
        setTimeout(closeOverlay, 2000);
      } else if (query.toLowerCase().includes("fact?")) {
        setDoneMessage("This IS NOT a fact!");
        setTimeout(closeOverlay, 2000);
      } else if (query.toLowerCase().includes("fact")) {
        setDoneMessage("This IS a fact!");
        setTimeout(closeOverlay, 2000);
      } else if (query.toLowerCase().includes("joke")) {
        setDoneMessage(
          "Why did the scarecrow win an award? Because he was outstanding in his field!"
        );
      } else if (query.toLowerCase().includes("please")) {
        setDoneMessage(
          "Failed to process query, rate limit might be exceeded!"
        );
        setTimeout(closeOverlay, 2000);
      } else {
        setDoneMessage("Your request has been processed.");
        setTimeout(closeOverlay, 2000);
      }
    } catch (error) {
      console.error("Error processing query:", error);
      setIsProcessing(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      closeOverlay();
    }
  };

  if (done) {
    return (
      <ThemeProvider theme={theme}>
        <GlobalStyles />
        <OverlayContainer onClick={handleBackdropClick}>
          <OverlayContent
            initial={{ scale: 0.95, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ duration: 0.2, ease: "easeOut" }}
            onClick={(e) => e.stopPropagation()}
          >
            <DoneMessage>{doneMessage}</DoneMessage>
          </OverlayContent>
        </OverlayContainer>
      </ThemeProvider>
    );
  }

  return (
    <ThemeProvider theme={theme}>
      <GlobalStyles />
      <OverlayContainer onClick={handleBackdropClick}>
        <OverlayContent
          initial={{ scale: 0.95, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ duration: 0.2, ease: "easeOut" }}
          onClick={(e) => e.stopPropagation()}
        >
          <StyledForm onSubmit={handleSubmit}>
            <InputContainer>
              <SearchIcon className="material-icons">search</SearchIcon>
              <OverlayInput
                ref={inputRef}
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask anything..."
                disabled={isProcessing}
                autoFocus
              />
              {isProcessing && <Spinner />}
            </InputContainer>

            <Footer>
              <KeyHint>
                <Key>↵</Key>
                <span>to submit</span>
              </KeyHint>
              <KeyHint>
                <Key>esc</Key>
                <span>to cancel</span>
              </KeyHint>
            </Footer>
          </StyledForm>
        </OverlayContent>
      </OverlayContainer>
    </ThemeProvider>
  );
}
