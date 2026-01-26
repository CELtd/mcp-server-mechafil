import { describe, it, expect, beforeAll } from 'vitest';
import { EconolensClient } from '../src/index.js';

const baseUrl = process.env.MCP_BASE_URL || 'https://mechafil-mcp-server.fly.dev/mcp';
const shouldRun = true; // run by default against provided default URL unless overridden

describe.skipIf(!shouldRun)('EconolensClient contract (MCP)', () => {
  let client: EconolensClient;

  beforeAll(() => {
    client = new EconolensClient({ baseUrl });
  });

  it('fetches context', async () => {
    const ctx = await client.fetchContext();
    expect(typeof ctx).toBe('string');
    expect(ctx.length).toBeGreaterThan(100);
  }, 20000); // allow for cold-start / network latency

  it('gets historical data for a specific field', async () => {
    const hist = await client.getHistoricalData({ fields: ['raw_byte_power'] });
    expect(hist).toBeTruthy();
  });

  it('runs a simulation with a short horizon', async () => {
    const sim = await client.simulate({ forecast_length_days: 60, requested_metric: 'available_supply' });
    expect(sim).toBeTruthy();
  });

  it('provides a plot spec', async () => {
    const plot = await client.providePlot({
      series: 'historical_raw_power_eib',
      start_date_key: 'data_start_date',
      title: 'Network Power',
      description: 'Test plot'
    });
    expect(plot).toBeTruthy();
  });
});
