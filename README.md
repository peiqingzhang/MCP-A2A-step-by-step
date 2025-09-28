# Weather Agent Tutorial

This repository contains the code for a step-by-step tutorial on how to build and deploy a weather agent using LangChain, MCP, and Google Cloud Run. It is creataed for my medium story: https://medium.com/@peiqingz/building-ai-agents-from-tools-and-context-to-mcp-and-a2a-protocols-f3ccadb5f1da

## Project Structure

The repository is organized into the following parts:

- **`simple-weather-agents.ipynb`**: A Jupyter notebook that demonstrates the difference between a LangChain agent with and without tools.
- **`MCP server with Google Cloud Run`**: A directory containing the code for the MCP server that provides weather tools.
- **`A2A Server Weather Agent with Google Cloud Run`**: A directory containing the code for the A2A weather agent that consumes the tools from the MCP server.
- **`mcp-weather-client-agent.ipynb`**: A Jupyter notebook that shows how to create a client that interacts with the deployed A2A weather agent.
- **`weather-advisor-agent.ipynb`**: A Jupyter notebook that demonstrates how to build a more advanced agent that uses the weather agent to provide recommendations.
- **`tutorial structure illustration.png`**: An illustration of the project structure.

![Tutorial Structure](tutorial%20structure%20illustration.png)

## Getting Started

This tutorial is divided into three main parts:

1.  **Running the Simple Weather Agents Notebook**: This will give you a basic understanding of how agents and tools work.
2.  **Deploying the MCP Server**: This will deploy the server that provides the weather tools.
3.  **Deploying the A2A Weather Agent**: This will deploy the agent that consumes the tools from the MCP server.
4.  **Running the Client and Advisor Notebooks**: This will show you how to interact with your deployed agent.

### Part 1: Simple Weather Agents Notebook

1.  Open the `simple-weather-agents.ipynb` notebook in a Jupyter environment.
2.  Follow the instructions in the notebook to run the cells.

### Part 2: Deploying the MCP Server

1.  Navigate to the `MCP server with Google Cloud Run` directory.
2.  Open the `deploy.sh` script and replace the placeholder values for `OPENWEATHERMAP_API_KEY`, `PROJECT_ID`, and `REGION` with your own values.
3.  Run the script:
    ```bash
    bash deploy.sh
    ```
4.  The script will deploy the MCP server to Google Cloud Run and print the service URL.

### Part 3: Deploying the A2A Weather Agent

1.  Navigate to the `A2A Server Weather Agent with Google Cloud Run` directory.
2.  Open the `deploy.sh` script and replace the placeholder values for `PROJECT_ID`, `REGION`, `REPO_NAME`, and `SERVICE_NAME` with your own values.
3.  Open the `weather-agent.yaml` file and replace the placeholder values for `MCP_SERVER_URL`, `OPENAI_API_KEY`, and `HOST_OVERRIDE` with your own values.
4.  Run the script:
    ```bash
    bash deploy.sh
    ```
5.  The script will deploy the A2A weather agent to Google Cloud Run.

### Part 4: Running the Client and Advisor Notebooks

1.  **`mcp-weather-client-agent.ipynb`**: Open this notebook and replace the placeholder for the A2A server URL with the URL of your deployed A2A weather agent. Then, run the cells to interact with the agent.
2.  **`weather-advisor-agent.ipynb`**: Open this notebook and replace the placeholder for the A2A server URL with the URL of your deployed A2A weather agent. Then, run the cells to see how a more advanced agent can use your weather agent to provide recommendations.

## Conclusion

This tutorial provides a comprehensive, step-by-step guide to building and deploying a sophisticated agent-based application. By following the steps in this tutorial, you will gain a deep understanding of how to build your own agents and connect them to the outside world.
