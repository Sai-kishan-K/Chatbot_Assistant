Craft AI is a comprehensive MLOps and LLMOps platform designed to streamline the creation, deployment, and management of AI applications at scale, ensuring compliance with European regulations like GDPR and the AI Act. It supports both traditional Machine Learning model deployment and the creation of secure, enterprise-integrated AI agents powered by Large Language Models (LLMs).

---

## Craft AI Technical Guide

This guide outlines the core functionalities and operational procedures for using the Craft AI platform for MLOps and LLMOps workflows.

### 1. Platform Overview

Craft AI provides a fully managed environment for the entire lifecycle of AI applications, from development and experimentation to production monitoring. Key features include:
*   **End-to-end MLOps:** Manage data, models, and deployments.
*   **LLMOps Capabilities:** Train, fine-tune, and deploy custom or self-hosted LLMs, and create AI agents integrated with enterprise data.
*   **Infrastructure Automation:** Rapid setup of computing and storage resources without extensive DevOps expertise.
*   **Cloud Agnostic:** Deploy on various cloud providers including AWS, GCP, Scaleway, OVHCloud, S3NS, and Outscale.
*   **Scalability:** Easily scale AI applications and underlying infrastructure.
*   **Monitoring & Cost Management:** Full monitoring for optimal use, and tools to manage AI costs and carbon impact.
*   **Regulatory Compliance:** Adherence to European regulations.

### 2. Getting Started

#### 2.1. Prerequisites
*   **Python:** Version 3.9 or higher installed locally.
*   **Browser:** Google Chrome recommended for UI access.
*   **SDK:** Install the Python SDK: `pip install craft-ai-sdk python-dotenv`.

#### 2.2. Authentication
Access the platform via the Web UI or Python SDK.
*   **Simple Authentication:**
    1.  Receive an invitation email.
    2.  Click the link to create your account (fill out the form).
    3.  Confirm account via validation email.
*   **Multi-Factor Authentication (MFA):**
    1.  Receive an invitation email.
    2.  Click the link to create your password.
    3.  Configure an authenticator app (e.g., Google Authenticator, Auth0 Guardian) by scanning the provided QR code. Use the app for subsequent logins.
*   **SDK Initialization:**
    1.  Retrieve your `MY_ENVIRONMENT_URL` (from Environment page in UI) and `MY_ACCESS_TOKEN` (from User Parameters -> SDK Token in UI).
    2.  Initialize the SDK:
        ```python
        from craft_ai_sdk import CraftAiSdk
        sdk = CraftAiSdk(environment_url="MY_ENVIRONMENT_URL", sdk_token="MY_ACCESS_TOKEN")
        ```
    3.  **Best Practice:** Store credentials securely in a `.env` file and load them using `python-dotenv`.

#### 2.3. Project & Environment Creation (UI)
1.  **Create Project:** From the main UI page, click "New Project". Provide a name, select an organization (default), and Python version (default). Configure Git connection and project-level libraries (`requirements.txt`, APK/PAT packages) if needed.
2.  **Create Environment:** Within a project, click "New environment".
    *   **General:** Name (3-20 characters, no special chars), Tag (Experimentation, Testing, Production).
    *   **Computing Resources:** Select Cloud Provider (e.g., Scaleway), Machine type (CPU/GPU), Machine size, and number of Workers for parallelization.
    *   **Storage Resources:** Data Store provider (auto-filled). Optionally, select a Vector Database provider (currently Weaviate, runs on CPU).
    *   **Runtime Planner:** Define operational days, resume time (UTC), and standby time (UTC) to control resource usage and costs.
3.  **Monitor Creation:** Environment creation takes approximately 5 minutes. Refresh the page to check status.

### 3. Core Platform Components

#### 3.1. Projects
*   **Purpose:** Logical grouping of environments and users for organizational clarity.
*   **Configuration:** Define default Python versions, manage project-level dependencies (`requirements.txt`), and connect to Git repositories for centralized code management.

#### 3.2. Environments
*   **Purpose:** Isolated infrastructure for data storage and computation, tailored for different project phases (Experimentation, Testing, Production).
*   **Components:** Each environment includes a fully managed Kubernetes cluster (for pipeline execution) and a cloud-based Data Store.
*   **Management:**
    *   **Settings:** Access environment details (status, URL, IP), manage runtime planner, and configure environment-specific variables.
    *   **State Control:** Manually put environments into `operational` or `standby` mode.
    *   **Deletion:** Delete environments and all associated data.

#### 3.3. Data Store
*   **Purpose:** Cloud object storage for all input files, intermediate data, and pipeline outputs.
*   **Access:** Browse a tree-like file structure within each environment.
*   **Actions:** Upload, Download, Create Folder, Copy, Delete, Rename files/folders.
*   **Vector Database (Weaviate):** Integrate a Weaviate vector database during environment creation for advanced LLM features like Retrieval-Augmented Generation (RAG). Access using `sdk.get_weaviate_client()`.
*   **External Sources:** Connect to external databases or cloud storage buckets by defining connection parameters as environment variables (in Environment Settings or via SDK). Whitelist your environment URL in external sources for authorization.

#### 3.4. Pipelines
*   **Definition:** A Machine Learning workflow defined as a Python function with explicit inputs, processing logic, and outputs. Executed on Kubernetes pods.
*   **Objectives:** Orchestrate ML workflows, enable collaborative development, and facilitate deployment.
*   **Creation (SDK):**
    *   Define `Input` and `Output` objects specifying `name`, `data_type` (string, number, boolean, json, array, file), `description`, `is_required`, and `default_value`.
    *   Use `sdk.create_pipeline()` with `function_path`, `function_name`, `description`, `inputs_list`, `outputs_list`, and `container_config` (for local folder or Git repository).
    *   **Code Structure:** Typically `requirements.txt` and source code in a `src/` folder.
    *   **Limitations:** Embedded code size < 5MB; Inputs (non-file) < 0.06MB.
*   **Custom Docker Configuration:** For advanced users, define your pipeline's container environment using a custom `Dockerfile` (`WORKDIR /app` is mandatory). This feature is restricted to `Elastic` deployment mode. Pipeline code must adapt to receive inputs via `sys.argv` (serialized JSON) and write outputs to `/app` with an `output-` prefix.
*   **Management (UI):** View pipelines, access detailed information (source code, requirements, inputs/outputs, logs), and delete pipelines.

#### 3.5. Deployments
*   **Purpose:** Automate pipeline execution via repeatable and scheduled triggers.
*   **Execution Rules:**
    *   **Endpoint:** Trigger pipeline executions via API calls (provides a URL).
    *   **Periodic:** Schedule executions using CRON expressions.
*   **Execution Modes:**
    *   **Low Latency:** Pipeline is always active for faster responses.
    *   **Elastic:** Pipeline enters standby when idle to conserve resources.
*   **Execution Management (for Low Latency):**
    *   **Queue:** FIFO task management.
    *   **Parallel:** Define maximum parallel executions (uses threads or asynchronous I/O coroutines; `async def` recommended for thread safety).
    *   **RAM Request:** Allocate RAM to prevent resource exhaustion; plan based on total environment RAM.
*   **Input/Output Mapping:** Map pipeline inputs and outputs to external parameters (e.g., endpoint request body, constant values for scheduled tasks).

#### 3.6. Executions
*   **Purpose:** Track and analyze the results and logs of pipeline runs.
*   **Execution Tracking (UI):**
    *   View all pipeline and deployment executions (in progress, failed, succeeded).
    *   Access detailed information:
        *   **General:** ID, Status (Success, Failed, Error), Creator, Execution Rule, Environment, Computing Size, Duration.
        *   **Input/Output:** List of defined inputs and outputs with their values.
        *   **Metrics:** Simple metrics (table) and list metrics (graphs).
        *   **Logs:** Last 200 lines, refresh, download full logs.
*   **Execution Comparison (UI):**
    *   Compare multiple executions side-by-side by selecting meta-data, inputs, simple metrics, and list metrics.
    *   Filter and sort executions, and visualize list metrics on graphs.

#### 3.7. Monitoring
*   **Pipeline Monitoring:** Track single metrics over time for production deployments.
*   **Resource Monitoring:** Visualize infrastructure health (CPU, RAM usage) across all workers over time. Download data in CSV format. Access via `Monitoring > Resource metrics` or `sdk.get_resource_metrics()`.

### 4. Advanced Features

#### 4.1. Large Language Models (LLMs)
*   **Supported Models:** GPT-5.2, Mistral Large 3, Mistral Small, GPT-5 mini, Qwen3 235B, GPT-oss 120B.
*   **Self-Hosted LLM Deployment (Templates):**
    1.  Deploy state-of-the-art open-weight models on GPU environments using pre-configured templates.
    2.  Select quantization levels (16-bit, 8-bit, 4-bit) to optimize for VRAM and inference time.
    3.  **Deployment Process:** Via `Pipelines` tab -> `Deploy` -> `New from Template`. Use `Low-latency mode` and `Endpoint` execution rule, setting GPU request to `1` if needed.
    4.  **Configuration:** Customize `Messages` (OpenAI chat format), `Temperature`, and `System Prompt` through deployment inputs/outputs. Output is `Choices` (OpenAI chat format).
*   **AI Agents:** Create secure AI agents, easily integrated with enterprise data sources.
    *   **Pre-installed Assistants:** Document Search (RAG), Web Search, Document Summarization, Spell Check, Rephrasing, Editorial Assistance, Image Information Extraction (Pixtral).

#### 4.2. Retrieval-Augmented Generation (RAG)
*   **Functionality:** Enhance LLM responses with information from provided documents. Sources and extracts are displayed.
*   **Admin Configuration:** For RAG-enabled assistants, administrators upload context documents to the `/RAG` folder in the Data Store.
*   **Contextual RAG:** Agents can leverage conversation history and document context.

#### 4.3. User-Facing AI Assistant Features
*   **Conversation Interaction:** Select assistants, choose underlying LLM models, attach files (PDF, TXT, MD, DOCX, XLS, CSV) for context, give feedback, share conversations, edit/regenerate messages.
*   **Personal Assistants:** Users can create custom assistants by defining name, icon, objective, and detailed instructions (role, tone, response format, specific rules) and conversation starters.
*   **Prompt Shortcuts:** Users can define ` /keyword` shortcuts to insert pre-configured prompts in the chat.

### 5. Administration

Access the "Espace Administration" from the bottom-left of the UI (admin-only).
*   **Assistant Management:**
    *   Create "Advanced Assistants" linked to AI Studio deployments.
    *   Mark assistants as "Featured" (pinned) or "Visible" (in explorer).
    *   Configure the default assistant with specific instructions.
*   **User Management:**
    *   Invite users (individually or in batches via CSV - from changelog).
    *   Assign roles (administrator, basic user).
    *   Activate, deactivate, or delete user accounts.
    *   Reset user passwords (admin provides a temporary password to be changed immediately by the user).
*   **AI Studio Integration:**
    *   **RAG Documents:** Upload documents to `/RAG` in the Data Store to provide context for RAG assistants.
    *   **Web Agent Whitelisting:** For web-enabled agents, upload a `websearch-allowlist.txt` file (URLs separated by newlines) to `/craftgpt-config` in the Data Store to control accessible websites.

---
**Note:** Many operations and configurations can be performed via the Python SDK, offering programmatic control over the platform's features. Refer to the SDK documentation for detailed function specifications.