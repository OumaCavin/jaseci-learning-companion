# Contributing to Jaseci Learning Companion

Thank you for your interest in contributing to the Jaseci Learning Companion! This document provides guidelines and information for contributors.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How to Contribute](#how-to-contribute)
- [Development Setup](#development-setup)
- [Coding Standards](#coding-standards)
- [Testing Requirements](#testing-requirements)
- [Documentation](#documentation)
- [Pull Request Process](#pull-request-process)
- [Issue Reporting](#issue-reporting)

## 🤝 Code of Conduct

Please read and follow our [Code of Conduct](CODE_OF_CONDUCT.md). We are committed to providing a welcoming and inclusive environment for all contributors.

## 🚀 How to Contribute

We welcome contributions in many forms:

- 🐛 **Bug Reports**: Help us identify and fix issues
- 💡 **Feature Requests**: Suggest new features or improvements
- 📝 **Documentation**: Improve our docs, guides, and examples
- 🔧 **Code Contributions**: Fix bugs, add features, improve performance
- 🧪 **Testing**: Write tests, improve test coverage
- 🎨 **UI/UX**: Enhance the user interface and experience

### Getting Started

1. **Fork the Repository**
   ```bash
   git clone https://github.com/OumaCavin/jaseci-learning-companion.git
   cd jaseci-learning-companion
   ```

2. **Set Up Development Environment**
   ```bash
   # Backend setup
   cd services/core/api_gateway
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   
   # Frontend setup
   cd frontend/web-dashboard
   npm install
   ```

3. **Create a Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

## 💻 Development Setup

### Prerequisites

- **Python 3.11+**
- **Node.js 18+**
- **Docker & Docker Compose**
- **PostgreSQL 15+**
- **Redis 7+**
- **Neo4j 5.0+**

### Docker Development Environment

```bash
# Start all services
docker-compose -f infrastructure/docker/dev/docker-compose.yml up -d

# Check service status
docker-compose -f infrastructure/docker/dev/docker-compose.yml ps

# View logs
docker-compose -f infrastructure/docker/dev/docker-compose.yml logs -f
```

### Local Development

```bash
# Start database services
docker-compose -f infrastructure/docker/dev/docker-compose.yml up -d postgres redis neo4j

# Backend development
cd services/core/api_gateway
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Frontend development (new terminal)
cd frontend/web-dashboard
npm run dev

# Agent development (new terminal)
cd services/orchestrator/agents/learning_progress
python -m learning_progress_agent
```

## 📏 Coding Standards

### Python Code Standards

- **PEP 8** compliance (enforced with Black and flake8)
- **Type hints** required for all functions
- **Docstrings** in Google style format
- **Import organization** using isort

```python
from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class AgentConfig:
    """Configuration for agent initialization.
    
    Attributes:
        name: Human-readable name for the agent
        capabilities: List of agent capabilities
        max_load: Maximum load factor (0.0 to 1.0)
        timeout: Request timeout in seconds
    """
    name: str
    capabilities: List[str]
    max_load: float = 0.8
    timeout: int = 30
    
    def is_available(self, current_load: float) -> bool:
        """Check if agent can handle more requests.
        
        Args:
            current_load: Current load factor of the agent
            
        Returns:
            True if agent can accept new requests
        """
        return current_load < self.max_load
```

### JavaScript/TypeScript Standards

- **ESLint + Prettier** for code formatting
- **TypeScript strict mode**
- **Component documentation** with JSDoc
- **React hooks** for state management

```typescript
interface AgentStatus {
  agentId: string;
  status: 'active' | 'busy' | 'idle' | 'failed';
  loadFactor: number;
  lastHeartbeat: Date;
}

interface AgentMonitorProps {
  agents: Record<string, AgentStatus>;
  onAgentAction: (agentId: string, action: string) => void;
}

/**
 * Component for monitoring multiple agent status in real-time
 */
export const AgentMonitor: React.FC<AgentMonitorProps> = ({
  agents,
  onAgentAction
}) => {
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null);
  
  return (
    <div className="agent-monitor">
      {/* Implementation */}
    </div>
  );
};
```

### Database Standards

- **PostgreSQL** for relational data
- **Neo4j** for graph data (OSP, CCG)
- **Redis** for caching and sessions
- **Proper indexing** for performance
- **Migration scripts** for schema changes

### API Standards

- **RESTful** design principles
- **OpenAPI/Swagger** documentation
- **Proper HTTP status codes**
- **Input validation** with Pydantic
- **Error handling** with meaningful messages

## 🧪 Testing Requirements

### Test Coverage Targets

- **Unit Tests**: 98%+ coverage
- **Integration Tests**: Complete workflow coverage
- **E2E Tests**: Full user journey coverage
- **Performance Tests**: Load testing for scalability

### Running Tests

```bash
# All tests
make test-all

# Unit tests with coverage
pytest tests/unit/ -v --cov=services --cov-report=html

# Integration tests
pytest tests/integration/ -v

# E2E tests
pytest tests/e2e/ -v --headless

# Performance tests
pytest tests/performance/ -v

# Frontend tests
cd frontend/web-dashboard
npm run test
npm run test:e2e
```

### Writing Tests

```python
import pytest
import asyncio
from unittest.mock import Mock, patch

from services.orchestrator.learning_progress_agent import LearningProgressAgent

class TestLearningProgressAgent:
    @pytest.fixture
    def agent(self):
        return LearningProgressAgent(agent_id="test_agent")
    
    @pytest.mark.asyncio
    async def test_calculate_mastery_score(self, agent):
        """Test mastery score calculation logic."""
        # Arrange
        user_data = {
            "completed_lessons": ["walker_intro", "osp_basics"],
            "quiz_scores": [85, 92],
            "time_spent": 1200
        }
        
        # Act
        result = await agent.calculate_mastery_score(user_data)
        
        # Assert
        assert result["overall_score"] > 0.8
        assert result["weak_areas"] is not None
        assert len(result["recommendations"]) > 0
```

```typescript
// Frontend test example
import { render, screen, fireEvent } from '@testing-library/react';
import { AgentMonitor } from '../AgentMonitor';

describe('AgentMonitor', () => {
  const mockAgents = {
    'agent_1': {
      agentId: 'agent_1',
      status: 'active',
      loadFactor: 0.3,
      lastHeartbeat: new Date()
    }
  };
  
  it('should display agent status correctly', () => {
    const onAgentAction = jest.fn();
    
    render(<AgentMonitor agents={mockAgents} onAgentAction={onAgentAction} />);
    
    expect(screen.getByText('agent_1')).toBeInTheDocument();
    expect(screen.getByText('active')).toBeInTheDocument();
  });
});
```

## 📚 Documentation

### Required Documentation

- **API documentation** for all endpoints
- **Component documentation** for React components
- **Architecture decisions** in `/docs/adr/`
- **User guides** for complex features
- **README updates** for new features

### Documentation Tools

- **Markdown** for most documentation
- **Sphinx** for API documentation
- **Storybook** for component documentation
- **Mermaid** for diagrams

```markdown
## API Documentation

### POST /api/v1/agents/learning-progress

Calculate learning progress for a user.

**Request Body:**
```json
{
  "user_id": "user_123",
  "lesson_id": "walker_intro",
  "completion_score": 0.85
}
```

**Response:**
```json
{
  "progress_id": "progress_456",
  "mastery_level": 0.85,
  "next_recommendations": ["osp_basics", "byllm_intro"],
  "estimated_completion_time": 3600
}
```
```

## 🔄 Pull Request Process

### Before Submitting

1. **Run all tests**: `make test-all`
2. **Check code quality**: `make lint`
3. **Update documentation**: Include doc updates
4. **Add tests**: Ensure new features are tested
5. **Update changelog**: Document your changes

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix (non-breaking change)
- [ ] New feature (non-breaking change)
- [ ] Breaking change (fix or feature)
- [ ] Documentation update
- [ ] Performance improvement

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] E2E tests pass
- [ ] Manual testing completed

## Documentation
- [ ] API documentation updated
- [ ] Component documentation updated
- [ ] User guide updated

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Code is well-commented
- [ ] No breaking changes (or properly documented)
```

### Review Process

1. **Automated Checks**: CI/CD pipeline validation
2. **Code Review**: Two approvals required
3. **Testing Review**: Ensure test coverage
4. **Documentation Review**: Verify docs completeness
5. **Security Review**: Check for security issues

## 🐛 Issue Reporting

### Bug Reports

Include the following information:

- **Environment**: OS, browser, Python version, etc.
- **Steps to Reproduce**: Detailed reproduction steps
- **Expected Behavior**: What should happen
- **Actual Behavior**: What actually happens
- **Screenshots**: If applicable
- **Error Messages**: Complete error logs

### Feature Requests

- **Problem Description**: What problem does this solve?
- **Proposed Solution**: How should this work?
- **Alternatives**: Other solutions considered
- **Additional Context**: Any other relevant information

## 🎯 Development Workflow

### Commit Messages

Follow conventional commits:

```
feat(agent): add adaptive learning capabilities
fix(api): resolve authentication timeout issue
docs(readme): update installation instructions
test(orchestrator): add agent orchestration tests
refactor(quality): optimize quality assessment algorithms
```

### Branch Naming

- `feature/feature-name` - New features
- `bugfix/issue-description` - Bug fixes
- `hotfix/critical-issue` - Critical fixes
- `docs/documentation-update` - Documentation updates

## 📞 Getting Help

- **📧 Email**: [cavin.otieno012@gmail.com](mailto:cavin.otieno012@gmail.com)
- **💬 Discussions**: Use GitHub Discussions
- **🐛 Issues**: Report bugs via GitHub Issues
- **📱 WhatsApp**: [+254708101604](wa.me/+254708101604)

## 🙏 Thank You!

Thank you for contributing to the Jaseci Learning Companion! Your efforts help make this project better for everyone.

**Built with ❤️ by Cavin Otieno**
