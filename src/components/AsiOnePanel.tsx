import { useState, useEffect } from "react";
import styled from "styled-components";

const Container = styled.div`
  h2 {
    font-size: 28px;
    margin-bottom: ${({ theme }) => theme.spacing.xl};
    color: rgba(0, 0, 0, 0.85);
    font-weight: 600;
  }
`;

const Section = styled.div`
  background: rgba(255, 255, 255, 0.6);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-radius: 12px;
  padding: ${({ theme }) => theme.spacing.xl};
  margin-bottom: ${({ theme }) => theme.spacing.lg};
  border: 0.5px solid rgba(0, 0, 0, 0.1);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);

  h3 {
    font-size: 18px;
    margin-bottom: ${({ theme }) => theme.spacing.lg};
    color: rgba(0, 0, 0, 0.85);
    font-weight: 600;
  }
`;

const InfoBox = styled.div`
  background: rgba(0, 122, 255, 0.1);
  border: 0.5px solid rgba(0, 122, 255, 0.3);
  border-radius: 8px;
  padding: ${({ theme }) => theme.spacing.md};
  margin-bottom: ${({ theme }) => theme.spacing.lg};
  display: flex;
  gap: ${({ theme }) => theme.spacing.sm};

  .material-icons {
    font-size: 20px;
    color: #007aff;
  }

  p {
    font-size: 14px;
    color: rgba(0, 0, 0, 0.7);
    line-height: 1.5;
    margin: 0;
  }
`;

const AgentList = styled.div`
  display: flex;
  flex-direction: column;
  gap: ${({ theme }) => theme.spacing.md};
  margin-top: ${({ theme }) => theme.spacing.lg};
`;

const AgentCard = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: ${({ theme }) => theme.spacing.lg};
  background: rgba(255, 255, 255, 0.8);
  border: 0.5px solid rgba(0, 0, 0, 0.1);
  border-radius: 8px;
  transition: all 0.2s;

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  }
`;

const AgentInfo = styled.div`
  flex: 1;

  .agent-name {
    font-size: 16px;
    font-weight: 600;
    color: rgba(0, 0, 0, 0.85);
    margin-bottom: ${({ theme }) => theme.spacing.xs};
  }

  .agent-address {
    font-size: 12px;
    font-family: "SF Mono", "Monaco", "Courier New", monospace;
    color: rgba(0, 0, 0, 0.5);
    margin-bottom: ${({ theme }) => theme.spacing.xs};
  }

  .agent-description {
    font-size: 14px;
    color: rgba(0, 0, 0, 0.6);
  }
`;

const Button = styled.button<{ $variant?: "primary" | "secondary" | "danger" }>`
  padding: ${({ theme }) => theme.spacing.sm} ${({ theme }) => theme.spacing.lg};
  background: ${({ $variant }) => {
    if ($variant === "danger") return "#ff3b30";
    if ($variant === "primary") return "#007aff";
    return "rgba(255, 255, 255, 0.8)";
  }};
  color: ${({ $variant }) =>
    $variant === "secondary" ? "rgba(0, 0, 0, 0.85)" : "white"};
  border: 0.5px solid
    ${({ $variant }) => {
      if ($variant === "danger") return "#ff3b30";
      if ($variant === "primary") return "#007aff";
      return "rgba(0, 0, 0, 0.2)";
    }};
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: ${({ theme }) => theme.spacing.sm};

  .material-icons {
    font-size: 18px;
  }

  &:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 12px
      ${({ $variant }) => {
        if ($variant === "danger") return "rgba(255, 59, 48, 0.3)";
        if ($variant === "primary") return "rgba(0, 122, 255, 0.3)";
        return "rgba(0, 0, 0, 0.1)";
      }};
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
    transform: none;
  }
`;

const AddAgentForm = styled.div`
  display: flex;
  flex-direction: column;
  gap: ${({ theme }) => theme.spacing.md};
  padding: ${({ theme }) => theme.spacing.lg};
  background: rgba(255, 255, 255, 0.8);
  border: 0.5px solid rgba(0, 0, 0, 0.1);
  border-radius: 8px;
  margin-top: ${({ theme }) => theme.spacing.lg};
`;

const FormGroup = styled.div`
  display: flex;
  flex-direction: column;
  gap: ${({ theme }) => theme.spacing.sm};
`;

const Label = styled.label`
  font-size: 14px;
  font-weight: 600;
  color: rgba(0, 0, 0, 0.75);
`;

const Input = styled.input`
  padding: ${({ theme }) => theme.spacing.sm} ${({ theme }) => theme.spacing.md};
  background: rgba(255, 255, 255, 0.9);
  border: 0.5px solid rgba(0, 0, 0, 0.2);
  border-radius: 8px;
  color: rgba(0, 0, 0, 0.85);
  font-size: 14px;
  font-family: inherit;

  &:focus {
    outline: none;
    border-color: #007aff;
    box-shadow: 0 0 0 3px rgba(0, 122, 255, 0.2);
  }

  &::placeholder {
    color: rgba(0, 0, 0, 0.3);
  }
`;

const TextArea = styled.textarea`
  padding: ${({ theme }) => theme.spacing.sm} ${({ theme }) => theme.spacing.md};
  background: rgba(255, 255, 255, 0.9);
  border: 0.5px solid rgba(0, 0, 0, 0.2);
  border-radius: 8px;
  color: rgba(0, 0, 0, 0.85);
  font-size: 14px;
  font-family: inherit;
  resize: vertical;
  min-height: 80px;

  &:focus {
    outline: none;
    border-color: #007aff;
    box-shadow: 0 0 0 3px rgba(0, 122, 255, 0.2);
  }

  &::placeholder {
    color: rgba(0, 0, 0, 0.3);
  }
`;

const ButtonGroup = styled.div`
  display: flex;
  gap: ${({ theme }) => theme.spacing.sm};
`;

interface Agent {
  id: string;
  name: string;
  address: string;
  description: string;
}

interface AsiOnePanelProps {
  onShowToast: (message: string, type: "success" | "error" | "info") => void;
}

export default function AsiOnePanel({ onShowToast }: AsiOnePanelProps) {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [showAddForm, setShowAddForm] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [isSavingKeys, setIsSavingKeys] = useState(false);

  const [asiOneKey, setAsiOneKey] = useState("");
  const [agentverseKey, setAgentverseKey] = useState("");

  const [newAgent, setNewAgent] = useState({
    name: "",
    address: "",
    description: "",
  });

  useEffect(() => {
    loadAgents();
    loadApiKeys();
  }, []);

  const loadApiKeys = async () => {
    try {
      const response = await fetch("http://127.0.0.1:8765/api/asi/keys");
      const data = await response.json();

      if (data.asi_one_key) {
        setAsiOneKey(data.asi_one_key);
      }
      if (data.agentverse_key) {
        setAgentverseKey(data.agentverse_key);
      }
    } catch (error) {
      console.error("Error loading API keys:", error);
    }
  };
  const loadAgents = async () => {
    try {
      const response = await fetch("http://127.0.0.1:8765/api/asi/agents");
      const data = await response.json();

      if (data.agents) {
        setAgents(data.agents);
      }
    } catch (error) {
      console.error("Error loading agents:", error);
    }
  };

  const handleAddAgent = async () => {
    if (!newAgent.name || !newAgent.address) {
      onShowToast("Name and address are required", "error");
      return;
    }

    setIsLoading(true);
    try {
      const response = await fetch("http://127.0.0.1:8765/api/asi/agents", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(newAgent),
      });

      if (!response.ok) {
        const error = await response.json();
        onShowToast(error.detail || "Failed to add agent", "error");
        setIsLoading(false);
        return;
      }

      const data = await response.json();

      if (data.success) {
        onShowToast("Agent added successfully!", "success");
        setNewAgent({ name: "", address: "", description: "" });
        setShowAddForm(false);
        loadAgents();
      }
    } catch (error) {
      console.error("Error adding agent:", error);
      onShowToast("Failed to add agent", "error");
    } finally {
      setIsLoading(false);
    }
  };

  const handleRemoveAgent = async (agentId: string) => {
    if (!confirm("Are you sure you want to remove this agent?")) {
      return;
    }

    try {
      const response = await fetch(
        `http://127.0.0.1:8765/api/asi/agents/${agentId}`,
        {
          method: "DELETE",
        }
      );

      if (!response.ok) {
        const error = await response.json();
        onShowToast(error.detail || "Failed to remove agent", "error");
        return;
      }

      onShowToast("Agent removed", "success");
      loadAgents();
    } catch (error) {
      console.error("Error removing agent:", error);
      onShowToast("Failed to remove agent", "error");
    }
  };

  const handleSaveApiKeys = async () => {
    if (!asiOneKey) {
      onShowToast("ASI One API key is required", "error");
      return;
    }

    setIsSavingKeys(true);
    try {
      const response = await fetch("http://127.0.0.1:8765/api/asi/keys", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          asi_one_key: asiOneKey,
          agentverse_key: agentverseKey,
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        onShowToast(error.detail || "Failed to save API keys", "error");
        setIsSavingKeys(false);
        return;
      }

      onShowToast("API keys saved successfully!", "success");
    } catch (error) {
      console.error("Error saving API keys:", error);
      onShowToast("Failed to save API keys", "error");
    } finally {
      setIsSavingKeys(false);
    }
  };

  return (
    <Container>
      <h2>ASI One Integration</h2>

      <Section>
        <h3>API Keys</h3>
        <InfoBox>
          <span className="material-icons">vpn_key</span>
          <div>
            <p>
              You need <strong>two API keys</strong>: one for ASI One (to use AI
              reasoning) and one for Agentverse (to directly call specific
              agents).
            </p>
          </div>
        </InfoBox>

        <FormGroup>
          <Label>ASI One API Key *</Label>
          <Input
            type="password"
            placeholder="Enter your ASI One API key"
            value={asiOneKey}
            onChange={(e) => setAsiOneKey(e.target.value)}
          />
          <p
            style={{
              fontSize: "12px",
              color: "rgba(0, 0, 0, 0.5)",
              marginTop: "4px",
            }}
          >
            Get from{" "}
            <a
              href="https://asi1.ai/"
              target="_blank"
              rel="noopener noreferrer"
              style={{ color: "#007aff" }}
            >
              asi1.ai
            </a>{" "}
            (Developer Section → Create New)
          </p>
        </FormGroup>

        <FormGroup>
          <Label>Agentverse API Key (Optional)</Label>
          <Input
            type="password"
            placeholder="Enter your Agentverse API key"
            value={agentverseKey}
            onChange={(e) => setAgentverseKey(e.target.value)}
          />
          <p
            style={{
              fontSize: "12px",
              color: "rgba(0, 0, 0, 0.5)",
              marginTop: "4px",
            }}
          >
            Get from{" "}
            <a
              href="https://agentverse.ai/"
              target="_blank"
              rel="noopener noreferrer"
              style={{ color: "#007aff" }}
            >
              agentverse.ai
            </a>{" "}
            (Profile → API Keys)
          </p>
        </FormGroup>

        <Button
          $variant="primary"
          onClick={handleSaveApiKeys}
          disabled={isSavingKeys}
        >
          <span className="material-icons">save</span>
          {isSavingKeys ? "Saving..." : "Save API Keys"}
        </Button>
      </Section>

      <Section>
        <h3>About ASI One & Agentverse</h3>
        <InfoBox>
          <span className="material-icons">info</span>
          <div>
            <p>
              <strong>ASI One</strong> is Fetch.ai's Web3-native LLM with{" "}
              <strong>automatic agent discovery</strong>. It can find and use
              ANY public agent from the <strong>Agentverse marketplace</strong>{" "}
              without any setup.
            </p>
            <p style={{ marginTop: "8px" }}>
              Type{" "}
              <code
                style={{
                  background: "rgba(0, 0, 0, 0.05)",
                  padding: "2px 6px",
                  borderRadius: "4px",
                  fontFamily: "monospace",
                }}
              >
                @asi your question
              </code>{" "}
              and ASI One will automatically search the marketplace, select the
              best agents, and orchestrate them to answer you.
            </p>
            <p
              style={{
                marginTop: "8px",
                fontSize: "13px",
                color: "rgba(0, 0, 0, 0.6)",
              }}
            >
              <strong>Advanced:</strong> You can also explicitly mention an
              agent:
              <br />
              <code
                style={{
                  background: "rgba(0, 0, 0, 0.05)",
                  padding: "2px 6px",
                  borderRadius: "4px",
                  fontFamily: "monospace",
                  fontSize: "12px",
                }}
              >
                @asi @agent1q2w3e4... get weather for Tokyo
              </code>
            </p>
          </div>
        </InfoBox>
      </Section>

      <Section>
        <h3>Favorite Agents (Optional)</h3>
        <InfoBox>
          <span className="material-icons">bookmark</span>
          <div>
            <p>
              Bookmark your favorite agents from the{" "}
              <a
                href="https://agentverse.ai/marketplace"
                target="_blank"
                rel="noopener noreferrer"
                style={{ color: "#007aff" }}
              >
                Agentverse Marketplace
              </a>
              . ASI One will prioritize these agents when relevant to your
              queries.
            </p>
            <p
              style={{
                marginTop: "8px",
                fontSize: "13px",
                color: "rgba(0, 0, 0, 0.6)",
              }}
            >
              <strong>Note:</strong> ASI One can discover and use agents even if
              you haven't bookmarked any. This list just helps it know your
              preferences.
            </p>
          </div>
        </InfoBox>

        {agents.length === 0 && !showAddForm && (
          <InfoBox
            style={{
              marginTop: "1rem",
              background: "rgba(255, 193, 7, 0.1)",
              border: "0.5px solid rgba(255, 193, 7, 0.3)",
            }}
          >
            <span className="material-icons" style={{ color: "#ffc107" }}>
              lightbulb
            </span>
            <p style={{ color: "rgba(0, 0, 0, 0.7)" }}>
              No favorites yet. ASI One will still work perfectly - it can find
              any public agent automatically!
            </p>
          </InfoBox>
        )}

        <AgentList>
          {agents.map((agent) => (
            <AgentCard key={agent.id}>
              <AgentInfo>
                <div className="agent-name">{agent.name}</div>
                <div className="agent-address">{agent.address}</div>
                {agent.description && (
                  <div className="agent-description">{agent.description}</div>
                )}
              </AgentInfo>
              <Button
                $variant="danger"
                onClick={() => handleRemoveAgent(agent.id)}
              >
                <span className="material-icons">delete</span>
                Remove
              </Button>
            </AgentCard>
          ))}
        </AgentList>

        {!showAddForm && (
          <Button
            $variant="primary"
            onClick={() => setShowAddForm(true)}
            style={{ marginTop: agents.length > 0 ? "1rem" : "0" }}
          >
            <span className="material-icons">add</span>
            Add Agent
          </Button>
        )}

        {showAddForm && (
          <AddAgentForm>
            <FormGroup>
              <Label>Agent Name *</Label>
              <Input
                type="text"
                placeholder="e.g., Weather Agent"
                value={newAgent.name}
                onChange={(e) =>
                  setNewAgent({ ...newAgent, name: e.target.value })
                }
              />
            </FormGroup>

            <FormGroup>
              <Label>Agent Address *</Label>
              <Input
                type="text"
                placeholder="agent1q..."
                value={newAgent.address}
                onChange={(e) =>
                  setNewAgent({ ...newAgent, address: e.target.value })
                }
              />
            </FormGroup>

            <FormGroup>
              <Label>Description</Label>
              <TextArea
                placeholder="What does this agent do?"
                value={newAgent.description}
                onChange={(e) =>
                  setNewAgent({ ...newAgent, description: e.target.value })
                }
              />
            </FormGroup>

            <ButtonGroup>
              <Button
                $variant="primary"
                onClick={handleAddAgent}
                disabled={isLoading}
              >
                <span className="material-icons">save</span>
                {isLoading ? "Adding..." : "Add Agent"}
              </Button>
              <Button
                $variant="secondary"
                onClick={() => {
                  setShowAddForm(false);
                  setNewAgent({ name: "", address: "", description: "" });
                }}
              >
                Cancel
              </Button>
            </ButtonGroup>
          </AddAgentForm>
        )}
      </Section>

      <Section>
        <h3>How to Use</h3>
        <ol
          style={{
            color: "rgba(0, 0, 0, 0.7)",
            lineHeight: 1.8,
            paddingLeft: "1.5rem",
          }}
        >
          <li>
            <strong>Get an API key:</strong> Sign up at{" "}
            <a
              href="https://asi1.ai"
              target="_blank"
              rel="noopener noreferrer"
              style={{ color: "#007aff" }}
            >
              asi1.ai
            </a>{" "}
            and navigate to the Developer Section to create a new API key.
          </li>
          <li>
            <strong>Add your API key above</strong> and save it.
          </li>
          <li>
            <strong>(Optional)</strong> Browse the{" "}
            <a
              href="https://agentverse.ai/marketplace"
              target="_blank"
              rel="noopener noreferrer"
              style={{ color: "#007aff" }}
            >
              Agentverse Marketplace
            </a>{" "}
            and bookmark your favorite agents by adding their addresses below.
          </li>
          <li>
            <strong>Use ASI One:</strong> Type{" "}
            <code
              style={{
                background: "rgba(0, 0, 0, 0.05)",
                padding: "2px 6px",
                borderRadius: "4px",
                fontFamily: "monospace",
              }}
            >
              @asi your question
            </code>{" "}
            in Pointer's input field.
          </li>
          <li>
            ASI One will automatically discover and coordinate with the best
            agents from the marketplace to answer your query. Your bookmarked
            agents will be prioritized when relevant.
          </li>
        </ol>
      </Section>
    </Container>
  );
}
