# Natural Language Database Agent with LangGraph & Amazon Bedrock

This repository demonstrates how to build a natural language interface to query databases using LangGraph and Amazon Bedrock. The agent can generate SQL based on user questions, execute them against an AWS Athena database, and create Python visualizations from the results.

## Features

- Natural language to SQL conversion using LLMs from Amazon Bedrock
- SQL query execution against AWS Athena
- Python code generation for data visualization and analysis
- Streamlit-based user interface for interactive querying
- LangGraph-powered agent architecture

## Architecture

The application uses a LangGraph state machine to orchestrate the following workflow:
1. User asks a question in natural language
2. LLM generates SQL query based on the question
3. SQL is executed against AWS Athena database
4. Results are processed and returned to the user
5. If visualization is needed, Python code is generated and executed

## Prerequisites

- Python 3.8+
- AWS Account with access to Bedrock and Athena
- AWS CLI configured with appropriate permissions
- Athena database configured with tables for querying

## Installation

1. Clone the repository:
```
git clone https://github.com/yourusername/langgraph-Nova-NLDBA-blogpost.git
cd langgraph-Nova-NLDBA-blogpost
```

2. Install dependencies:
```
pip install -r requirements.txt
```

3. Configure AWS credentials:
```
aws configure
```

## Configuration

Update the configuration in `src/config.py` with your AWS settings:
- AWS region
- Athena database name
- S3 output location
- Bedrock model IDs

Download the spider data and add it to the `data/` folder and run `notebooks/database_setup.ipynb`.

## Usage

Run the Streamlit application:
```
streamlit run app.py
```
Note: This demo uses Streamlit for illustration purposes only. For production deployments, please review Streamlit's security configuration and deployment architecture to ensure it aligns with your organization's security requirements and best practices.

The application will launch in your browser, where you can:
- Select a user profile
- Choose an LLM model from Amazon Bedrock
- Ask questions in natural language about your data
- View the generated SQL and results
- See visualizations when requested

## Project Structure

- `app.py` - Main Streamlit application
- `src/config.py` - Configuration settings
- `src/prompts/` - LLM prompts for SQL and Python generation
- `src/tools/` - Agent tools for SQL and Python creation/execution
- `src/utils/` - Utility functions for AWS services
- `data/` - Sample data and schema information

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.