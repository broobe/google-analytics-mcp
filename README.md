# Google Analytics MCP Server — HTTP dual-transport edition

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-ready-2496ed.svg)](https://docker.com)

HTTP-ready fork of [google-analytics-mcp](https://github.com/googleanalytics/google-analytics-mcp) with **dual SSE + Streamable HTTP transport**, OpenAI-compatible tool schemas, and API key authentication. Works out of the box with **ChatGPT Desktop** (SSE) and **Open Web UI** (Streamable HTTP).

This repo contains the source code for running a containerized
[MCP](https://modelcontextprotocol.io) server that interacts with APIs for
[Google Analytics](https://support.google.com/analytics).

## Tools 🛠️

The server uses the
[Google Analytics Admin API](https://developers.google.com/analytics/devguides/config/admin/v1)
and
[Google Analytics Data API](https://developers.google.com/analytics/reporting/data/v1)
to provide several
[Tools](https://modelcontextprotocol.io/docs/concepts/tools) for use with LLMs.

### Retrieve account and property information 🟠

- `get_account_summaries`: Retrieves information about the user's Google
  Analytics accounts and properties.
- `get_property_details`: Returns details about a property.
- `list_google_ads_links`: Returns a list of links to Google Ads accounts for
  a property.

### Run core reports 📙

- `run_report`: Runs a Google Analytics report using the Data API.
- `run_funnel_report`: Runs a Google Analytics funnel report using the Data API.
- `run_conversions_report`: Runs a Google Analytics conversions / attribution report.
- `get_custom_dimensions_and_metrics`: Retrieves the custom dimensions and
  metrics for a specific property.

### Run realtime reports ⏳

- `run_realtime_report`: Runs a Google Analytics realtime report using the
  Data API.

## Quick start (Docker) 🐳

### Prerequisites

- Docker and docker-compose
- A Google Cloud project with the [Analytics Admin API](https://console.cloud.google.com/apis/library/analyticsadmin.googleapis.com) and [Analytics Data API](https://console.cloud.google.com/apis/library/analyticsdata.googleapis.com) enabled
- OAuth 2.0 credentials (Desktop client) for a Google account with access to your GA4 properties
- An ADC (Application Default Credentials) JSON file with the `analytics.readonly` scope

### Setup

1. **Clone the repo**

   ```shell
   git clone https://github.com/broobe/google-analytics-mcp.git
   cd google-analytics-mcp
   ```

2. **Configure OAuth credentials**

   Generate your ADC file (you only need to do this once):

   ```shell
   gcloud auth application-default login \
     --scopes https://www.googleapis.com/auth/analytics.readonly,https://www.googleapis.com/auth/cloud-platform \
     --client-id-file=YOUR_CLIENT_JSON_FILE
   ```

   Copy the generated credentials file into the project:

   ```shell
   cp PATH_TO_CREDENTIALS_JSON credentials.json
   ```

3. **Configure environment**

   ```shell
   cp .env.example .env
   ```

   Edit `.env` and set:

   - `GOOGLE_CLOUD_PROJECT` — your Google Cloud project ID
   - `GOOGLE_APPLICATION_CREDENTIALS` — path to your ADC JSON file
   - `MCP_API_KEY` — a secure API key of your choice (used for bearer auth)

4. **Build and run**

   ```shell
   docker compose up -d ga4-mcp-http
   ```

   The server listens on port **8080** inside the container. Map it to any host port (default in docker-compose.yml: `8081:8080`).

### Client configuration

#### ChatGPT Desktop (SSE)

Configure your MCP client with:

- **URL**: `http://your-host:8081/`
- **Transport**: SSE (GET `/`)
- **Auth**: `Authorization: Bearer YOUR_MCP_API_KEY`

The server returns an SSE endpoint event, and the client POSTs JSON-RPC messages back.

#### Open Web UI (Streamable HTTP)

Configure your MCP connection with:

- **URL**: `http://your-host:8081/`
- **Transport**: Streamable HTTP (POST `/`)
- **Auth**: `Authorization: Bearer YOUR_MCP_API_KEY`

The client sends `initialize` → `notifications/initialized` → `tools/list` (server returns all 9 tools).

## API reference

### GET /

Returns SSE stream if `Accept: text/event-stream` header is present. Otherwise returns a simple status message.

### POST /

All JSON-RPC method calls. Requires `Authorization: Bearer <MCP_API_KEY>`.

If the query contains `session_id` (e.g., `/messages/?session_id=xxx`), the POST is routed to the SSE transport's message handler. Otherwise it goes to the Streamable HTTP transport.

### Streamable HTTP vs SSE

| Feature | Streamable HTTP | SSE |
|---------|----------------|-----|
| Transport | POST request/response | SSE stream (GET) + POST messages |
| Client example | Open Web UI, custom MCP clients | ChatGPT Desktop |
| Session lifecycle | Per-request | Long-lived connection |

## Advanced usage

For detailed report examples and a full dimension/metric reference, see [GA4-MCP-PROMPT.md](./GA4-MCP-PROMPT.md).

## Contributing ✨

Contributions welcome! See the [Contributing Guide](CONTRIBUTING.md).
