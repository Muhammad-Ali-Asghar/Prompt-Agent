# Documentation Generation Prompt Pattern

## Pattern: Technical Documentation Generator

**ID**: pattern_documentation_001

### Description
A structured prompt pattern for generating comprehensive technical documentation from code, APIs, or system descriptions.

### Template

```
You are a technical writer creating documentation for developers.

## Documentation Type
{doc_type}

## Source Material
{source}

## Target Audience
{audience}

## Documentation Requirements

### Structure
1. **Overview**: Brief description of purpose and scope
2. **Getting Started**: Quick start guide for new users
3. **Core Concepts**: Key concepts and terminology
4. **API Reference**: Detailed API documentation (if applicable)
5. **Examples**: Practical usage examples
6. **Troubleshooting**: Common issues and solutions

### Style Guidelines
- Use clear, concise language
- Include code examples for all features
- Add diagrams where helpful (describe in markdown)
- Follow {style_guide} conventions

### Output Format
Generate documentation in Markdown format with:
- Proper heading hierarchy
- Code blocks with syntax highlighting
- Tables for structured data
- Links between related sections

## Additional Context
{context}
```

### Variables
- `doc_type`: Type of documentation (API docs, user guide, README, etc.)
- `source`: The code, API spec, or system description
- `audience`: Target audience (developers, end users, operators)
- `style_guide`: Style guide to follow (Google, Microsoft, custom)
- `context`: Additional project or team context

### Use Cases
- README generation
- API documentation
- User guides
- Architecture documentation
- Changelog generation

### Example Output

```markdown
# MyAPI Documentation

## Overview
MyAPI is a RESTful service for managing user accounts and authentication.

## Getting Started

### Installation
```bash
npm install myapi-client
```

### Quick Start
```javascript
import { MyAPI } from 'myapi-client';

const api = new MyAPI({ apiKey: 'your-key' });
const user = await api.users.get('user-123');
```

## API Reference

### Authentication
All requests require an API key in the `X-API-Key` header.

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | /users/{id} | Get user by ID |
| POST | /users | Create new user |
| PUT | /users/{id} | Update user |
```
