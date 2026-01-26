export interface EconolensClientOptions {
  baseUrl?: string;
  tokenProvider?: () => Promise<string | null>;
  fetchImpl?: typeof fetch;
  timeoutMs?: number;
}

export interface HistoricalDataRequest {
  fields?: string | string[];
}

export interface SimulationParams {
  rbp?: number | number[];
  rr?: number | number[];
  fpr?: number | number[];
  lock_target?: number | number[];
  forecast_length_days?: number;
  sector_duration_days?: number;
  requested_metric?: string;
}

export interface ProvidePlotRequest {
  series: string | PlotSeries | Array<string | PlotSeries>;
  start_date_key: string;
  title?: string;
  description?: string;
}

export interface PlotSeries {
  name: string;
  label?: string;
  unit?: string;
}

interface JsonRpcRequest {
  jsonrpc: '2.0';
  method: string;
  params?: Record<string, any>;
  id: number;
}

export class EconolensClient {
  private baseUrl: string;
  private tokenProvider?: () => Promise<string | null>;
  private fetchImpl: typeof fetch;
  private timeoutMs: number;
  private sessionId: string | null = null;
  private requestId = 0;

  constructor(options: EconolensClientOptions = {}) {
    this.baseUrl = (options.baseUrl || process.env.MCP_BASE_URL || 'https://mechafil-mcp-server.fly.dev/mcp').replace(/\/$/, '');
    this.tokenProvider = options.tokenProvider;
    this.fetchImpl = options.fetchImpl || (globalThis.fetch as typeof fetch);
    this.timeoutMs = options.timeoutMs || 45000;

    if (!this.fetchImpl) {
      throw new Error('No fetch implementation available. Provide fetchImpl or run in an environment with global fetch.');
    }
  }

  async fetchContext(): Promise<string> {
    const result = await this.callTool('fetch_context');
    if (typeof result !== 'string') {
      throw new Error('Unexpected response type for fetch_context');
    }
    return result;
  }

  async getHistoricalData(req: HistoricalDataRequest = {}): Promise<any> {
    return this.callTool('get_historical_data', req);
  }

  async simulate(params: SimulationParams = {}): Promise<any> {
    return this.callTool('simulate', params);
  }

  async providePlot(params: ProvidePlotRequest): Promise<any> {
    return this.callTool('provide_plot', params);
  }

  private async ensureSession(): Promise<void> {
    if (this.sessionId) return;

    this.requestId += 1;
    const initReq: JsonRpcRequest = {
      jsonrpc: '2.0',
      method: 'initialize',
      params: {
        protocolVersion: '2024-11-05',
        capabilities: {},
        clientInfo: { name: 'econolens-sdk-js', version: '0.1.0' }
      },
      id: this.requestId
    };

    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      Accept: 'application/json, text/event-stream'
    };
    const token = this.tokenProvider ? await this.tokenProvider() : null;
    if (token) headers['Authorization'] = `Bearer ${token}`;

    const res = await this.fetchWithTimeout(this.baseUrl, {
      method: 'POST',
      headers,
      body: JSON.stringify(initReq)
    });
    if (!res.ok) {
      throw new Error(`MCP initialization failed: ${res.status} ${res.statusText}`);
    }

    const sessionId = res.headers.get('mcp-session-id');
    if (!sessionId) {
      throw new Error('No mcp-session-id header in initialization response');
    }
    this.sessionId = sessionId;

    const text = await res.text();
    const lines = text.split('\n').map(l => l.trim()).filter(Boolean);
    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = JSON.parse(line.substring(6));
        if (data.error) {
          throw new Error(`MCP initialization error: ${data.error.message}`);
        }
      }
    }

    // send notifications/initialized
    this.requestId += 1;
    const notifReq: JsonRpcRequest = {
      jsonrpc: '2.0',
      method: 'notifications/initialized',
      params: {},
      id: this.requestId
    };
    await this.fetchWithTimeout(this.baseUrl, {
      method: 'POST',
      headers: {
        ...headers,
        'mcp-session-id': this.sessionId
      },
      body: JSON.stringify(notifReq)
    }, 5000);
  }

  private async callTool(toolName: string, args: Record<string, any> = {}): Promise<any> {
    await this.ensureSession();
    this.requestId += 1;
    const req: JsonRpcRequest = {
      jsonrpc: '2.0',
      method: 'tools/call',
      params: { name: toolName, arguments: args },
      id: this.requestId
    };

    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      Accept: 'application/json, text/event-stream',
      'mcp-session-id': this.sessionId || ''
    };
    const token = this.tokenProvider ? await this.tokenProvider() : null;
    if (token) headers['Authorization'] = `Bearer ${token}`;

    const res = await this.fetchWithTimeout(this.baseUrl, {
      method: 'POST',
      headers,
      body: JSON.stringify(req)
    }, this.timeoutMs);

    if (!res.ok) {
      const txt = await res.text().catch(() => '');
      throw new Error(`Tool call failed (${res.status} ${res.statusText}): ${txt || 'no body'}`);
    }

    const text = await res.text();
    const lines = text.split('\n').map(l => l.trim()).filter(Boolean);
    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = JSON.parse(line.substring(6));
        if (data.error) {
          throw new Error(`Tool error: ${data.error.message}`);
        }
        if (data.result?.content?.length) {
          const first = data.result.content[0];
          if (first && typeof first.text === 'string') {
            return first.text;
          }
        }
        if (data.result?.data) {
          return data.result.data;
        }
        if (data.result) {
          return data.result;
        }
      }
    }

    throw new Error('No result returned from MCP server');
  }

  private async fetchWithTimeout(url: string, options: any, timeoutMs: number = this.timeoutMs): Promise<Response> {
    const controller = new AbortController();
    const id = setTimeout(() => controller.abort(), timeoutMs);
    try {
      const res = await this.fetchImpl(url, { ...options, signal: controller.signal });
      clearTimeout(id);
      return res;
    } catch (err: any) {
      clearTimeout(id);
      if (err?.name === 'AbortError') {
        throw new Error(`Request timed out after ${timeoutMs}ms`);
      }
      throw err;
    }
  }
}
