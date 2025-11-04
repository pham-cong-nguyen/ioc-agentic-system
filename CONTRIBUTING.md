# Contributing to IOC Agentic System

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## 🚀 Getting Started

1. **Fork the repository**
2. **Clone your fork**
   ```bash
   git clone https://github.com/your-username/akaAPIs.git
   cd akaAPIs
   ```
3. **Set up development environment**
   ```bash
   ./setup.sh
   ```
4. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

## 📋 Development Workflow

### 1. Code Style

We follow PEP 8 for Python code:

```bash
# Format code
make format

# Lint code
make lint
```

**Key conventions:**
- Use type hints
- Write docstrings for all functions
- Keep functions focused and small
- Use async/await for I/O operations

### 2. Testing

Write tests for new features:

```python
# tests/test_your_feature.py
import pytest

@pytest.mark.asyncio
async def test_your_feature():
    # Your test here
    pass
```

Run tests:
```bash
make test
make test-coverage
```

### 3. Documentation

- Update README.md for user-facing changes
- Update docstrings in code
- Add API documentation in OpenAPI
- Update PROJECT_SUMMARY.md for major changes

## 🏗️ Architecture Guidelines

### Backend Structure

```
backend/
├── module_name/
│   ├── models.py      # Database models
│   ├── schemas.py     # Pydantic schemas
│   ├── service.py     # Business logic
│   └── routes.py      # API endpoints
```

### Adding New Modules

1. Create module directory under `backend/`
2. Implement models, schemas, service, routes
3. Register routes in `backend/main.py`
4. Add tests in `tests/`
5. Update documentation

### LangGraph Nodes

To add a new orchestration node:

```python
# backend/orchestrator/graph.py
async def your_node(self, state: AgentState) -> Dict[str, Any]:
    """Your node description"""
    try:
        # Your logic here
        return {"updated_state": value}
    except Exception as e:
        logger.error(f"Error in your_node: {e}")
        return {"error": str(e)}
```

### Analysis Types

To add new analysis:

```python
# backend/analyzer/service.py
async def _analyze_your_type(
    self,
    data: List[Any],
    entities: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Your analysis logic"""
    # Implementation
    return result
```

## 🔧 Common Tasks

### Adding a New API Endpoint

1. **Define schema** in `schemas.py`:
```python
class YourRequest(BaseModel):
    field: str = Field(..., description="Field description")

class YourResponse(BaseModel):
    result: str
```

2. **Implement service** in `service.py`:
```python
async def your_function(self, data: YourRequest) -> YourResponse:
    # Logic here
    return YourResponse(result="value")
```

3. **Create route** in `routes.py`:
```python
@router.post("/your-endpoint", response_model=YourResponse)
async def your_endpoint(
    request: YourRequest,
    current_user: dict = Depends(get_current_user)
):
    """Endpoint description"""
    return await service.your_function(request)
```

### Adding LLM Provider

1. **Install package**:
```bash
pip install langchain-your-provider
```

2. **Update settings** in `config/settings.py`:
```python
YOUR_PROVIDER_API_KEY: Optional[str] = None
YOUR_PROVIDER_MODEL: str = "model-name"
```

3. **Add provider** in `backend/orchestrator/llm_service.py`:
```python
elif provider == "your_provider":
    from langchain_your_provider import ChatYourProvider
    return ChatYourProvider(
        model=settings.YOUR_PROVIDER_MODEL,
        api_key=settings.YOUR_PROVIDER_API_KEY
    )
```

## 📝 Pull Request Process

1. **Update your branch**:
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Run tests**:
   ```bash
   make test
   make lint
   ```

3. **Commit your changes**:
   ```bash
   git add .
   git commit -m "feat: add your feature"
   ```
   
   Use conventional commit format:
   - `feat:` New feature
   - `fix:` Bug fix
   - `docs:` Documentation
   - `test:` Tests
   - `refactor:` Code refactoring
   - `chore:` Maintenance

4. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

5. **Create Pull Request**:
   - Clear title and description
   - Link related issues
   - Include screenshots if UI changes
   - Request review

## 🐛 Bug Reports

When reporting bugs, include:

1. **Environment**:
   - OS and version
   - Python version
   - Docker version (if applicable)

2. **Steps to reproduce**:
   - Exact commands/queries
   - Input data
   - Expected vs actual behavior

3. **Logs**:
   - Error messages
   - Stack traces
   - Relevant log entries

## 💡 Feature Requests

For new features:

1. **Use case**: Describe the problem
2. **Proposed solution**: Your idea
3. **Alternatives**: Other approaches considered
4. **Additional context**: Examples, mockups

## 🔒 Security

- **DO NOT** commit sensitive data (API keys, passwords)
- Use `.env` file for secrets
- Report security issues privately
- Follow security best practices

## 📚 Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [LangChain Docs](https://python.langchain.com/)
- [LangGraph Guide](https://langchain-ai.github.io/langgraph/)
- [SQLAlchemy Docs](https://docs.sqlalchemy.org/)
- [Pydantic Documentation](https://docs.pydantic.dev/)

## 🎯 Areas for Contribution

### High Priority
- [ ] React/TypeScript frontend
- [ ] WebSocket streaming
- [ ] User management system
- [ ] Conversation persistence
- [ ] Rate limiting middleware
- [ ] Prometheus metrics

### Medium Priority
- [ ] More analysis types
- [ ] Visualization components
- [ ] Additional LLM providers
- [ ] Advanced caching strategies
- [ ] Performance optimizations

### Low Priority
- [ ] Mobile app
- [ ] Voice interface
- [ ] Report generation
- [ ] Data export features
- [ ] Multi-language support

## 📧 Contact

- **GitHub Issues**: For bugs and features
- **Discussions**: For questions and ideas
- **Email**: support@example.com

## 📜 License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing! 🙏
